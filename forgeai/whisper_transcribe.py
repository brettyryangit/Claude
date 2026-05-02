import openai
import requests
import tempfile
import os
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


def transcribe_audio_url(audio_url: str) -> str:
    response = requests.get(audio_url)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return transcript
    finally:
        os.unlink(tmp_path)
