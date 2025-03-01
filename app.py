from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import os
import requests
import subprocess
import mtranslate

app = Flask(__name__)

def translate_text(text, source_lang, target_lang):
    try:
        translated_text = mtranslate.translate(text, target_lang, source_lang)
        return translated_text
    except Exception as e:
        print(f"Translation failed: {e}")
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    temp_webm_path = os.path.join("static", "audio", "temp.webm")
    temp_wav_path = os.path.join("static", "audio", "temp.wav")

    # Save the uploaded file temporarily
    audio_file.save(temp_webm_path)

    # Convert webm to wav using ffmpeg
    try:
        subprocess.run([
            "ffmpeg", "-i", temp_webm_path, "-acodec", "pcm_s16le", "-ar", "16000", temp_wav_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Failed to convert audio file"}), 500

    # Transcribe the converted WAV file
    recognizer = sr.Recognizer()
    with sr.AudioFile(temp_wav_path) as source:
        audio = recognizer.record(source)

    try:
        transcript = recognizer.recognize_google(audio)
        return jsonify({"transcript": transcript})
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio"}), 400
    except sr.RequestError:
        return jsonify({"error": "API unavailable"}), 500
    finally:
        # Clean up temporary files
        if os.path.exists(temp_webm_path):
            os.remove(temp_webm_path)
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

import time  # Add this import at the top of your file

@app.route("/translate", methods=["POST"])
def translate():
    data = request.json
    text = data.get("text")
    source_lang = data.get("source_lang")
    target_lang = data.get("target_lang")

    if not text or not source_lang or not target_lang:
        return jsonify({"error": "Missing parameters"}), 400

    translated_text = translate_text(text, source_lang, target_lang)
    if translated_text:
        # Generate audio for translated text
        tts = gTTS(translated_text, lang=target_lang)
        audio_path = os.path.join("static", "audio", "translation.mp3")
        tts.save(audio_path)

        # Add a timestamp to the URL to prevent caching
        timestamp = int(time.time())
        audio_url = f"/static/audio/translation.mp3?t={timestamp}"

        return jsonify({"translated_text": translated_text, "audio_url": audio_url})
    return jsonify({"error": "Translation failed"}), 500
if __name__ == "__main__":
    os.makedirs(os.path.join("static", "audio"), exist_ok=True)
    app.run(debug=True)
