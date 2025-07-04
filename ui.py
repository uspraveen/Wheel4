# ui.py

from PyQt6.QtWidgets import QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QObject

class Communicate(QObject):
    transcription_ready = pyqtSignal(str)
    ai_response_ready = pyqtSignal(str)

class GlassAppUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.comm = Communicate()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Glass - Python Clone")
        self.setGeometry(100, 100, 500, 300)

        # Make the window frameless and stay on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Set a transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Main text box for transcriptions and AI responses
        self.transcription_box = QTextEdit(self)
        self.transcription_box.setReadOnly(True)
        self.transcription_box.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border: 1px solid #555;
            border-radius: 10px;
            font-size: 16px;
            padding: 10px;
        """)
        layout.addWidget(self.transcription_box)

    def update_transcription(self, text):
        self.transcription_box.append(f"<b>You:</b> {text}")

    def update_ai_response(self, text):
        self.transcription_box.append(f"<b>AI:</b> {text}")

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()