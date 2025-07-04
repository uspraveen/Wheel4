#!/usr/bin/env python3
"""
Wheel4 - On-screen AI Brain
Main entry point with proper Qt threading
"""

import sys
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

from ui import AIBrainUI
from database import initialize_database, create_new_session, close_session
from hotkeys import HotkeyManager

class HotkeyBridge(QObject):
    """Bridge to handle hotkey signals properly on main thread"""
    toggle_requested = pyqtSignal()
    question_requested = pyqtSignal()

def main():
    print("🧠 Starting Wheel4 AI Brain...")
    
    # Initialize database
    initialize_database()
    print("✅ Database initialized")
    
    # Create new session
    session_id = create_new_session()
    print(f"📝 Session {session_id} started")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Create main UI
    ui = AIBrainUI(session_id)
    
    # Create hotkey bridge for thread-safe UI updates
    hotkey_bridge = HotkeyBridge()
    
    # Connect bridge signals to UI methods
    hotkey_bridge.toggle_requested.connect(ui.toggle_visibility)
    hotkey_bridge.question_requested.connect(ui.show_question_input)
    
    # Setup hotkeys with thread-safe callbacks
    def toggle_visibility():
        print("🔄 Toggle requested")
        hotkey_bridge.toggle_requested.emit()
    
    def ask_question():
        print("❓ Question requested")
        hotkey_bridge.question_requested.emit()
    
    hotkey_manager = HotkeyManager(
        toggle_hotkey="<ctrl>+\\",
        toggle_callback=toggle_visibility,
        question_hotkey="<ctrl>+<enter>",
        question_callback=ask_question
    )
    
    hotkey_manager.start()
    print("⌨️  Hotkeys active: Ctrl+\\ (toggle), Ctrl+Enter (ask)")
    
    # Show UI
    ui.show()
    ui.raise_()
    ui.activateWindow()
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    
    # Cleanup on exit
    def cleanup():
        print("🛑 Shutting down...")
        hotkey_manager.stop()
        close_session(session_id)
        print(f"📝 Session {session_id} closed")
        print("✅ Cleanup complete")
    
    app.aboutToQuit.connect(cleanup)
    
    print("🚀 AI Brain ready!")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()