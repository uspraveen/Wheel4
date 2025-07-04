#!/usr/bin/env python3
"""
Wheel4 - AI Brain UI
Modern, clean interface with proper Claude orange theme
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import threading
import time
import re
import json

from database import get_api_key, save_api_key, save_interaction, get_session_history
from ai_service import get_ai_response, extract_json_from_response
from screen_capture import capture_full_screen

# Claude orange color palette
CLAUDE_ORANGE = "#FF6B35"
CLAUDE_ORANGE_LIGHT = "#FF8A65"
CLAUDE_ORANGE_DARK = "#E65100"

class GlassTextEdit(QTextEdit):
    """Modern text edit with Claude orange theme"""
    
    enterPressed = pyqtSignal()
    
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMaximumHeight(100)
        self.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 107, 53, 0.3);
                border-radius: 16px;
                color: white;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                padding: 16px 20px;
                selection-background-color: rgba(255, 107, 53, 0.3);
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border: 1px solid rgba(255, 107, 53, 0.5);
                background: rgba(255, 255, 255, 0.08);
            }}
        """)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.enterPressed.emit()
        else:
            super().keyPressEvent(event)

class ModernAPIDialog(QDialog):
    """Clean, properly sized API key setup dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("AI Brain Setup")
        self.setFixedSize(500, 400)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container with clean styling
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background: rgba(45, 45, 45, 0.98);
                border-radius: 20px;
                border: 1px solid rgba(255, 107, 53, 0.2);
            }
        """)
        layout.addWidget(main_widget)
        
        # Content layout
        content_layout = QVBoxLayout(main_widget)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(50, 50, 50, 50)
        
        # Logo/Icon area
        icon_layout = QHBoxLayout()
        icon_layout.addStretch()
        
        # Logo placeholder
        logo_label = QLabel("🧠")
        logo_label.setStyleSheet(f"""
            QLabel {{
                color: {CLAUDE_ORANGE};
                font-size: 52px;
                background: transparent;
                border: none;
            }}
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(logo_label)
        
        icon_layout.addStretch()
        content_layout.addLayout(icon_layout)
        
        # Header
        header = QLabel("AI Brain")
        header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                letter-spacing: -0.5px;
                background: transparent;
                border: none;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Enter your OpenAI API key to get started")
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 18px;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: transparent;
                border: none;
            }
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(subtitle)
        
        # API Key input
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("sk-...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setMinimumHeight(50)
        self.api_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.08);
                border: 2px solid rgba(255, 107, 53, 0.3);
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                padding: 15px 20px;
                selection-background-color: rgba(255, 107, 53, 0.3);
            }}
            QLineEdit:focus {{
                border: 2px solid rgba(255, 107, 53, 0.6);
                background: rgba(255, 255, 255, 0.12);
            }}
        """)
        content_layout.addWidget(self.api_input)
        
        # Show/Hide toggle
        self.show_key_checkbox = QCheckBox("Show API key")
        self.show_key_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                spacing: 10px;
                background: transparent;
                border: none;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid rgba(255, 107, 53, 0.5);
                background: rgba(255, 255, 255, 0.05);
            }}
            QCheckBox::indicator:checked {{
                background: {CLAUDE_ORANGE};
                border: 2px solid {CLAUDE_ORANGE};
            }}
        """)
        self.show_key_checkbox.toggled.connect(self.toggle_password_visibility)
        content_layout.addWidget(self.show_key_checkbox)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 100, 100, 0.9);
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                background: transparent;
                border: none;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 2px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 12px 30px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.25);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.04);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Continue")
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CLAUDE_ORANGE};
                border: 2px solid {CLAUDE_ORANGE};
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                padding: 12px 30px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background: {CLAUDE_ORANGE_LIGHT};
                border: 2px solid {CLAUDE_ORANGE_LIGHT};
            }}
            QPushButton:pressed {{
                background: {CLAUDE_ORANGE_DARK};
                border: 2px solid {CLAUDE_ORANGE_DARK};
            }}
        """)
        self.save_btn.clicked.connect(self.save_api_key)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        content_layout.addLayout(button_layout)
        
        self.api_input.setFocus()
        
    def toggle_password_visibility(self, checked):
        if checked:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
            
    def save_api_key(self):
        key = self.api_input.text().strip()
        if not key:
            self.status_label.setText("Please enter an API key")
            return
            
        if not key.startswith("sk-"):
            self.status_label.setText("API key should start with 'sk-'")
            return
            
        self.api_key = key
        self.accept()

class SettingsDialog(QDialog):
    """Clean settings dialog with proper text visibility"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 350)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main container
        main_widget = QWidget()
        main_widget.setStyleSheet("""
            QWidget {
                background: rgba(45, 45, 45, 0.98);
                border-radius: 16px;
                border: 1px solid rgba(255, 107, 53, 0.2);
            }
        """)
        layout.addWidget(main_widget)
        
        # Content layout
        content_layout = QVBoxLayout(main_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("⚙️ Settings")
        header.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: transparent;
                border: none;
            }
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(header)
        
        # Settings buttons
        button_style = f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.06);
                border: 2px solid rgba(255, 107, 53, 0.2);
                border-radius: 10px;
                color: white;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 15px 20px;
                text-align: left;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background: rgba(255, 107, 53, 0.1);
                border: 2px solid rgba(255, 107, 53, 0.4);
                color: white;
            }}
            QPushButton:pressed {{
                background: rgba(255, 107, 53, 0.05);
            }}
        """
        
        # Logout button
        logout_btn = QPushButton("🔐 Change API Key")
        logout_btn.setStyleSheet(button_style)
        logout_btn.clicked.connect(self.logout)
        content_layout.addWidget(logout_btn)
        
        # Website button
        site_btn = QPushButton("🌐 Visit Website")
        site_btn.setStyleSheet(button_style)
        site_btn.clicked.connect(self.open_website)
        content_layout.addWidget(site_btn)
        
        # UI Dimensions
        dimensions_btn = QPushButton("📐 UI Dimensions")
        dimensions_btn.setStyleSheet(button_style)
        dimensions_btn.clicked.connect(self.ui_dimensions)
        content_layout.addWidget(dimensions_btn)
        
        # About
        about_btn = QPushButton("ℹ️ About")
        about_btn.setStyleSheet(button_style)
        about_btn.clicked.connect(self.about)
        content_layout.addWidget(about_btn)
        
        # Spacer
        content_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {CLAUDE_ORANGE};
                border: 2px solid {CLAUDE_ORANGE};
                border-radius: 10px;
                color: white;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                padding: 12px 20px;
            }}
            QPushButton:hover {{
                background: {CLAUDE_ORANGE_LIGHT};
                border: 2px solid {CLAUDE_ORANGE_LIGHT};
            }}
            QPushButton:pressed {{
                background: {CLAUDE_ORANGE_DARK};
                border: 2px solid {CLAUDE_ORANGE_DARK};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        content_layout.addWidget(close_btn)
        
    def logout(self):
        self.accept()
        self.parent().reset_data()
        
    def open_website(self):
        import webbrowser
        webbrowser.open("https://github.com/yourusername/wheel4")
        
    def ui_dimensions(self):
        QMessageBox.information(self, "UI Dimensions", "Current screen width: 1920px\nUI adapts automatically to screen size")
        
    def about(self):
        QMessageBox.information(self, "About", "Wheel4 AI Brain v2.0\nAn intelligent on-screen AI assistant")

class AIBrainUI(QMainWindow):
    """Modern AI Brain interface with clean design"""
    
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.current_response_data = None
        self.setup_ui()
        self.check_api_key()
        
    def setup_ui(self):
        """Setup modern UI with Claude orange theme"""
        # Window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get screen dimensions
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.setGeometry(0, 0, self.screen_width, 72)
        
        # Main container
        container = QWidget()
        self.setCentralWidget(container)
        
        container.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 30, 0.9);
                border-bottom: 2px solid rgba(255, 107, 53, 0.3);
            }
        """)
        
        # Main layout
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 16, 24, 16)
        self.main_layout.setSpacing(16)
        
        # Setup components
        self.setup_top_bar()
        self.setup_question_input()
        self.setup_response_area()
        
    def setup_top_bar(self):
        """Setup minimal top bar with logo and controls"""
        top_bar = QHBoxLayout()
        
        # Logo and status
        logo_status_layout = QHBoxLayout()
        logo_status_layout.setSpacing(12)
        
        # Logo placeholder
        logo_label = QLabel("🧠")
        logo_label.setStyleSheet(f"""
            QLabel {{
                color: {CLAUDE_ORANGE};
                font-size: 24px;
                background: transparent;
                border: none;
            }}
        """)
        logo_status_layout.addWidget(logo_label)
        
        # Status indicator
        self.status_label = QLabel("AI Brain")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 17px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                letter-spacing: -0.3px;
                padding: 8px 16px;
                background: rgba(255, 107, 53, 0.15);
                border-radius: 18px;
                border: 1px solid rgba(255, 107, 53, 0.3);
            }}
        """)
        logo_status_layout.addWidget(self.status_label)
        
        top_bar.addLayout(logo_status_layout)
        
        top_bar.addStretch()
        
        # Session info
        self.session_info = QLabel(f"Session {self.session_id}")
        self.session_info.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                padding: 4px 8px;
            }
        """)
        top_bar.addWidget(self.session_info)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Settings button
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 107, 53, 0.25);
                border-radius: 8px;
                color: {CLAUDE_ORANGE};
                font-size: 16px;
                font-weight: 500;
                padding: 8px 10px;
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
            }}
            QPushButton:hover {{
                background: rgba(255, 107, 53, 0.1);
                border: 1px solid rgba(255, 107, 53, 0.4);
            }}
        """)
        self.settings_btn.clicked.connect(self.show_settings)
        controls_layout.addWidget(self.settings_btn)
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 69, 58, 0.8);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 18px;
                font-weight: 600;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton:hover {
                background: rgba(255, 69, 58, 1.0);
            }
        """)
        self.close_btn.clicked.connect(self.close_application)
        controls_layout.addWidget(self.close_btn)
        
        top_bar.addLayout(controls_layout)
        self.main_layout.addLayout(top_bar)
        
    def setup_question_input(self):
        """Setup question input area"""
        self.input_container = QWidget()
        input_layout = QVBoxLayout(self.input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(16)
        
        # Input field
        self.question_input = GlassTextEdit("Ask AI about your screen... (Shift+Enter for new line)")
        self.question_input.enterPressed.connect(self.process_question)
        input_layout.addWidget(self.question_input)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        quick_questions = [
            ("Explain", "Explain what's on this screen"),
            ("Issues", "Find any issues or problems"),
            ("Next", "What should I do next?"),
            ("Summary", "Summarize the key information")
        ]
        
        for label, question in quick_questions:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 107, 53, 0.08);
                    border: 1px solid rgba(255, 107, 53, 0.2);
                    border-radius: 8px;
                    color: {CLAUDE_ORANGE};
                    font-size: 13px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    font-weight: 500;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 107, 53, 0.15);
                    border: 1px solid rgba(255, 107, 53, 0.35);
                }}
                QPushButton:pressed {{
                    background: rgba(255, 107, 53, 0.05);
                }}
            """)
            btn.clicked.connect(lambda checked, q=question: self.quick_question(q))
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        input_layout.addLayout(actions_layout)
        
        self.input_container.hide()
        self.main_layout.addWidget(self.input_container)
        
    def setup_response_area(self):
        """Setup response display area"""
        self.response_container = QWidget()
        response_layout = QVBoxLayout(self.response_container)
        response_layout.setContentsMargins(0, 0, 0, 0)
        response_layout.setSpacing(16)
        
        # Main response area
        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setMaximumHeight(300)
        self.response_area.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 107, 53, 0.15);
                border-radius: 16px;
                color: white;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                padding: 20px;
                line-height: 1.6;
                selection-background-color: rgba(255, 107, 53, 0.3);
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                border-radius: 4px;
                margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 107, 53, 0.4);
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 107, 53, 0.6);
            }}
        """)
        response_layout.addWidget(self.response_area)
        
        # Suggested questions area
        self.suggestions_container = QWidget()
        suggestions_layout = QVBoxLayout(self.suggestions_container)
        suggestions_layout.setContentsMargins(0, 0, 0, 0)
        suggestions_layout.setSpacing(10)
        
        # Suggestions title
        suggestions_title = QLabel("Suggested Questions")
        suggestions_title.setStyleSheet(f"""
            QLabel {{
                color: {CLAUDE_ORANGE};
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                letter-spacing: -0.1px;
                padding: 0 4px;
            }}
        """)
        suggestions_layout.addWidget(suggestions_title)
        
        # Suggestions buttons container
        self.suggestions_scroll = QScrollArea()
        self.suggestions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.suggestions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.suggestions_scroll.setWidgetResizable(True)
        self.suggestions_scroll.setMaximumHeight(60)
        self.suggestions_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        self.suggestions_widget = QWidget()
        self.suggestions_layout = QVBoxLayout(self.suggestions_widget)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(8)
        
        self.suggestions_scroll.setWidget(self.suggestions_widget)
        suggestions_layout.addWidget(self.suggestions_scroll)
        
        self.suggestions_container.hide()
        response_layout.addWidget(self.suggestions_container)
        
        self.response_container.hide()
        self.main_layout.addWidget(self.response_container)
        
    def parse_json_response(self, response_text):
        """Parse JSON response with robust error handling"""
        # Use the improved extraction function
        response_data = extract_json_from_response(response_text)
        
        if response_data and isinstance(response_data, dict):
            # Ensure all required fields exist
            required_fields = ["response", "code_blocks", "links", "suggested_questions"]
            for field in required_fields:
                if field not in response_data:
                    if field == "response":
                        response_data[field] = response_text
                    else:
                        response_data[field] = []
            
            print("✅ JSON response parsed successfully")
            return response_data
        
        # Fallback: create structured response
        print("⚠️  Using fallback response format")
        return {
            "response": response_text,
            "code_blocks": [],
            "links": [],
            "suggested_questions": [
                "What should I do next?",
                "Can you explain more?",
                "Are there any issues?",
                "How can I improve this?"
            ]
        }
        
    def format_response(self, response_data):
        """Format structured response with Claude orange styling"""
        html_parts = []
        
        # Main response text
        response_text = response_data.get('response', '')
        if response_text:
            # Convert markdown formatting with Claude orange
            response_text = re.sub(r'\*\*(.*?)\*\*', f'<strong style="color: {CLAUDE_ORANGE};">\\1</strong>', response_text)
            response_text = re.sub(r'\*(.*?)\*', r'<em style="color: rgba(255, 255, 255, 0.95);">\1</em>', response_text)
            
            # Handle code spans
            response_text = re.sub(r'`(.*?)`', f'<code style="background: rgba(255, 107, 53, 0.1); color: {CLAUDE_ORANGE}; padding: 3px 6px; border-radius: 4px; font-family: SF Mono, Monaco, monospace; font-size: 14px;">\\1</code>', response_text)
            
            # Handle bullet points
            response_text = re.sub(r'^- (.*?)$', f'<div style="margin: 10px 0; padding-left: 20px; position: relative;"><span style="position: absolute; left: 0; color: {CLAUDE_ORANGE};">•</span>\\1</div>', response_text, flags=re.MULTILINE)
            
            # Handle numbered lists
            response_text = re.sub(r'^(\d+)\. (.*?)$', f'<div style="margin: 10px 0; padding-left: 26px; position: relative;"><span style="position: absolute; left: 0; color: {CLAUDE_ORANGE}; font-weight: 600;">\\1.</span>\\2</div>', response_text, flags=re.MULTILINE)
            
            # Handle paragraphs
            response_text = response_text.replace('\n\n', '</p><p style="margin: 18px 0 0 0;">')
            response_text = response_text.replace('\n', '<br>')
            
            html_parts.append(f'<p style="margin: 0; color: rgba(255, 255, 255, 0.95);">{response_text}</p>')
        
        # Code blocks
        code_blocks = response_data.get('code_blocks', [])
        if code_blocks:
            html_parts.append('<div style="margin-top: 24px;">')
            for code_block in code_blocks:
                html_parts.append(f'''
                <div style="margin: 16px 0; background: rgba(0, 0, 0, 0.3); border-radius: 12px; border: 1px solid rgba(255, 107, 53, 0.2); overflow: hidden;">
                    <div style="padding: 10px 16px; border-bottom: 1px solid rgba(255, 107, 53, 0.2); background: rgba(255, 107, 53, 0.05);">
                        <span style="color: {CLAUDE_ORANGE}; font-size: 13px; font-weight: 600; font-family: SF Mono, Monaco, monospace;">
                            {code_block.get('language', 'code')}
                        </span>
                    </div>
                    <div style="padding: 16px; font-family: SF Mono, Monaco, monospace; font-size: 14px; color: rgba(255, 255, 255, 0.95); line-height: 1.5; white-space: pre-wrap;">
                        {code_block.get('code', '')}
                    </div>
                </div>
                ''')
            html_parts.append('</div>')
        
        # Links
        links = response_data.get('links', [])
        if links:
            html_parts.append('<div style="margin-top: 24px;">')
            for link in links:
                html_parts.append(f'''
                <div style="margin: 12px 0; padding: 16px; background: rgba(255, 107, 53, 0.05); border-radius: 12px; border-left: 4px solid {CLAUDE_ORANGE};">
                    <a href="{link['url']}" style="color: {CLAUDE_ORANGE}; text-decoration: none; font-weight: 600; font-size: 15px;">{link['title']}</a>
                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 14px; margin-top: 6px; line-height: 1.4;">{link['description']}</div>
                </div>
                ''')
            html_parts.append('</div>')
        
        return ''.join(html_parts)
        
    def check_api_key(self):
        """Check API key"""
        api_key = get_api_key()
        if not api_key:
            QTimer.singleShot(300, self.show_api_key_setup)
        else:
            self.status_label.setText("AI Brain")
            
    def show_api_key_setup(self):
        """Show API key setup dialog"""
        dialog = ModernAPIDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            save_api_key(dialog.api_key)
            self.status_label.setText("AI Brain")
            print("✅ API key saved")
        else:
            self.close_application()
            
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def reset_data(self):
        """Reset all data"""
        save_api_key("")
        self.show_api_key_setup()
            
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            
    def show_question_input(self):
        """Show question input"""
        if not self.isVisible():
            self.show()
            
        self.raise_()
        self.activateWindow()
        
        # Expand window
        self.setGeometry(0, 0, self.screen_width, 220)
        
        self.input_container.show()
        
        self.question_input.setFocus()
        self.question_input.clear()
        
        self.status_label.setText("Listening...")
        
    def quick_question(self, question):
        """Process quick question"""
        self.question_input.setPlainText(question)
        self.process_question()
        
    def process_question(self):
        """Process user question"""
        question = self.question_input.toPlainText().strip()
        if not question:
            return
            
        print(f"🤔 Processing: {question}")
        
        # Clear old response and update UI
        self.response_area.clear()
        self.response_container.hide()
        self.suggestions_container.hide()
        self.input_container.hide()
        self.status_label.setText("Thinking...")
        
        # Expand for response
        self.setGeometry(0, 0, self.screen_width, 400)
        self.response_container.show()
        
        # Show loading placeholder
        self.response_area.setHtml(f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: white;">
            <div style="margin-bottom: 20px; padding: 18px; background: rgba(255, 107, 53, 0.1); border-radius: 12px; border-left: 4px solid {CLAUDE_ORANGE};">
                <div style="color: {CLAUDE_ORANGE}; font-weight: 600; font-size: 14px; margin-bottom: 10px; letter-spacing: -0.1px;">YOUR QUESTION</div>
                <div style="color: rgba(255, 255, 255, 0.95); font-size: 15px; line-height: 1.5;">{question}</div>
            </div>
            <div style="padding: 18px; background: rgba(255, 255, 255, 0.03); border-radius: 12px; border-left: 4px solid rgba(255, 255, 255, 0.2);">
                <div style="color: {CLAUDE_ORANGE}; font-weight: 600; font-size: 14px; margin-bottom: 10px; letter-spacing: -0.1px;">AI RESPONSE</div>
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 15px;">
                    <span style="opacity: 0.6;">●</span> Analyzing your screen...
                </div>
            </div>
        </div>
        """)
        
        # Process in background
        def process_in_background():
            try:
                start_time = time.time()
                
                # Optimized screenshot capture
                current_time = time.time()
                if (self.last_screenshot and 
                    current_time - self.last_screenshot_time < 2.0):
                    screenshot = self.last_screenshot
                    print("📸 Using cached screenshot")
                else:
                    print("📸 Capturing fresh screenshot...")
                    screenshot = capture_full_screen()
                    self.last_screenshot = screenshot
                    self.last_screenshot_time = current_time
                
                # Get context
                history = get_session_history(self.session_id, limit=3)
                context = ""
                if history:
                    context_parts = []
                    for q, r, t in history:
                        context_parts.append(f"Q: {q[:100]}")
                        context_parts.append(f"A: {r[:150]}")
                    context = "\n".join(context_parts)
                
                print("🤖 Getting AI response...")
                
                # Get response
                response = get_ai_response(question, screenshot, context)
                
                # Parse response
                if isinstance(response, dict) and "error" in response:
                    QTimer.singleShot(0, lambda: self.show_error(response["error"]))
                    return
                
                response_data = self.parse_json_response(response)
                
                elapsed = time.time() - start_time
                print(f"✅ Response received in {elapsed:.2f}s")
                
                # Store for UI update
                self.current_response_data = response_data
                self.current_question = question
                
                # Update UI
                QTimer.singleShot(0, self.show_final_response)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                QTimer.singleShot(0, lambda: self.show_error(str(e)))
        
        threading.Thread(target=process_in_background, daemon=True).start()
        
    def show_final_response(self):
        """Show the final response"""
        response_data = self.current_response_data
        question = self.current_question
        
        # Format the response
        formatted_response = self.format_response(response_data)
        
        # Create the full HTML
        full_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; line-height: 1.6; color: white;">
            <div style="margin-bottom: 24px; padding: 18px; background: rgba(255, 107, 53, 0.1); border-radius: 12px; border-left: 4px solid {CLAUDE_ORANGE};">
                <div style="color: {CLAUDE_ORANGE}; font-weight: 600; font-size: 14px; margin-bottom: 10px; letter-spacing: -0.1px;">YOUR QUESTION</div>
                <div style="color: rgba(255, 255, 255, 0.95); font-size: 15px; line-height: 1.5;">{question}</div>
            </div>
            
            <div style="padding: 18px; background: rgba(255, 255, 255, 0.03); border-radius: 12px; border-left: 4px solid rgba(255, 255, 255, 0.2);">
                <div style="color: {CLAUDE_ORANGE}; font-weight: 600; font-size: 14px; margin-bottom: 12px; letter-spacing: -0.1px;">AI RESPONSE</div>
                <div style="color: rgba(255, 255, 255, 0.95); font-size: 15px; line-height: 1.7;">
                    {formatted_response}
                </div>
            </div>
        </div>
        """
        
        # Set the response
        self.response_area.setHtml(full_html)
        
        self.status_label.setText("Complete")
        
        # Show suggested questions
        suggested_questions = response_data.get('suggested_questions', [])
        if suggested_questions:
            self.show_suggested_questions(suggested_questions)
        
        # Save to database
        save_interaction(self.session_id, question, response_data.get('response', ''))
        
    def show_suggested_questions(self, questions):
        """Show suggested questions with proper error handling"""
        # Clear existing suggestions safely
        for i in reversed(range(self.suggestions_layout.count())):
            item = self.suggestions_layout.itemAt(i)
            if item and item.widget():
                item.widget().setParent(None)
        
        # Add new suggestions
        for question in questions[:3]:  # Max 3 suggestions
            btn = QPushButton(question)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 107, 53, 0.08);
                    border: 1px solid rgba(255, 107, 53, 0.2);
                    border-radius: 8px;
                    color: {CLAUDE_ORANGE};
                    font-size: 13px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    font-weight: 500;
                    padding: 10px 16px;
                    text-align: left;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 107, 53, 0.15);
                    border: 1px solid rgba(255, 107, 53, 0.35);
                }}
                QPushButton:pressed {{
                    background: rgba(255, 107, 53, 0.05);
                }}
            """)
            btn.clicked.connect(lambda checked, q=question: self.ask_suggested_question(q))
            self.suggestions_layout.addWidget(btn)
        
        self.suggestions_container.show()
        
    def ask_suggested_question(self, question):
        """Ask a suggested question"""
        self.question_input.setPlainText(question)
        self.process_question()
        
    def show_error(self, error):
        """Show error message"""
        self.status_label.setText("Error")
        
        self.setGeometry(0, 0, self.screen_width, 180)
        error_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; padding: 20px; background: rgba(255, 100, 100, 0.1); border-radius: 12px; border-left: 4px solid rgba(255, 100, 100, 0.6);">
            <div style="color: rgba(255, 100, 100, 0.9); font-weight: 600; font-size: 14px; margin-bottom: 10px;">ERROR</div>
            <div style="color: rgba(255, 255, 255, 0.95); font-size: 15px; line-height: 1.5;">{error}</div>
        </div>
        """
        self.response_area.setHtml(error_html)
        self.response_container.show()
        
        QTimer.singleShot(5000, lambda: self.status_label.setText("AI Brain"))
        
    def close_application(self):
        """Close application"""
        QApplication.instance().quit()
        
    def closeEvent(self, event):
        """Handle close event"""
        self.close_application()
        event.accept()