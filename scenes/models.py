from django.db import models

class Scene(models.Model):
    name = models.CharField(max_length=100, verbose_name="シーン名")
    description = models.TextField(blank=True, verbose_name="説明")
    background_image = models.CharField(
        max_length=255,
        default="images/backgrounds/default.png",
        verbose_name="背景画像パス"
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.name


class Phrase(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='phrases')
    display_order = models.IntegerField()

    turn_order = models.CharField(max_length=20, default="staff_first")  # staff_first / npc_first
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