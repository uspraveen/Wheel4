#!/usr/bin/env python3
"""
Wheel4 - Global Hotkeys
System-wide hotkey handling
"""

from pynput import keyboard

class HotkeyManager:
    def __init__(self, toggle_hotkey, toggle_callback, question_hotkey, question_callback):
        """Initialize hotkey manager with two hotkeys"""
        self.toggle_callback = toggle_callback
        self.question_callback = question_callback
        
        # Parse hotkey combinations
        try:
            self.toggle_hotkey = keyboard.HotKey(
                keyboard.HotKey.parse(toggle_hotkey),
                toggle_callback
            )
            print(f"⌨️  Toggle hotkey: {toggle_hotkey}")
        except Exception as e:
            print(f"❌ Invalid toggle hotkey '{toggle_hotkey}': {e}")
            self.toggle_hotkey = None
        
        try:
            self.question_hotkey = keyboard.HotKey(
                keyboard.HotKey.parse(question_hotkey),
                question_callback
            )
            print(f"⌨️  Question hotkey: {question_hotkey}")
        except Exception as e:
            print(f"❌ Invalid question hotkey '{question_hotkey}': {e}")
            self.question_hotkey = None
        
        # Keyboard listener
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
    
    def on_press(self, key):
        """Handle key press"""
        try:
            if self.toggle_hotkey:
                self.toggle_hotkey.press(self.listener.canonical(key))
            if self.question_hotkey:
                self.question_hotkey.press(self.listener.canonical(key))
        except Exception as e:
            # Ignore hotkey processing errors
            pass
    
    def on_release(self, key):
        """Handle key release"""
        try:
            if self.toggle_hotkey:
                self.toggle_hotkey.release(self.listener.canonical(key))
            if self.question_hotkey:
                self.question_hotkey.release(self.listener.canonical(key))
        except Exception as e:
            # Ignore hotkey processing errors
            pass
    
    def start(self):
        """Start listening for hotkeys"""
        try:
            self.listener.start()
            print("✅ Hotkey listener started")
        except Exception as e:
            print(f"❌ Failed to start hotkey listener: {e}")
    
    def stop(self):
        """Stop listening for hotkeys"""
        try:
            if self.listener.running:
                self.listener.stop()
                print("🛑 Hotkey listener stopped")
        except Exception as e:
            print(f"❌ Error stopping hotkey listener: {e}")