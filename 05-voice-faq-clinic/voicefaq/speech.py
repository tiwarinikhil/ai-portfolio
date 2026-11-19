"""Speech to text and text to speech, with any OpenAI-compatible audio API.

Set LLM_API_KEY (and LLM_BASE_URL for other providers). Optional:
  STT_MODEL  default whisper-1
  TTS_MODEL  default tts-1
  TTS_VOICE  default alloy
Without a key, the agent runs text-only: you type what the caller said.
"""

import os


class SpeechUnavailable(RuntimeError):
    pass


def _client():
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise SpeechUnavailable("No LLM_API_KEY set. Running in text-only mode.")
    from openai import OpenAI

    return OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL"))


def transcribe(audio_path: str) -> str:
    client = _client()
    with open(audio_path, "rb") as f:
        out = client.audio.transcriptions.create(model=os.getenv("STT_MODEL", "whisper-1"), file=f)
    return out.text


def speak(text: str, out_path: str) -> str:
    client = _client()
    audio = client.audio.speech.create(
        model=os.getenv("TTS_MODEL", "tts-1"), voice=os.getenv("TTS_VOICE", "alloy"), input=text
    )
    audio.write_to_file(out_path)
    return out_path
