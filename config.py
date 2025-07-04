# config.py

# OpenAI API Key - Replace with your actual key
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# Hotkey to toggle the window's visibility
HOTKEY = "<ctrl>+"

# Hotkey to ask AI about the screen/context
ASK_AI_HOTKEY = "<ctrl>+enter"

# Audio settings
SAMPLE_RATE = 16000  # Hz
CHUNK_DURATION_MS = 30  # ms
CHANNELS = 1
VAD_AGGRESSIVENESS = 3  # 0 (least aggressive) to 3 (most aggressive)
SILENCE_DURATION_S = 2  # Seconds of silence to consider an utterance complete