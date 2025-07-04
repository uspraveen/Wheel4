# hotkeys.py

from pynput import keyboard

class HotkeyManager:
    def __init__(self, toggle_hotkey, toggle_callback, ask_ai_hotkey, ask_ai_callback):
        self.toggle_hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(toggle_hotkey),
            toggle_callback
        )
        self.ask_ai_hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(ask_ai_hotkey),
            ask_ai_callback
        )
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )

    def on_press(self, key):
        self.toggle_hotkey.press(self.listener.canonical(key))
        self.ask_ai_hotkey.press(self.listener.canonical(key))

    def on_release(self, key):
        self.toggle_hotkey.release(self.listener.canonical(key))
        self.ask_ai_hotkey.release(self.listener.canonical(key))

    def start(self):
        self.listener.start()

    def stop(self):
        self.listener.stop()