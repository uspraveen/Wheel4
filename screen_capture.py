# screen_capture.py

import mss
from PIL import Image
import io

def capture_screen_as_base64():
    """Captures the primary screen and returns it as a base64 encoded string."""
    with mss.mss() as sct:
        # Get information of monitor 1
        monitor = sct.monitors[1]

        # Capture the screen
        sct_img = sct.grab(monitor)

        # Convert to PIL Image
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

        # Save to a BytesIO object
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        
        # Return the bytes (OpenAI API expects bytes, not base64 directly for image upload)
        return buffered.getvalue()

