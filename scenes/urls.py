from django.urls import path
from . import views

app_name = "scenes"

urlpatterns = [
    path("", views.scene_list, name="scene_list"),
    path("<int:pk>/", views.phrase_list, name="phrase_list"),
]