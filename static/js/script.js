let mediaRecorder;
let audioChunks = [];

document
  .getElementById("record_button")
  .addEventListener("click", startRecording);
document.getElementById("stop_button").addEventListener("click", stopRecording);
document
  .getElementById("speak_button")
  .addEventListener("click", playTranslation);

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
  mediaRecorder.onstop = sendAudioForTranscription;
  mediaRecorder.start();
  document.getElementById("record_button").disabled = true;
  document.getElementById("stop_button").disabled = false;
}

function stopRecording() {
  mediaRecorder.stop();
  document.getElementById("record_button").disabled = false;
  document.getElementById("stop_button").disabled = true;
}

async function sendAudioForTranscription() {
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
  const formData = new FormData();
  formData.append("audio", audioBlob);

  const response = await fetch("/transcribe", {
    method: "POST",
    body: formData,
  });
  const result = await response.json();

  if (result.transcript) {
    document.getElementById("original_text").textContent = result.transcript;
    translateText(result.transcript);
  } else {
    alert("Transcription failed: " + result.error);
  }
  audioChunks = [];
}

async function translateText(text) {
  const sourceLang = document.getElementById("source_lang").value;
  const targetLang = document.getElementById("target_lang").value;

  const response = await fetch("/translate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      source_lang: sourceLang,
      target_lang: targetLang,
    }),
  });
  const result = await response.json();

  if (result.translated_text) {
    document.getElementById("translated_text").textContent =
      result.translated_text;
    document.getElementById("speak_button").dataset.audioUrl = result.audio_url;
  } else {
    alert("Translation failed: " + result.error);
  }
}

function playTranslation() {
  const audioUrl = document.getElementById("speak_button").dataset.audioUrl;
  if (audioUrl) {
    const audio = new Audio(audioUrl);
    audio.play();
  }
}
