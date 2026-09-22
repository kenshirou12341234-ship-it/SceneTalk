import random
import time


def generate_content_with_retry(
    client, model, prompt, config, max_retries=5, initial_delay=1.0, backoff_factor=2.0
):
    """
    指数バックオフ（ジッター付き）を用いてGemini API呼び出しをリトライする関数
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            # Gemini API の呼び出し
            response = client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response  # 成功したら即座にレスポンスを返す

        except Exception as e:
            # 最後の試行だった場合はエラーを上に投げる
            if attempt == max_retries - 1:
                print(f"最大リトライ回数({max_retries})に達しました。")
                raise

            # APIのレートリミット（429）やサーバーエラー（5xx）などを想定
            print(f"[試行 {attempt + 1}/{max_retries}] エラー発生: {e}")

            # 【重要】ジッター（Jitter）の追加
            # 単純な倍々ではなく、ランダムな揺らぎを加えることでサーバーへの同時集中を防ぎます
            jittered_delay = delay * random.uniform(0.5, 1.5)

            print(f"{jittered_delay:.2f} 秒後に再試行します...")
            time.sleep(jittered_delay)

            # 次回のリトライに向けて待ち時間を指数関数的に増加（例: 1s -> 2s -> 4s -> 8s）
            delay *= backoff_factor
