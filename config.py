#!/usr/bin/env python3
"""
Wheel4 - Configuration
Basic app configuration
"""

# Application info
APP_NAME = "Wheel4 AI Brain"
APP_VERSION = "2.0"

# Hotkeys (can be modified here)
TOGGLE_HOTKEY = "<ctrl>+\\"
QUESTION_HOTKEY = "<ctrl>+<enter>"

# UI Settings
WINDOW_HEIGHT_NORMAL = 60      # Normal height (just status bar)
WINDOW_HEIGHT_INPUT = 100      # Height when showing input
WINDOW_HEIGHT_RESPONSE = 250   # Height when showing response

# Auto-hide settings
AUTO_HIDE_DELAY = 10000  # ms (10 seconds)

# Database settings
DATABASE_FILE = "ai_brain.db"
PROMPTS_FILE = "prompts.md"

# Debug settings
DEBUG_LOGS = True

def log(message):
    """Simple logging function"""
    if DEBUG_LOGS:
        print(message)