from django.contrib import admin
from .models import Scene, Phrase


class PhraseInline(admin.TabularInline):
    model = Phrase
    extra = 1


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "background_image", "display_order", "created_at", "updated_at")

    ordering = ("display_order",)
    inlines = [PhraseInline]  # ← Scene編集画面でPhraseもまとめて入力できるようにする


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ("id", "scene", "turn_order", "staff_jp", "staff_en", "npc_en", "display_order")
    ordering = ("scene", "display_order")
    list_filter = ("scene",)