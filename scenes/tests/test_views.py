import json
from unittest.mock import patch

import pytest
from django.urls import reverse

from scenes.models import ConversationHistory, Phrase
from scenes.tests.factories import SceneFactory, UserFactory


@pytest.mark.django_db
class TestCoreAppFeatures:
    """アプリのコア機能（認証・画面表示・API応答）の統合ビューテスト"""

    @pytest.fixture(autouse=True)
    def setup_method(self, client):
        self.client = client
        self.user = UserFactory()
        self.scene = SceneFactory()

        # テスト用のフレーズ（解答送信ターン）を作成
        self.phrase = Phrase.objects.create(
            scene=self.scene,
            display_order=1,
            turn_order="staff_first",
            npc_en="Hello!",
            staff_jp="こんにちは",
            staff_en="Hello",
        )

    def test_top_page_and_login_flow(self):
        """トップページの表示と、ログイン状態によるコンテンツ切り替えのテスト"""
        top_url = reverse("top:index")

        response = self.client.get(top_url)
        assert response.status_code == 200
        assert "ログインはこちら" in response.content.decode("utf-8")
        assert "シーン一覧" not in response.content.decode("utf-8")

        self.client.force_login(self.user)

        response = self.client.get(top_url)
        assert response.status_code == 200
        assert "シーン一覧" in response.content.decode("utf-8")

    def test_phrase_list_view_with_optimization(self):
        """フレーズ一覧画面がログインユーザーに対して正常に表示されるかのテスト"""
        self.client.force_login(self.user)

        url = reverse("scenes:phrase_list", kwargs={"pk": self.scene.id})
        response = self.client.get(url)

        assert response.status_code == 200
        assert self.scene.name in response.content.decode("utf-8")
        assert "[店員(あなた)]" in response.content.decode("utf-8")
        assert "こんにちは" in response.content.decode("utf-8")

    # 【修正】パッチの対象パスを 'scenes.views' から 'practice.views' に変更
    @patch("practice.views.generate_content_with_retry")
    def test_practice_answer_api_success_and_history_saved(self, mock_gemini):
        """ユーザーの発話解答がGemini API（モック）を通過し、正しく会話履歴がDBに自動保存されるかのテスト"""
        self.client.force_login(self.user)

        session = self.client.session
        session[f"current_phrase_id_{self.scene.id}"] = self.phrase.id
        session.save()

        class DummyResponse:
            text = json.dumps(
                {
                    "is_correct": True,
                    "feedback_comment": "Excellent! Very natural English.",
                    "native_suggestions": ["Hi there!", "Good day!"],
                }
            )

        mock_gemini.return_value = DummyResponse()

        url = reverse("practice:practice_answer", kwargs={"scene_id": self.scene.id})

        response = self.client.post(
            url, {"answer": "Hello"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["feedback_comment"] == "Excellent! Very natural English."

        assert (
            ConversationHistory.objects.filter(user=self.user, scene=self.scene).count()
            == 1
        )

        saved_history = ConversationHistory.objects.first()
        assert saved_history.user_answer == "Hello"
        assert saved_history.is_correct is True
        assert "Excellent!" in saved_history.feedback_comment
