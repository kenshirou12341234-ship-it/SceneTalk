from django.conf import settings  # 1. settingsをインポート
from django.db import models

# from django.contrib.auth.models import User  # ← このインポートは不要になるので削除してOKです


class Scene(models.Model):
    name = models.CharField(max_length=100, verbose_name="シーン名")
    description = models.TextField(blank=True, verbose_name="説明")
    background_image = models.CharField(
        max_length=255,
        default="images/backgrounds/default.png",
        verbose_name="背景画像パス",
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.name


class Phrase(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name="phrases")
    display_order = models.IntegerField()

    turn_order = models.CharField(
        max_length=20, default="staff_first"
    )  # staff_first / npc_first
    npc_en = models.CharField(max_length=255, blank=True, null=True)
    staff_jp = models.CharField(max_length=255, blank=True, null=True)
    staff_en = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["scene", "display_order"],
                name="unique_scene_display_order",
            ),
        ]

    def __str__(self):
        return self.staff_jp or self.npc_en or ""


# --- 【修正】会話履歴を記録するモデル ---
class ConversationHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # 2. ここを「settings.AUTH_USER_MODEL」に書き換えます
        on_delete=models.CASCADE,
        related_name="conversation_histories",
        verbose_name="ユーザー",
    )
    scene = models.ForeignKey(
        Scene,
        on_delete=models.CASCADE,
        related_name="conversation_histories",
        verbose_name="シーン",
    )
    user_answer = models.TextField(blank=True, verbose_name="ユーザーの入力テキスト")
    is_correct = models.BooleanField(default=False, verbose_name="正誤判定")
    feedback_comment = models.TextField(blank=True, verbose_name="AIフィードバック")
    native_suggestions = models.JSONField(
        default=list, blank=True, verbose_name="ネイティブ言い換え候補"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="練習日時")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "会話履歴"
        verbose_name_plural = "会話履歴一覧"

    def __str__(self):
        # どのカスタムユーザーモデルでも基本実装されている「get_username()」か「username」を参照します

        return f"{self.user} - {self.scene.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
