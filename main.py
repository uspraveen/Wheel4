# main.py

import sys
from PyQt6.QtWidgets import QApplication

from ui import GlassAppUI
from audio_processing import AudioProcessor
from hotkeys import HotkeyManager
from database import initialize_database
from config import HOTKEY

def main():
    # Initialize the database
    initialize_database()

    # Create the application
    app = QApplication(sys.argv)
    ui = GlassAppUI()

    # Connect the audio processor to the UI
    def ui_update_callback(text):
        ui.comm.transcription_ready.emit(text)

    ui.comm.transcription_ready.connect(ui.update_transcription)

    # Start the audio processor
    audio_processor = AudioProcessor(ui_update_callback)
    audio_processor.start()

    # Start the hotkey manager
    hotkey_manager = HotkeyManager(HOTKEY, ui.toggle_visibility)
    hotkey_manager.start()

    # Show the UI
    ui.show()

    # Ensure threads are stopped when the app closes
    def on_about_to_quit():
        audio_processor.stop()
        hotkey_manager.stop()

    app.aboutToQuit.connect(on_about_to_quit)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
