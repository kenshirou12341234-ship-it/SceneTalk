import pytest

from scenes.tests.factories import ConversationHistoryFactory


@pytest.mark.django_db
class TestConversationHistory:
    """ConversationHistoryモデルのテスト"""

    def test_create_conversation_history(self):
        """会話履歴が正しく作成できること"""
        history = ConversationHistoryFactory()
        assert history.id is not None
        # 【修正】新フィールド名で検証
        assert history.user_answer == "テスト入力"
        assert history.feedback_comment == "テストフィードバック"

    def test_str_representation(self):
        """__str__メソッドが正しく動作すること"""
        history = ConversationHistoryFactory()
        # 【修正】モデルの __str__ 実装に合わせて expected を作成
        expected = f"{history.user.email} - {history.scene.name} ({history.created_at.strftime('%Y-%m-%d %H:%M')})"
        assert str(history) == expected

    def test_ordering(self):
        """会話履歴が created_at の降順で並ぶこと"""
        ConversationHistoryFactory()
        ConversationHistoryFactory()

        from scenes.models import ConversationHistory

        histories = list(ConversationHistory.objects.all())

        # 【修正】新しく作られた（IDが大きい / created_at が新しい）ものが先に来る
        assert histories[0].created_at >= histories[1].created_at
