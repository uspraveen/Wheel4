# transcription.py

import openai
from config import OPENAI_API_KEY

# Initialize the OpenAI client
if OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY":
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

def transcribe_audio(audio_data):
    """Transcribes audio data using the OpenAI Whisper API."""
    if not client:
        return "OpenAI API key not set. Please set it in config.py"

    try:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_data,
            response_format="text"
        )
        return response
    except Exception as e:
        print(f"Error during transcription: {e}")
        return "Error during transcription."
