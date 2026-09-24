import factory
from django.contrib.auth import get_user_model

from scenes.models import ConversationHistory, Scene

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """ユーザーのテストデータを生成"""

    class Meta:
        model = User

    # 【修正】CustomUserに存在しない username を削除し、email だけを生成する
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")


class SceneFactory(factory.django.DjangoModelFactory):
    """シーンのテストデータを生成"""

    class Meta:
        model = Scene

    name = factory.Sequence(lambda n: f"Scene {n}")
    description = "テスト用のシーン説明"
    background_image = "images/backgrounds/cafe.png"

class ConversationHistoryFactory(factory.django.DjangoModelFactory):
    """会話履歴のテストデータを生成"""

    class Meta:
        model = ConversationHistory

    user = factory.SubFactory(UserFactory)
    scene = factory.SubFactory(SceneFactory)
    # 【修正】統合後の最新フィールド名に書き換え
    user_answer = "テスト入力"
    is_correct = True
    feedback_comment = "テストフィードバック"
    native_suggestions = ["Suggestion 1", "Suggestion 2"]
