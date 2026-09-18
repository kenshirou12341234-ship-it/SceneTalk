from django.shortcuts import render, get_object_or_404
from .models import Scene

def scene_list(request):
    scenes = Scene.objects.all()
    return render(request, "scenes/scene_list.html", {"scenes": scenes})

def phrase_list(request, pk):
    scene = get_object_or_404(Scene, pk=pk)
    phrases = scene.phrases.all()
    return render(request, "scenes/phrase_list.html", {"scene": scene, "phrases": phrases})