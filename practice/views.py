import json
import logging
import random
import re
import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from scenes.models import ConversationHistory, Phrase, Scene

logger = logging.getLogger(__name__)


# --- Geminiから確実に受け取りたいJSONフォーマットを定義 ---
class AssessmentResult(BaseModel):
    is_correct: bool = Field(
        description="ユーザーの解答が指定された日本語の指示（staff_jp）やシチュエーションに対して、意味が通じていれば true。完全に的外れ、または意味が通じない場合は false"
    )
    feedback_comment: str = Field(
        description="判定の理由、文法のフィードバック、またはユーザーの解答に対する日本語のアドバイスコメント"
    )
    native_suggestions: list[str] = Field(
        description="ユーザーの解答をより自然に、またはネイティブらしくした英語の言い換え表現候補（2〜3個）"
    )


# --- 指数バックオフ（ジッター付き）を用いてGemini APIを安全に呼び出す関数 ---
def generate_content_with_retry(
    client, model, prompt, config, max_retries=3, initial_delay=1.0, backoff_factor=2.0
):
    """
    APIの一時的なエラーやレートリミットを回避するためのリトライロジック
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response  # 成功時は即座に返却
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(
                    f"Gemini API 最大リトライ回数({max_retries})に達したため終了します。"
                )
                raise

            # ジッター（揺らぎ）を加えることでリトライ負荷の集中を回避
            jittered_delay = delay * random.uniform(0.5, 1.5)
            logger.warning(
                f"[試行 {attempt + 1}/{max_retries}] Geminiエラー: {e}。 {jittered_delay:.2f}秒後に再試行します..."
            )

            time.sleep(jittered_delay)
            delay *= backoff_factor


def next_view(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id)
    phrase_key = f"current_phrase_id_{scene_id}"
    feedback_key = f"feedback_{scene_id}"

    if phrase_key in request.session:
        current_phrase = get_object_or_404(Phrase, id=request.session[phrase_key])
        next_phrase = (
            scene.phrases.filter(display_order__gt=current_phrase.display_order)
            .order_by("display_order")
            .first()
        )  # 昇順に変更

        if next_phrase:
            request.session[phrase_key] = next_phrase.id
            request.session[feedback_key] = None
            request.session.modified = True

    return redirect("practice:practice", scene_id=scene_id)


def prev_view(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id)
    phrase_key = f"current_phrase_id_{scene_id}"
    feedback_key = f"feedback_{scene_id}"

    if phrase_key in request.session:
        current_phrase = get_object_or_404(Phrase, id=request.session[phrase_key])
        prev_phrase = (
            scene.phrases.filter(display_order__lt=current_phrase.display_order)
            .order_by("-display_order")
            .first()
        )

        if prev_phrase:
            request.session[phrase_key] = prev_phrase.id
            request.session[feedback_key] = None
            request.session.modified = True

    return redirect("practice:practice", scene_id=scene_id)


def restart_view(request, scene_id):
    phrase_key = f"current_phrase_id_{scene_id}"
    feedback_key = f"feedback_{scene_id}"

    if phrase_key in request.session:
        del request.session[phrase_key]
    if feedback_key in request.session:
        del request.session[feedback_key]

    return redirect("practice:practice", scene_id=scene_id)


def practice_view(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id)
    phrase_key = f"current_phrase_id_{scene_id}"
    feedback_key = f"feedback_{scene_id}"

    # 初回アクセス時の初期化
    if phrase_key not in request.session:
        first_phrase = scene.phrases.order_by("display_order").first()

        if first_phrase is None:
            context = {
                "error_message": "このシーンにはまだフレーズが登録されていません。",
            }
            return render(request, "practice/practice.html", context)

        request.session[phrase_key] = first_phrase.id
        request.session[feedback_key] = None

    # GETリクエスト時(通常の画面表示)の処理
    current_phrase = get_object_or_404(
        Phrase.objects.select_related("scene"), id=request.session[phrase_key]
    )

    feedback = request.session.get(feedback_key)

    context = {
        "scene": scene,
        "current_phrase": current_phrase,
        "feedback": feedback,
    }
    return render(request, "practice/practice.html", context)


def normalize_answer(text):
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


# --- Gemini APIと指数バックオフを組み込んだ解答判定ビュー ---
def practice_answer_view(request, scene_id):
    if request.method != "POST":
        return JsonResponse({"error": "POSTメソッドのみ対応しています"}, status=405)

    # 会話履歴をユーザーに紐づけるためログイン状態をチェック
    if not request.user.is_authenticated:
        return JsonResponse({"error": "履歴保存にはログインが必要です"}, status=401)

    phrase_key = f"current_phrase_id_{scene_id}"
    feedback_key = f"feedback_{scene_id}"

    current_phrase = get_object_or_404(
        Phrase.objects.select_related("scene"), id=request.session.get(phrase_key)
    )
    user_answer = request.POST.get("answer", "").strip()

    # 1. 初期変数のセット
    is_correct = False
    feedback_comment = ""
    native_suggestions = []
    skipped = False

    # 2. npc_first の場合はスタッフの解答が不要なターンなので判定をスキップ
    if current_phrase.turn_order == "npc_first":
        is_correct = True
        skipped = True
    else:
        # 3. ユーザー入力がある場合に Gemini API で高度な判定を行う
        if user_answer:
            # 最新の Google GenAI SDK クライアント初期化
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            try:
                models = list(client.models.list())
                logger.info("利用可能なモデル一覧:")
                for m in models:
                    logger.info(m.name)
            except Exception as e:
                logger.error(f"モデル一覧の取得に失敗: {e}")


            # AIへ渡すプロンプトの構成
            prompt = f"""
            あなたは親切で的確な英会話の先生です。
            以下のシチュエーションにおいて、ユーザーが発言した英語が適切かどうかを判定してください。

            【NPCからの直前の英語発話】
            {current_phrase.npc_en}

            【ユーザーが表現したかった日本語の意図（目標）】
            {current_phrase.staff_jp}

            【手本となる英文（一例）】
            {current_phrase.staff_en}

            【ユーザーが実際に入力した英語の解答】
            {user_answer}

            ＜判定基準＞
            手本の英文（staff_en）と一言一句一致していなくても、意味が通じ、シチュエーションや日本語の意図に対して適切であれば `is_correct: true` と判定してください。
            文法的に多少のミス（三単現のsの抜けや冠詞のミスなど）があっても、コミュニケーションが成立していれば許容し、アドバイスで優しく指摘してください。
            """

            try:
                # 構造化出力（Structured Outputs）の設定
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AssessmentResult,
                    temperature=0.2,  # 判定のブレをなくすため低めに設定
                )

                # 指数バックオフ関数を経由して安全に通信を実行
                response = generate_content_with_retry(
                    client=client,
                    model="gemini-3.6-flash",
                    prompt=prompt,
                    config=config,
                    max_retries=3,  # 最大3回リトライ
                    initial_delay=1.0,  # 初回遅延1秒
                )

                # JSON文字列をシリアライズ
                ai_result = json.loads(response.text)

                is_correct = ai_result["is_correct"]
                feedback_comment = ai_result["feedback_comment"]
                native_suggestions = ai_result["native_suggestions"]

            except Exception as e:
                # すべてのリトライが失敗した場合のセーフティネット（既存の完全一致方式にフォールバック）
                is_correct = normalize_answer(user_answer) == normalize_answer(
                    current_phrase.staff_en
                )
                feedback_comment = (
                    "AI判定中にエラーが発生したため、システム自動判定を行いました。"
                )
                logger.error(
                    f"AI判定中に最終エラーが発生しました（自動採点へ移行）: {e}",
                    exc_info=True,
                )
                native_suggestions = [current_phrase.staff_en]
        else:
            # 空欄で送信された場合
            is_correct = False
            feedback_comment = (
                "解答が入力されていません。発話するか文字を入力してください。"
            )

    # --- 【新機能】会話履歴をデータベースへ永続化 ---
    if not skipped and user_answer:
        try:
            ConversationHistory.objects.create(
                user=request.user,
                scene=current_phrase.scene,
                user_answer=user_answer,
                is_correct=is_correct,
                feedback_comment=feedback_comment,
                native_suggestions=native_suggestions,
            )
        except Exception as save_error:
            logger.error(f"会話履歴のDB保存に失敗しました: {save_error}", exc_info=True)

    # 4. 判定結果に基づき、セッション更新およびレスポンス返却
    if is_correct:
        next_phrase = (
            Phrase.objects.filter(
                scene_id=scene_id, display_order__gt=current_phrase.display_order
            )
            .order_by("display_order")
            .first()
        )

        if next_phrase:
            request.session[phrase_key] = next_phrase.id
            request.session[feedback_key] = None
            return JsonResponse(
                {
                    "is_correct": True,
                    "is_finished": False,
                    "finished": False,
                    "user_answer": user_answer,
                    "skipped": skipped,
                    "feedback_comment": feedback_comment,
                    "native_suggestions": native_suggestions,
                    "next_phrase": {
                        "id": next_phrase.id,
                        "npc_en": next_phrase.npc_en,
                        "staff_jp": next_phrase.staff_jp,
                        "turn_order": next_phrase.turn_order,
                    },
                }
            )
        else:
            request.session[feedback_key] = None
            return JsonResponse(
                {
                    "is_correct": True,
                    "is_finished": True,
                    "finished": True,
                    "user_answer": user_answer,
                    "skipped": skipped,
                    "feedback_comment": feedback_comment,
                    "native_suggestions": native_suggestions,
                }
            )
    else:
        # 不正解時のフィードバックテキストをセッションに格納
        request.session[feedback_key] = feedback_comment
        return JsonResponse(
            {
                "is_correct": False,
                "is_finished": False,
                "finished": False,
                "user_answer": user_answer,
                "skipped": skipped,
                "feedback": feedback_comment,
                # 既存互換用
                "feedback_comment": feedback_comment,
                # Gemini用
                "native_suggestions": native_suggestions,
            }
        )
