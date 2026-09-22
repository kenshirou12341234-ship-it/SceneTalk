from django.db import models
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from .models import Phrase, Scene


def scene_list(request):
    scenes = Scene.objects.all().annotate(phrases_count=Count("phrases"))
    return render(request, "scenes/scene_list.html", {"scenes": scenes})


def phrase_list(request, pk):
    scene = get_object_or_404(
        Scene.objects.prefetch_related(
            models.Prefetch(
                "phrases", queryset=Phrase.objects.order_by("display_order")
            )
        ),
        pk=pk,
    )
    phrases = scene.phrases.all()
    return render(
        request, "scenes/phrase_list.html", {"scene": scene, "phrases": phrases}
    )
