# voice_of_python

Offline Multilingual Voice Bot Library for Python  
===============================================

`voice_of_python` is a Python library that provides offline multilingual speech recognition and text-to-speech (TTS) capabilities. It uses the Vosk toolkit for offline speech-to-text and pyttsx3 for offline TTS, supporting multiple languages through automatic language detection.

---

## Features

- Record audio from microphone or accept existing WAV audio files.
- Offline speech-to-text using Vosk models (no API or internet required).
- Automatic language detection with `langid`.
- Text-to-speech in detected language voice (if available locally).
- Works fully on CPU; suitable for local and privacy-sensitive applications.
- Designed for easy integration with chatbots and LLMs.

---

## Installation

Install dependencies:

``` pip install vosk langid pyttsx3 sounddevice numpy soundfile```


*Note:* Download and provide local Vosk models for supported languages separately.

---

## Usage

### 1. Initialize the library with Vosk model paths

from voice_of_python import MultiLingualVoiceBot

model_paths = {
<br>"en": "/path/to/vosk-model-en-us-0.22",<br>
"hi": "/path/to/vosk-model-small-hi-0.22"<br>
}

bot = MultiLingualVoiceBot(model_paths)

### 2. Record from microphone and get transcription

text, lang_code = bot.record_and_transcribe(record_duration=5)<br>
print(f"Detected language: {lang_code}")<br>
print(f"Recognized text: {text}")


### 3. Integrate with your LLM or AI model

Pass `text` to your backend model to generate a reply message.

reply_text = "यहाँ आपका उत्तर है"


### 4. Speak reply in detected language

bot.speak_text(reply_text, lang_code)


### 5. Alternatively, process external audio file and speak reply

audio_file = "user.wav"
reply_text = "Thank you for your question."
bot.process_audio_and_reply(audio_file, reply_text)

---

## API Reference

- **`MultiLingualVoiceBot(model_paths: dict, sample_rate: int = 16000)`**  
  Initialize with `{language_code: vosk_model_path}` mapping.

- **`record_and_transcribe(record_duration: int = 5) -> (str, str)`**  
  Record from mic and return transcription and detected language code.

- **`process_audio_and_reply(audio_input: Union[str, np.ndarray], reply_text: str)`**  
  Transcribe audio (file path or raw numpy array), detect language, speak reply text.

- **`speak_text(text: str, lang_code: str)`**  
  Speak given text in specified language voice.

---

## Contributing

Contributions welcome! Please open issues or pull requests on GitHub.

---

## Acknowledgements

- Vosk: https://alphacephei.com/vosk/  
- pyttsx3: https://pyttsx3.readthedocs.io/en/latest/  
- langid: https://github.com/saffsd/langid.py

---

## Support

Please report issues or questions on the GitHub repository.

---

*Enjoy building multilingual, offline voice-enabled applications with voice_of_python!*
