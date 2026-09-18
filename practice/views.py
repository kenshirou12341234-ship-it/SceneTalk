from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from scenes.models import Scene, Phrase
from django.shortcuts import render, get_object_or_404, redirect


def prev_view(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id)
    phrase_key = f'current_phrase_id_{scene_id}'
    feedback_key = f'feedback_{scene_id}'

    if phrase_key in request.session:
        current_phrase = get_object_or_404(Phrase, id=request.session[phrase_key])
        prev_phrase = scene.phrases.filter(
            display_order__lt=current_phrase.display_order
        ).order_by('-display_order').first()

        if prev_phrase:
            request.session[phrase_key] = prev_phrase.id
            request.session[feedback_key] = None
            request.session.modified = True

    return redirect('practice:practice', scene_id=scene_id)

def restart_view(request, scene_id):
    phrase_key = f'current_phrase_id_{scene_id}'
    feedback_key = f'feedback_{scene_id}'

    if phrase_key in request.session:
        del request.session[phrase_key]
    if feedback_key in request.session:
        del request.session[feedback_key]

    return redirect('practice:practice', scene_id=scene_id)

def practice_view(request, scene_id):
    scene = get_object_or_404(Scene, id=scene_id)

    phrase_key = f'current_phrase_id_{scene_id}'
    feedback_key = f'feedback_{scene_id}'

    # 初回アクセス時の初期化
    if phrase_key not in request.session:
        first_phrase = scene.phrases.order_by('display_order').first()

        if first_phrase is None:
            context = {
                'error_message': 'このシーンにはまだフレーズが登録されていません。',
            }
            return render(request, 'practice/practice.html', context)

        request.session[phrase_key] = first_phrase.id
        request.session[feedback_key] = None

    # GETリクエスト時(通常の画面表示)の処理
    current_phrase = get_object_or_404(Phrase, id=request.session[phrase_key])
    feedback = request.session.get(feedback_key)

    context = {
        'scene': scene,
        'current_phrase': current_phrase,
        'feedback': feedback,
    }
    return render(request, 'practice/practice.html', context)


def practice_answer_view(request, scene_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POSTメソッドのみ対応しています'}, status=405)

    phrase_key = f'current_phrase_id_{scene_id}'
    feedback_key = f'feedback_{scene_id}'

    current_phrase = get_object_or_404(Phrase, id=request.session.get(phrase_key))
    user_answer = request.POST.get('answer', '').strip()

    is_correct = (user_answer.lower() == current_phrase.staff_en.strip().lower())

    if is_correct:
        next_phrase = Phrase.objects.filter(
            scene_id=scene_id,
            display_order__gt=current_phrase.display_order
        ).order_by('display_order').first()

        if next_phrase:
            request.session[phrase_key] = next_phrase.id
            request.session[feedback_key] = None
            return JsonResponse({
                'is_correct': True,
                'is_finished': False,
                'finished': False,
                'user_answer': user_answer,
                'next_phrase': {
                    'id': next_phrase.id,
                    'npc_en': next_phrase.npc_en,
                    'staff_jp': next_phrase.staff_jp,
                    'turn_order': next_phrase.turn_order,
                },
            })
        else:
            request.session[feedback_key] = None
            return JsonResponse({
                'is_correct': True,
                'is_finished': True,
                'finished': True,
                'user_answer': user_answer,
            })
    else:
        request.session[feedback_key] = '不正解です。もう一度試してみましょう。'
        return JsonResponse({
            'is_correct': False,
            'is_finished': False,
            'finished': False,
            'feedback': '不正解です。もう一度試してみましょう。',
            'user_answer': user_answer,
        })