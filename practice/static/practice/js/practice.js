console.log("=== practice.js の読み込みを開始しました ===");

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

// --- Web Speech API (TTS: 音声合成) 関数の定義 ---
function speakEnglishText(text) {
  if (!text) return;
  if (!('speechSynthesis' in window)) {
    console.warn('このブラウザは音声読み上げに対応していません。');
    return;
  }

  // 再生中の音声を一度キャンセル
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = 0.95; // 読み上げ速度（少しゆっくり）
  utterance.pitch = 1.0;

  // 英語のボイスを選択
  const voices = window.speechSynthesis.getVoices();
  const englishVoice = voices.find(v => v.lang.startsWith('en'));
  if (englishVoice) {
    utterance.voice = englishVoice;
  }

  window.speechSynthesis.speak(utterance);
}

// 画面の要素がすべて読み込まれてから処理を開始する
document.addEventListener('DOMContentLoaded', () => {
  console.log("practice.js が読み込まれました");

  const form = document.getElementById('answer-form');
  const sceneId = form ? form.dataset.sceneId : null;

  const startRecBtn = document.getElementById('start-rec-btn');
  const stopRecBtn = document.getElementById('stop-rec-btn');
  const clearRecBtn = document.getElementById('clear-rec-btn'); 
  const recStatus = document.getElementById('rec-status');
  const recError = document.getElementById('rec-error');
  const answerInput = document.getElementById('answer-input');
  const inputContainer = document.getElementById('input-container'); 

  // --- 初期表示時の AI セリフ自動読み上げ ---
  const initialNpcText = document.getElementById('npc-text');
  if (initialNpcText && initialNpcText.textContent.trim()) {
    // 画面ロード完了後、少し間を置いて発声
    setTimeout(() => {
      speakEnglishText(initialNpcText.textContent.trim());
    }, 500);
  }

  // --- Web Speech API (STT: 音声認識) の初期化 ---
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';        
    recognition.interimResults = true; 
    recognition.continuous = false;

    // 認識開始イベント
    recognition.onstart = () => {
      console.log("🎤 音声認識が開始されました");
      if (recStatus) {
        recStatus.textContent = "状態: 🔴 録音中...";
        recStatus.className = "text-red-600 font-bold";
      }
      if (startRecBtn) {
        startRecBtn.disabled = true;
        startRecBtn.classList.add('opacity-50');
      }
      if (stopRecBtn) {
        stopRecBtn.disabled = false;
        stopRecBtn.classList.remove('opacity-50');
      }
    };

    // 認識終了イベント
    recognition.onend = () => {
      console.log("🛑 音声認識が終了しました");
      if (recStatus && !recStatus.textContent.includes('🤖')) {
        resetRecStatusUI();
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
      if (answerInput) {
        answerInput.value = finalTranscript + interimTranscript;
      }
    };

    // エラー処理
    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      if (event.error === 'aborted') return;

      let message = 'エラーが発生しました';
      switch (event.error) {
        case 'not-allowed':
          message = 'マイク権限が拒否されています';
          break;
        case 'no-speech':
          message = '音声が検出されませんでした';
          break;
        case 'network':
          message = 'ネットワークエラーが発生しました（※Chrome/Edge等でお試しください）';
          break;
      }
      if (recError) recError.textContent = message;
      resetRecStatusUI();
    };

  } else {
    console.error("このブラウザは SpeechRecognition に対応していません");
    if (recStatus) recStatus.textContent = "状態: 音声認識非対応のブラウザです";
    if (startRecBtn) {
      startRecBtn.disabled = true;
      startRecBtn.classList.add('bg-gray-400', 'cursor-not-allowed');
    }
  }

  // --- ボタンのイベント登録 ---
  if (startRecBtn) {
    startRecBtn.addEventListener('click', () => {
      console.log("「録音開始」ボタンがクリックされました");
      if (!recognition) return;

      if (recError) recError.textContent = '';
      
      // 念のため起動中のものを一度強制停止してからスタート
      try {
        recognition.stop();
      } catch (e) {}

      setTimeout(() => {
        try {
          recognition.start();
        } catch (e) {
          console.error("recognition.start() エラー:", e);
        }
      }, 50);
    });
  }

  if (stopRecBtn) {
    stopRecBtn.addEventListener('click', () => {
      console.log("「停止」ボタンがクリックされました");
      if (recognition) recognition.stop();
    });
  }

  if (clearRecBtn) {
    clearRecBtn.addEventListener('click', () => {
      forceStopRecognition();    
      setTimeout(() => {
        if (answerInput) answerInput.value = '';     
        if (recError) recError.textContent = ''; 
        resetRecStatusUI();
      }, 50);
    });
  }

  // UIリセット用関数
  function resetRecStatusUI() {
    if (recStatus) {
      recStatus.textContent = "状態: 停止中";
      recStatus.className = "text-gray-500 font-medium";
    }
    if (startRecBtn) {
      startRecBtn.disabled = false;
      startRecBtn.classList.remove('opacity-50');
    }
    if (stopRecBtn) {
      stopRecBtn.disabled = true;
      stopRecBtn.classList.add('opacity-50');
    }
  }

  function forceStopRecognition() {
    if (recognition) {
      try { recognition.abort(); } catch (e) {}
    }
  }

  function toggleFormControls(disabled) {
    if (!form) return;
    const submitBtn = form.querySelector('button[type="submit"]');

    if (answerInput) answerInput.disabled = disabled;
    if (startRecBtn) {
      startRecBtn.disabled = disabled;
      if (disabled) startRecBtn.classList.add('opacity-50');
      else if (SpeechRecognition) startRecBtn.classList.remove('opacity-50');
    }
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
  }

  // --- 解答送信（Ajax POST処理） ---
  if (form) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      forceStopRecognition();

      const answer = answerInput ? answerInput.value : '';

      if (recStatus) {
        recStatus.textContent = "状態: 🤖 AIが解答を判定中...";
        recStatus.className = "text-blue-600 font-bold";
      }
      if (recError) recError.textContent = ''; 
      
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

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        renderFeedback(data);
        if (answerInput) answerInput.value = '';

      } catch (error) {
        console.error("Transmission error:", error);
        if (recError) recError.textContent = "通信エラーが発生しました。もう一度お試しください。";
        resetRecStatusUI();
        toggleFormControls(false);
      }
    });
  }

  function renderFeedback(data) {
    console.log('受け取ったdata:', data);
    const feedbackArea = document.getElementById('feedback-area');
    if (!feedbackArea) return;

    feedbackArea.innerHTML = '';

    if (!data.skipped) {
      const statusColor = data.is_correct ? 'text-emerald-400' : 'text-amber-400';
      const statusText = data.is_correct ? '⭕ 正解！' : '🔺 もう少し！';
      
      let htmlContent = `
        <div class="bg-slate-900 bg-opacity-95 p-4 rounded-xl border border-slate-700 space-y-2 text-sm text-slate-200 shadow-xl mt-3">
          <div class="flex items-center gap-2">
            <span class="font-bold ${statusColor} text-base">${statusText}</span>
            <span class="text-slate-400 text-xs">あなたの解答: "${data.user_answer || '(空欄)'}"</span>
          </div>
          <p class="text-slate-300 leading-relaxed text-xs sm:text-sm">
            <span class="font-bold text-blue-400">💡 先生からのアドバイス:</span><br>${data.feedback_comment}
          </p>
      `;

      if (data.native_suggestions && data.native_suggestions.length > 0) {
        htmlContent += `
          <div class="pt-2 border-t border-slate-800">
            <span class="font-bold text-emerald-400 text-xs sm:text-sm">✨ おすすめの言い換え表現:</span>
            <ul class="list-disc list-inside mt-1 text-slate-300 space-y-1 text-xs italic">
        `;
        data.native_suggestions.forEach(suggestion => {
          // 単語ごとに音声再生できるボタンも併記
          const escapedSuggestion = suggestion.replace(/'/g, "\\'");
          htmlContent += `
            <li class="flex items-center gap-2">
              <span>"${suggestion}"</span>
              <button type="button" onclick="speakEnglishText('${escapedSuggestion}')" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-0.5 rounded border border-slate-600 transition">
                🔊 聴く
              </button>
            </li>
          `;
        });
        htmlContent += `
            </ul>
          </div>
        `;
      }

      htmlContent += `</div>`;
      feedbackArea.innerHTML = htmlContent;
    }

    resetRecStatusUI();
    toggleFormControls(false);

    if (data.is_correct) {
      if (data.finished) {
        showFinishMessage();
        return;
      }

      if (data.next_phrase) {
        updateQuestion(data.next_phrase);

        if (data.next_phrase.turn_order === 'npc_first') {
          if (inputContainer) inputContainer.style.display = 'none';
          setTimeout(() => {
            advancePhrase();
          }, 5000);
        } else {
          if (inputContainer) inputContainer.style.display = '';
        }
      }
    } else {
      if (inputContainer) inputContainer.style.display = '';
    }
  }

  function updateQuestion(nextPhrase) {
    const npcTextEl = document.getElementById('npc-text');
    const staffJpEl = document.getElementById('staff-jp-text');

    if (npcTextEl) {
      npcTextEl.textContent = nextPhrase.npc_en;
      // 新しいフレーズになったら AI のセリフを自動読み上げ
      if (nextPhrase.npc_en) {
        speakEnglishText(nextPhrase.npc_en);
      }
    }

    if (staffJpEl) {
      const parentFlex = staffJpEl.closest('.flex');
      if (nextPhrase.turn_order === 'staff_first') {
        staffJpEl.textContent = nextPhrase.staff_jp;
        if (parentFlex) parentFlex.style.display = '';
      } else {
        if (parentFlex) parentFlex.style.display = 'none';
      }
    }
  }

  async function advancePhrase() {
    forceStopRecognition();
    try {
      const response = await fetch(`/practice/${sceneId}/answer/`, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCookie('csrftoken'),
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ answer: '' }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      renderFeedback(data);
    } catch (error) {
      console.error("Advance phrase error:", error);
      if (recError) recError.textContent = "通信エラーが発生しました。";
      if (inputContainer) inputContainer.style.display = '';
      resetRecStatusUI();
      toggleFormControls(false);
    }
  }

  function showFinishMessage() {
    const feedbackArea = document.getElementById('feedback-area');
    if (feedbackArea) {
      feedbackArea.innerHTML = `
        <div class="bg-emerald-950/80 border border-emerald-500/30 p-4 rounded-xl text-center text-emerald-200 font-bold text-sm sm:text-base mt-3">
          🎉 このシーンの接客練習はすべて終了です！お疲れ様でした！
        </div>
      `;
    }
    if (inputContainer) inputContainer.style.display = 'none';
  }
});