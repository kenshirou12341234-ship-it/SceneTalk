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

// --- 音声認識の初期設定 ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

const startRecBtn = document.getElementById('start-rec-btn');
const stopRecBtn = document.getElementById('stop-rec-btn');
const clearRecBtn = document.getElementById('clear-rec-btn'); // 【追加】やり直すボタン
const recStatus = document.getElementById('rec-status');
const recError = document.getElementById('rec-error');
const answerInput = document.getElementById('answer-input');
const inputContainer = document.getElementById('input-container'); // フォームを包むコンテナ

if (SpeechRecognition && startRecBtn) {
  recognition = new SpeechRecognition();
  recognition.lang = 'en-US';        // 英会話想定のため英語に設定
  recognition.interimResults = true; // リアルタイムの途中経過を表示
  recognition.continuous = true;     // 連続認識を有効化

  // 録音開始
  startRecBtn.addEventListener('click', () => {
    recError.textContent = '';
    answerInput.value = '';
    try {
      recognition.start();
    } catch (e) {
      console.error(e);
    }
  });

  // 録音停止
  stopRecBtn.addEventListener('click', () => {
    if (recognition) recognition.stop();
  });

  // 【追加】音声入力をクリアしてやり直す
  if (clearRecBtn) {
    clearRecBtn.addEventListener('click', () => {
      forceStopRecognition();    // 認識中のデータを即座に破棄して強制終了
      
      // 音声認識の停止完了ラグによる文字の再乱入を防ぐため、僅かに遅らせてクリア
      setTimeout(() => {
        answerInput.value = '';     // 入力テキストを完全にクリア
        recError.textContent = ''; // エラー表示をクリア
      }, 50);
    });
  }

  // 認識開始時の処理
  recognition.onstart = () => {
    recStatus.textContent = "状態: 🔴 録音中...";
    recStatus.classList.add('text-red-600');
    startRecBtn.disabled = true;
    startRecBtn.classList.add('opacity-50');
    stopRecBtn.disabled = false;
  };

  // 認識終了時の処理
  recognition.onend = () => {
    // AI判定中の時は文言を上書きしたくないため、「判定中」でない場合のみ「停止中」に戻す
    if (!recStatus.textContent.includes('🤖')) {
      recStatus.textContent = "状態: 停止中";
      recStatus.classList.remove('text-red-600');
      startRecBtn.disabled = false;
      startRecBtn.classList.remove('opacity-50');
      stopRecBtn.disabled = true;
    }
  };

  // リアルタイムテキスト反映
  recognition.onresult = (event) => {
    let finalTranscript = '';
    let interimTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i] && event.results[i][0]) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
    }
    answerInput.value = finalTranscript + interimTranscript;
  };

  // エラーハンドリング
  recognition.onerror = (event) => {
    if (event.error === 'aborted') {
      return;
    }
    console.error("Speech recognition error:", event.error);
    let message = 'エラーが発生しました';
    switch (event.error) {
      case 'not-allowed':
        message = 'マイク権限が拒否されています';
        break;
      case 'no-speech':
        message = '音声が検出されませんでした';
        break;
      case 'network':
        message = 'ネットワークエラーが発生しました';
        break;
    }
    recError.textContent = message;
  };
} else if (startRecBtn) {
  // ブラウザ非対応時のUI変更
  recStatus.textContent = "状態: 音声認識非対応のブラウザです";
  startRecBtn.disabled = true;
  startRecBtn.classList.add('bg-gray-400', 'cursor-not-allowed');
  startRecBtn.classList.remove('bg-blue-500', 'hover:bg-blue-600');
}

// 【修正】安全かつ確実に音声認識を止めるための共通関数
function forceStopRecognition() {
  if (recognition) {
    try {
      // stop() ではなく abort() にすることで、バッファに残った音声データを即座に破棄してマイクを切断します
      recognition.abort();
    } catch (e) {
      // 既に止まっている場合のエラーなどを回避
    }
  }
}

// --- 【追加】AI通信中にすべての入力・ボタン操作をロック/解除する共通関数 ---
function toggleFormControls(disabled) {
  const submitBtn = form.querySelector('button[type="submit"]');

  if (answerInput) answerInput.disabled = disabled;
  if (startRecBtn) startRecBtn.disabled = disabled;
  if (stopRecBtn) stopRecBtn.disabled = disabled;
  if (clearRecBtn) clearRecBtn.disabled = disabled;
  
  if (submitBtn) {
    submitBtn.disabled = disabled;
    if (disabled) {
      submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
      submitBtn.textContent = '送信中...';
    } else {
      submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
      submitBtn.textContent = '送信';
    }
  }

  // 録音開始ボタンの見た目の調整
  if (startRecBtn) {
    if (disabled) startRecBtn.classList.add('opacity-50');
    else if (SpeechRecognition) startRecBtn.classList.remove('opacity-50');
  }
}
// -------------------------------------------------------------------------

form.addEventListener('submit', async function (e) {
  e.preventDefault();

  // 送信時に音声認識を安全にストップ
  forceStopRecognition();

  const answer = answerInput.value;

  // 【変更】通信開始時に「AI判定中」の表示を出し、ボタン類をすべて無効化
  recStatus.textContent = "状態: 🤖 AIが解答を判定中...";
  recStatus.classList.add('text-blue-600');
  recStatus.classList.remove('text-red-600');
  recError.textContent = ''; // 過去のエラーメッセージを消去
  
  toggleFormControls(true);

  try {
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

  } catch (error) {
    console.error("Transmission error:", error);
    recError.textContent = "通信エラーが発生しました。もう一度お試しください。";
    
    // エラー終了時はフォームのロックを解除して復帰
    recStatus.textContent = "状態: 停止中";
    recStatus.classList.remove('text-blue-600');
    toggleFormControls(false);
  }
});

// 【修正】Gemini API の返却データ（アドバイス・言い換え表現）を描画するよう統合
function renderFeedback(data) {
  console.log('受け取ったdata:', data);
  console.log('turn_order の値:', data.next_phrase?.turn_order);
  const feedbackArea = document.getElementById('feedback-area');

  // フィードバックエリアを一旦クリア
  feedbackArea.innerHTML = '';

  if (data.skipped) {
    // npc_firstなどの自動進行時は表示をスキップ
  } else {
    // 正誤ステータスの設定
    const statusColor = data.is_correct ? 'text-green-400' : 'text-yellow-400';
    const statusText = data.is_correct ? '⭕ 正解！' : '🔺 もう少し！';
    
    // HTML組み立て（Tailwind CSSを使用したメッセージボックス）
    let htmlContent = `
      <div class="bg-gray-800 bg-opacity-90 p-4 rounded-lg border border-gray-600 space-y-3 text-sm text-white">
        <div class="flex flex-col sm:flex-row sm:items-center gap-2">
          <span class="font-bold text-base ${statusColor}">${statusText}</span>
          <span class="text-gray-300">あなたの解答: "${data.user_answer || '(空欄)'}"</span>
        </div>
        <p class="text-gray-200 leading-relaxed">
          <span class="font-bold text-blue-300">💡 先生からのアドバイス:</span><br>${data.feedback_comment}
        </p>
    `;

    // おすすめの言い換え表現（native_suggestions）があればリスト表示
    if (data.native_suggestions && data.native_suggestions.length > 0) {
      htmlContent += `
        <div class="pt-2 border-t border-gray-700">
          <span class="font-bold text-green-300">✨ おすすめの言い換え表現:</span>
          <ul class="list-disc list-inside mt-1 text-gray-300 space-y-1">
      `;
      data.native_suggestions.forEach(suggestion => {
        htmlContent += `<li class="italic">"${suggestion}"</li>`;
      });
      htmlContent += `
          </ul>
        </div>
      `;
    }

    htmlContent += `</div>`;
    feedbackArea.innerHTML = htmlContent;
  }

  // --- 進行ライフサイクルロジック ---
  if (data.is_correct) {
    if (data.finished) {
      showFinishMessage();
      return;
    }

    if (data.next_phrase) {
      updateQuestion(data.next_phrase);

      if (data.next_phrase.turn_order === 'npc_first') {
        // 解答不要なので、音声認識ボタンを含むコンテナごと隠す
        if (inputContainer) inputContainer.style.display = 'none';
        
        // AIのアドバイスコメントを読む時間を確保するため、自動遷移ディレイを5秒（5000ms）に延長
        setTimeout(() => {
          advancePhrase();
        }, 5000);
      } else {
        // プレイヤーのターンになったらコンテナを表示し、ロックを解除
        if (inputContainer) inputContainer.style.display = '';
        recStatus.textContent = "状態: 停止中";
        recStatus.classList.remove('text-blue-600');
        toggleFormControls(false);
      }
    }
  } else {
    // 不正解の場合はその場でストップし、コンテナを表示させてユーザーのフォームロックを解除（再入力を促す）
    if (inputContainer) inputContainer.style.display = '';
    recStatus.textContent = "状態: 停止中";
    recStatus.classList.remove('text-blue-600');
    toggleFormControls(false);
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
    if (staffJpEl) staffJpEl.style.display = 'none';
  }
}

// npc_first を自動で通過させ、次のフレーズ情報を取得するための関数
async function advancePhrase() {
  // 自動進行の前にも念のため音声認識を止める
  forceStopRecognition();

  const response = await fetch(`/practice/${sceneId}/answer/`, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({ answer: '' }),
  });

