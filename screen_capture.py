#!/usr/bin/env python3
"""
Wheel4 - Screen Capture
Simple, reliable screen capture
"""

import mss
from PIL import Image
import io
import time

# Cache screen info for efficiency
_screen_info = None

def get_screen_info():
    """Get screen dimensions, cached for performance"""
    global _screen_info
    if _screen_info is None:
        with mss.mss() as sct:
            # Get primary monitor info
            monitor = sct.monitors[1]  # Index 0 is all monitors combined, 1 is primary
            _screen_info = {
                'width': monitor['width'],
                'height': monitor['height'],
                'left': monitor['left'],
                'top': monitor['top']
            }
            print(f"📐 Screen dimensions: {_screen_info['width']}x{_screen_info['height']}")
    
    return _screen_info

def capture_full_screen():
    """Capture full screen with optimization"""
    try:
        screen_info = get_screen_info()
        
        with mss.mss() as sct:
            # Capture primary monitor
            monitor = {
                'left': screen_info['left'],
                'top': screen_info['top'],
                'width': screen_info['width'],
                'height': screen_info['height']
            }
            
            # Take screenshot
            start_time = time.time()
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            
            # Intelligent resizing for OpenAI API limits
            max_dimension = 2048
            
            if img.width > max_dimension or img.height > max_dimension:
                # Calculate new size maintaining aspect ratio
                ratio = min(max_dimension / img.width, max_dimension / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                
                # Use high-quality resampling
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"📏 Resized screenshot: {img.width}x{img.height}")
            
            # Convert to bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG', optimize=True)
            screenshot_bytes = buffer.getvalue()
            
            capture_time = time.time() - start_time
            size_kb = len(screenshot_bytes) / 1024
            
            print(f"📸 Screenshot captured: {img.width}x{img.height} ({size_kb:.1f}KB) in {capture_time:.2f}s")
            
            return screenshot_bytes
            
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return None