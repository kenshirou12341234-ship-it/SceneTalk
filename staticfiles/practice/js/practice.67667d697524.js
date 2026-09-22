// CSRFトークン取得(Django公式のサンプルコード)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const form = document.getElementById('answer-form');
const sceneId = form.dataset.sceneId;

form.addEventListener('submit', async function (e) {
  e.preventDefault();

  const answerInput = document.getElementById('answer-input');
  const answer = answerInput.value;

  const response = await fetch(`/practice/${sceneId}/answer/`, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({ answer: answer }),
  });

  const data = await response.json();

  renderFeedback(data);
  answerInput.value = '';
});

function renderFeedback(data) {
  console.log('受け取ったdata:', data);
  console.log('turn_order の値:', data.next_phrase?.turn_order);
  const feedbackArea = document.getElementById('feedback-area');
  const form = document.getElementById('answer-form');

  if (data.is_correct) {
    feedbackArea.textContent = data.skipped
      ? ''
      : `正解! あなたの解答: ${data.user_answer}`;

    if (data.finished) {
      showFinishMessage();
      return;
    }

    if (data.next_phrase) {
      updateQuestion(data.next_phrase);

      if (data.next_phrase.turn_order === 'npc_first') {
        // 解答不要なので、フォームを隠して自動的に次へ進める
        form.style.display = 'none';
        setTimeout(() => {
          advancePhrase();
        }, 1500);
      } else {
        form.style.display = '';
      }
    }
  } else {
    feedbackArea.textContent = `もう一度お願いします: ${data.user_answer}`;
  }
}

function updateQuestion(nextPhrase) {
  const npcTextEl = document.getElementById('npc-text');
  const staffJpEl = document.getElementById('staff-jp-text');

  npcTextEl.textContent = nextPhrase.npc_en;

  if (nextPhrase.turn_order === 'staff_first') {
    staffJpEl.textContent = nextPhrase.staff_jp;
    staffJpEl.style.display = '';
  } else {
    // npc_first のときは日本語の問題文は不要なので隠す
    staffJpEl.style.display = 'none';
  }
}

// npc_first を自動で通過させ、次のフレーズ情報を取得するための関数
async function advancePhrase() {
  const response = await fetch(`/practice/${sceneId}/answer/`, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    // npc_first のときは answer は採点に使われないので空でOK
    body: new URLSearchParams({ answer: '' }),
  });

  const data = await response.json();
  renderFeedback(data);
}

function showFinishMessage() {
  const feedbackArea = document.getElementById('feedback-area');
  feedbackArea.textContent = '🎉 このシーンは終了です!お疲れ様でした!';

  const form = document.getElementById('answer-form');
  form.style.display = 'none';
}