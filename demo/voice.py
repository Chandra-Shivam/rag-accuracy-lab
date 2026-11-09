"""DEMO: narration text -> spoken WAV with Gemini text-to-speech, cached on disk.

Clips are cached by hash(model + voice + text), so editing one scene re-generates only that clip.
Only the narration is sent: a style instruction like "Read this in a calm voice:" was read aloud as part of the clip.
Needs GOOGLE_API_KEY in .env.
"""
import hashlib
import time
import wave
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

MODEL = "gemini-3.8-flash-tts"
# TODO(human): pick the voice. Others to try: Charon (informative), Puck (upbeat), Aoede (breezy), Iapetus (clear).
VOICE = "Kore"
RETRIES = 4

_client = None


def _get_client():
    global _client
    if _client is None:
        load_dotenv()
        _client = genai.Client()
    return _client


def speak(text, out_dir):
    """Returns the path of a WAV file with the text spoken. Calls Gemini only on a cache miss."""
    key = hashlib.sha256(f"{MODEL}|{VOICE}|{text}".encode()).hexdigest()[:16]
    path = Path(out_dir) / f"{key}.wav"
    if path.exists():
        return path
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE))))
    for attempt in range(1, RETRIES + 1):
        try:
            reply = _get_client().models.generate_content(model=MODEL, contents=text, config=config)
            break
        except errors.APIError as e:
            # The free tier allows only 10 voice requests per model per day; waiting seconds won't help, so stop.
            # Clips already made are cached, so the next run continues from here.
            if e.code == 429 and "PerDay" in str(e):
                raise SystemExit(f"voice: daily quota for {MODEL} used up; run the build again after it resets") from e
            # Per-minute quota (429) or busy (503): both pass within a minute or two. Anything else is a real error.
            if e.code not in (429, 503) or attempt == RETRIES:
                raise
            print(f"  voice: {e.code}, retrying in {30 * attempt} s", flush=True)
            time.sleep(30 * attempt)
    data = reply.candidates[0].content.parts[0].inline_data.data
    path.parent.mkdir(parents=True, exist_ok=True)
    if data[:4] == b"RIFF":
        path.write_bytes(data)
    else:
        # Some TTS models return raw 16-bit PCM at 24 kHz instead of a WAV file.
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(data)
    return path


def duration(path):
    """Length of a WAV file in seconds."""
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()
