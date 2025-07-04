# ai_service.py

import openai
from config import OPENAI_API_KEY
from database import save_transcription
import base64

# Initialize the OpenAI client
client = None
if OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY":
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
else:
    print("Warning: OpenAI API key not set. Please set it in config.py to enable AI features.")

def transcribe_audio(audio_file):
    """Transcribes audio data using the OpenAI Whisper API."""
    if not client:
        return "OpenAI API key not set. Please set it in config.py"

    try:
        # The OpenAI API expects a file-like object for audio transcription
        # audio_file should be an io.BytesIO object
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", audio_file.getvalue(), "audio/wav"), # Provide filename and content type
            response_format="text"
        )
        return response
    except Exception as e:
        print(f"Error during audio transcription: {e}")
        return "Error during transcription."

def get_ai_response(prompt_text, image_data=None, conversation_history=None):
    """Gets a response from the OpenAI GPT-4o model with text and optional image context."""
    if not client:
        return "OpenAI API key not set. Please set it in config.py"

    messages = []

    # Add conversation history from database
    if conversation_history:
        for speaker, text in conversation_history:
            messages.append({"role": "user" if speaker == "user" else "assistant", "content": text})

    # Add the current prompt and image if available
    content_parts = []
    content_parts.append({"type": "text", "text": prompt_text})

    if image_data:
        # Encode image data to base64 for OpenAI Vision API
        base64_image = base64.b64encode(image_data).decode('utf-8')
        content_parts.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
        })

    messages.append({"role": "user", "content": content_parts})

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Using gpt-4o for multimodal capabilities
            messages=messages,
            max_tokens=500
        )
        ai_response = response.choices[0].message.content
        save_transcription("assistant", ai_response) # Save AI response to DB
        return ai_response
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return "Error getting AI response."
