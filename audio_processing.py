# audio_processing.py

import threading
import sounddevice as sd
import webrtcvad
import numpy as np
from collections import deque
import io
import time

from config import SAMPLE_RATE, CHUNK_DURATION_MS, CHANNELS, VAD_AGGRESSIVENESS, SILENCE_DURATION_S
from ai_service import transcribe_audio, get_ai_response
from database import save_transcription, get_all_transcripts
from screen_capture import capture_screen_as_base64

class AudioProcessor(threading.Thread):
    def __init__(self, ui_update_callback, ai_response_callback):
        super().__init__()
        self.ui_update_callback = ui_update_callback
        self.ai_response_callback = ai_response_callback
        self.is_running = False
        self.vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self.frames_per_chunk = (SAMPLE_RATE * CHUNK_DURATION_MS) // 1000
        self.silence_chunks = int((SILENCE_DURATION_S * 1000) / CHUNK_DURATION_MS)

    def run(self):
        self.is_running = True
        voiced_frames = deque()
        silence_counter = 0

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', blocksize=self.frames_per_chunk) as stream:
            while self.is_running:
                frame, overflowed = stream.read(self.frames_per_chunk)
                if overflowed:
                    print("Audio overflowed!")

                is_speech = self.vad.is_speech(frame.tobytes(), SAMPLE_RATE)

                if is_speech:
                    voiced_frames.append(frame)
                    silence_counter = 0
                elif voiced_frames:
                    silence_counter += 1
                    if silence_counter > self.silence_chunks:
                        # End of utterance, process the audio
                        audio_data = np.concatenate(list(voiced_frames))
                        voiced_frames.clear()
                        silence_counter = 0

                        # Transcribe and get AI response in a new thread to avoid blocking
                        threading.Thread(target=self.process_audio_and_get_ai_response, args=(audio_data,)).start()

    def process_audio_and_get_ai_response(self, audio_data):
        # Convert to a file-like object for OpenAI API
        audio_file = io.BytesIO()
        audio_file.write(audio_data.tobytes())
        audio_file.seek(0)

        # 1. Transcribe audio
        transcription = transcribe_audio(audio_file)
        if transcription and transcription != "Error during transcription.":
            save_transcription("user", transcription)
            self.ui_update_callback(transcription) # Update UI with user's speech

            # 2. Capture screen
            screen_image_data = capture_screen_as_base64()

            # 3. Get conversation history
            conversation_history = get_all_transcripts()

            # 4. Get AI response
            ai_response = get_ai_response(transcription, screen_image_data, conversation_history)
            if ai_response and ai_response != "Error getting AI response.":
                self.ai_response_callback(ai_response) # Update UI with AI's response

    def stop(self):
        self.is_running = False