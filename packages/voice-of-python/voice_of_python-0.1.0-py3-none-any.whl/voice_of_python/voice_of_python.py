import os
import json
import time
import vosk
import langid
import pyttsx3
import soundfile as sf
import sounddevice as sd
import numpy as np


class MultiLingualVoiceBot:
    def __init__(self, model_paths: dict, sample_rate: int = 16000):
        """
        Initialize the voice bot.

        Args:
            model_paths (dict): Mapping of ISO language codes (e.g. 'en', 'hi')
                                to local Vosk model directory paths.
            sample_rate (int): Expected audio sample rate in Hz (default 16000).

        Raises:
            ValueError: If model_paths is empty or any path does not exist.
            RuntimeError: If TTS engine fails to initialize.
        """
        if not model_paths or not isinstance(model_paths, dict):
            raise ValueError(
                "model_paths must be a non-empty dict: language_code -> model_path"
            )
        for lang_code, path in model_paths.items():
            if not os.path.isdir(path):
                raise ValueError(
                    f"Model path for '{lang_code}' does not exist or is not a directory: {path}"
                )
        self.model_paths = model_paths
        self.sample_rate = sample_rate
        self.current_lang = None
        self.model = None
        self.recognizer = None
        try:
            self.engine = pyttsx3.init()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize TTS engine: {e}")

        self.load_model(next(iter(self.model_paths.keys())))

    def load_model(self, lang_code: str):
        if lang_code == self.current_lang:
            return
        model_path = self.model_paths.get(lang_code)
        if model_path is None:
            # fallback to first model
            model_path = next(iter(self.model_paths.values()))
            lang_code = next(iter(self.model_paths.keys()))
            print(f"[Warning] Falling back model to '{lang_code}'")
        try:
            print(f"Loading Vosk model for '{lang_code}' from '{model_path}'")
            self.model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)
            self.current_lang = lang_code
            time.sleep(1)  # Allow time for model to load
        except Exception as e:
            raise RuntimeError(f"Error loading Vosk model '{lang_code}': {e}")

    def record_audio(self, duration: int = 5) -> np.ndarray:
        """Record audio from microphone."""
        try:
            print(f"Recording audio for {duration} seconds...")
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            audio_np = np.squeeze(recording)
            return audio_np
        except Exception as e:
            raise RuntimeError(f"Audio recording failed: {e}")

    def transcribe_raw_audio(self, audio_np: np.ndarray) -> str:
        """Transcribe raw audio numpy array (mono int16)."""
        if self.recognizer is None:
            raise RuntimeError("Recognizer not initialized.")
        try:
            self.recognizer.Reset()
            chunk_size = 4000
            text = ""
            for i in range(0, len(audio_np), chunk_size):
                chunk = audio_np[i : i + chunk_size]
                if self.recognizer.AcceptWaveform(chunk.tobytes()):
                    res = json.loads(self.recognizer.Result())
                    text += " " + res.get("text", "")
            final_res = json.loads(self.recognizer.FinalResult())
            text += " " + final_res.get("text", "")
            return text.strip()
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe audio from a WAV file path."""
        try:
            data, samplerate = sf.read(audio_file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read audio file '{audio_file_path}': {e}")

        if samplerate != self.sample_rate:
            raise ValueError(
                f"Expected sample rate {self.sample_rate}, but got {samplerate}"
            )
        if data.ndim > 1:
            data = data[:, 0]

        return self.transcribe_raw_audio(data)

    def detect_language(self, text: str) -> str:
        """Detect language code from text using langid."""
        if not text:
            raise ValueError("Cannot detect language from empty text")
        lang_code, conf = langid.classify(text)
        print(f"Detected language: {lang_code} (confidence {conf:.2f})")
        if lang_code not in self.model_paths:
            print(
                f"Language '{lang_code}' not supported, falling back to default language"
            )
            lang_code = next(iter(self.model_paths.keys()))
        return lang_code

    def speak_text(self, text: str, lang_code: str):
        """Speak given text using TTS matching language voice."""
        if not text:
            print("Warning: No text provided for speaking.")
            return

        voices = self.engine.getProperty("voices")
        selected_voice = None
        lang_code = lang_code.lower() if lang_code else ""
        for voice in voices:
            voice_id_lc = voice.id.lower()
            languages = []
            if hasattr(voice, "languages") and voice.languages:
                languages = [
                    l.decode("utf-8").lower() if isinstance(l, bytes) else l.lower()
                    for l in voice.languages
                ]
            if lang_code in voice_id_lc or lang_code in languages:
                selected_voice = voice.id
                break
        if selected_voice:
            self.engine.setProperty("voice", selected_voice)
        print(f"Speaking with voice: {selected_voice or 'default system voice'}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            raise RuntimeError(f"TTS engine error: {e}")

    def record_and_transcribe(self, record_duration: int = 5) -> tuple[str, str]:
        """Record from mic and return transcription and detected language."""
        audio_np = self.record_audio(record_duration)
        text = self.transcribe_raw_audio(audio_np)
        lang_code = self.detect_language(text)
        self.load_model(lang_code)
        return text, lang_code

    def process_audio_and_reply(self, audio_input, reply_text: str):
        """
        Accept audio as file path or numpy array, transcribe, detect language,
        and speak reply_text in same language.

        Args:
            audio_input (str or np.ndarray): Path to WAV file or raw audio numpy array.
            reply_text (str): Text to speak in detected language.
        """
        if isinstance(audio_input, str):
            text = self.transcribe_audio(audio_input)
        elif isinstance(audio_input, np.ndarray):
            text = self.transcribe_raw_audio(audio_input)
        else:
            raise TypeError("audio_input must be a file path (str) or numpy ndarray")

        print(f"Transcribed text: '{text}'")
        lang_code = self.detect_language(text)
        self.load_model(lang_code)
        self.speak_text(reply_text, lang_code)
