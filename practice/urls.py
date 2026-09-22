from django.urls import path

from . import views

app_name = "practice"

urlpatterns = [
    path("<int:scene_id>/", views.practice_view, name="practice"),
    path(
        "<int:scene_id>/answer/", views.practice_answer_view, name="practice_answer"
    ),  # practice/ を削除
    path("<int:scene_id>/restart/", views.restart_view, name="restart"),
    path("<int:scene_id>/prev/", views.prev_view, name="prev"),
    path("<int:scene_id>/next/", views.next_view, name="next"),
]
