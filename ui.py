#!/usr/bin/env python3
"""
Wheel4 - Enhanced Complete UI with Session-Based Custom Instructions
Fixed hotkey handling and improved custom instructions dialog
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import threading
import time
import re
import json
import html
import math
import webbrowser
import os

from database import (
    get_api_key, save_api_key, save_interaction, get_session_history, 
    get_all_sessions, switch_to_session, create_new_session,
    save_session_custom_instructions, get_session_custom_instructions,
    get_session_info
)
from ai_service import get_ai_response, extract_json_from_response
from screen_capture import capture_full_screen

# Enhanced Color Palette with Higher Opacity
GLASS_LIGHT = QColor(255, 255, 255, 60)    # Increased from 30
GLASS_MEDIUM = QColor(255, 255, 255, 45)   # Increased from 20
GLASS_DARK = QColor(255, 255, 255, 30)     # Increased from 12
BORDER_LIGHT = QColor(255, 255, 255, 80)   # Increased from 50
BORDER_MEDIUM = QColor(255, 255, 255, 60)  # Increased from 30

TEXT_PRIMARY = QColor(255, 255, 255, 255)
TEXT_SECONDARY = QColor(255, 255, 255, 240)  # Increased from 220
TEXT_TERTIARY = QColor(255, 255, 255, 200)   # Increased from 180
TEXT_INPUT = QColor(255, 255, 255, 255)      # Increased from 240

ACCENT_BLUE = QColor(0, 122, 255)
SUCCESS_GREEN = QColor(48, 209, 88)
ERROR_RED = QColor(255, 69, 58)
WARNING_ORANGE = QColor(255, 159, 10)

BG_PRIMARY = QColor(0, 0, 0, 180)    # Increased from 120
BG_SECONDARY = QColor(0, 0, 0, 120)  # Increased from 80

class AIWorkerThread(QThread):
    """Enhanced AI processing thread with better timeout handling"""
    
    response_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    screenshot_captured = pyqtSignal()
    status_update = pyqtSignal(str)
    
    def __init__(self, question, session_id, web_search_enabled=False, custom_instructions=""):
        super().__init__()
        self.question = question
        self.session_id = session_id
        self.web_search_enabled = web_search_enabled
        self.custom_instructions = custom_instructions
        self.retry_count = 0
        self.max_retries = 2
        
    def run(self):
        """Enhanced run with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                self.retry_count = attempt
                if attempt > 0:
                    print(f"🔄 Retry attempt {attempt}/{self.max_retries}")
                    self.status_update.emit(f"Retrying... (attempt {attempt + 1})")
                    time.sleep(1)  # Brief delay before retry
                
                return self._process_ai_request()
                
            except Exception as e:
                error_msg = f"AI processing error (attempt {attempt + 1}): {str(e)}"
                print(f"❌ {error_msg}")
                
                if attempt < self.max_retries:
                    continue  # Try again
                else:
                    self.error_occurred.emit(f"Failed after {self.max_retries + 1} attempts: {str(e)}")
                    return
    
    def _process_ai_request(self):
        """Core AI processing logic"""
        print(f"🔄 AI Worker Thread started for: {self.question}")
        if self.custom_instructions:
            print(f"🎯 Using custom instructions ({len(self.custom_instructions)} chars)")
        
        # Step 1: Screenshot capture with enhanced timeout
        screenshot = None
        if not self.web_search_enabled:
            print("📸 Capturing screenshot...")
            self.status_update.emit("Taking screenshot...")
            
            try:
                screenshot = self._capture_screenshot_with_timeout(timeout=5)  # Increased timeout
                if screenshot:
                    size_kb = len(screenshot) / 1024
                    print(f"✅ Screenshot: {size_kb:.1f}KB")
                    self.screenshot_captured.emit()
                else:
                    print("⚠️ Screenshot capture failed, continuing without")
            except Exception as e:
                print(f"⚠️ Screenshot error: {e}, continuing without")
        
        # Step 2: Get context
        self.status_update.emit("Getting context...")
        from database import get_session_context
        context = get_session_context(self.session_id)
        
        if context and len(context) > 500:
            context = context[:500] + "..."
        
        # Step 3: Prepare question
        api_question = self.question
        if self.web_search_enabled:
            api_question = f"[WEB_SEARCH] {self.question}"
        
        # Step 4: Enhanced AI call with custom instructions
        print("🤖 Making AI call with custom instructions...")
        self.status_update.emit("Getting AI response...")
        
        response = get_ai_response(
            api_question, 
            screenshot, 
            context, 
            None,  # No template_key
            self.custom_instructions
        )
        
        if isinstance(response, dict) and "error" in response:
            print(f"❌ AI error: {response['error']}")
            raise Exception(response["error"])
            
        print("✅ AI response received")
        self.response_ready.emit((response, self.question))
    
    def _capture_screenshot_with_timeout(self, timeout=5):
        """Enhanced screenshot capture with timeout"""
        import queue
        
        screenshot_queue = queue.Queue()
        
        def screenshot_worker():
            try:
                result = capture_full_screen()
                screenshot_queue.put(("success", result))
            except Exception as e:
                screenshot_queue.put(("error", str(e)))
        
        screenshot_thread = threading.Thread(target=screenshot_worker)
        screenshot_thread.daemon = True
        screenshot_thread.start()
        
        try:
            result_type, result = screenshot_queue.get(timeout=timeout)
            if result_type == "success":
                return result
            else:
                raise Exception(result)
        except queue.Empty:
            print(f"⏰ Screenshot timeout after {timeout}s")
            return None

class SessionCustomInstructionsDialog(QDialog):
    """Enhanced dialog for session-based custom instructions with improved layout"""
    
    def __init__(self, parent=None, session_id=None):
        super().__init__(parent)
        self.session_id = session_id
        self.current_instructions = ""
        self.is_locked = False
        self.setup_ui()
        self.load_current_instructions()
        
    def setup_ui(self):
        self.setWindowTitle("Custom Instructions")
        self.setFixedSize(540, 450)  # Slightly smaller height
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Center the dialog
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            int(screen.height() * 0.15)
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Enhanced main container with clean background
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(30, 30, 30, 250),
                    stop: 1 rgba(20, 20, 20, 240));
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 100);
            }}
        """)
        layout.addWidget(self.main_widget)
        
        content_layout = QVBoxLayout(self.main_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 25, 30, 25)
        
        # Clean header with close button
        header_layout = QHBoxLayout()
        
        # Title section - simplified
        title = QLabel("🎯 Custom Instructions")
        title.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 255);
                font-size: 22px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 69, 58, 200);
                border: none;
                border-radius: 14px;
                color: white;
                font-size: 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 69, 58, 255);
            }}
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn)
        
        content_layout.addLayout(header_layout)
        
        # Enhanced description
        desc_label = QLabel("Configure AI behavior for this session. Instructions will be locked after your first interaction to maintain consistency.")
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 200);
                font-size: 14px;
                font-weight: 400;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                line-height: 1.5;
                background: transparent;
                border: none;
                margin-bottom: 5px;
            }}
        """)
        desc_label.setWordWrap(True)
        content_layout.addWidget(desc_label)
        
        # Session info with lock status
        info_layout = QHBoxLayout()
        if self.session_id:
            session_info = get_session_info(self.session_id)
            if session_info:
                session_label = QLabel(f"Session: {session_info['name']}")
                session_label.setStyleSheet(f"""
                    QLabel {{
                        color: rgba(0, 122, 255, 255);
                        font-size: 13px;
                        font-weight: 500;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                        background: transparent;
                        border: none;
                    }}
                """)
                info_layout.addWidget(session_label)
        
        info_layout.addStretch()
        
        # Lock status indicator
        self.lock_indicator = QLabel("")
        self.lock_indicator.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 159, 10, 255);
                font-size: 12px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: rgba(255, 159, 10, 20);
                padding: 4px 8px;
                border-radius: 6px;
                border: 1px solid rgba(255, 159, 10, 60);
            }}
        """)
        info_layout.addWidget(self.lock_indicator)
        
        content_layout.addLayout(info_layout)
        
        # Custom instructions text area with clear label
        instructions_label = QLabel("Instructions")
        instructions_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 240);
                font-size: 15px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: transparent;
                border: none;
                margin-bottom: 8px;
            }}
        """)
        content_layout.addWidget(instructions_label)
        
        self.instructions_input = QTextEdit()
        self.instructions_input.setPlaceholderText("Enter custom instructions here...\n\nExample:\n• Respond as a senior developer\n• Focus on best practices\n• Include error handling in code\n• Prefer Python solutions")
        self.instructions_input.setMinimumHeight(140)
        self.instructions_input.setMaximumHeight(140)
        self.instructions_input.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(40, 40, 40, 200);
                border: 2px solid rgba(255, 255, 255, 100);
                border-radius: 12px;
                color: rgba(255, 255, 255, 255);
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                padding: 15px;
                selection-background-color: rgba(0, 122, 255, 80);
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border: 2px solid rgba(0, 122, 255, 150);
                background: rgba(45, 45, 45, 220);
            }}
            /* Modern scrollbar styling */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 100),
                    stop: 1 rgba(0, 122, 255, 120));
                border-radius: 4px;
                min-height: 20px;
                border: 1px solid rgba(0, 122, 255, 40);
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 140),
                    stop: 1 rgba(0, 122, 255, 160));
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                height: 0px;
                background: transparent;
            }}
        """)
        content_layout.addWidget(self.instructions_input)
        
        # Action buttons - removed character count
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumHeight(40)
        clear_btn.setMinimumWidth(80)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 80);
                border-radius: 10px;
                color: rgba(255, 255, 255, 255);
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 12px 20px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 40);
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 10);
                color: rgba(255, 255, 255, 100);
                border: 1px solid rgba(255, 255, 255, 30);
            }}
        """)
        clear_btn.clicked.connect(self.clear_instructions)
        
        save_btn = QPushButton("Save Instructions")
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(160)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 122, 255, 255);
                border: 1px solid rgba(0, 122, 255, 255);
                border-radius: 10px;
                color: white;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                padding: 12px 20px;
            }}
            QPushButton:hover {{
                background: rgba(0, 122, 255, 230);
            }}
            QPushButton:disabled {{
                background: rgba(100, 100, 100, 150);
                border: 1px solid rgba(100, 100, 100, 150);
                color: rgba(255, 255, 255, 150);
            }}
        """)
        save_btn.clicked.connect(self.save_instructions)
        
        # Store buttons for enabling/disabling
        self.clear_btn = clear_btn
        self.save_btn = save_btn
        
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        content_layout.addLayout(button_layout)
        
    def load_current_instructions(self):
        """Load current instructions and check lock status"""
        if self.session_id:
            instructions = get_session_custom_instructions(self.session_id)
            self.current_instructions = instructions
            self.instructions_input.setPlainText(instructions)
            
            # Check if session has any interactions (which would indicate locked state)
            from database import get_session_history
            history = get_session_history(self.session_id, limit=1)
            self.is_locked = len(history) > 0 and bool(instructions)
            
            self.update_lock_status()
            
    def update_lock_status(self):
        """Update lock status indicators"""
        if self.is_locked:
            self.lock_indicator.setText("🔒 LOCKED")
            self.instructions_input.setReadOnly(True)
            self.clear_btn.setEnabled(False)
            self.save_btn.setEnabled(False)
            self.instructions_input.setStyleSheet(self.instructions_input.styleSheet() + """
                QTextEdit { 
                    background: rgba(30, 30, 30, 120); 
                    border: 2px solid rgba(255, 159, 10, 50);
                    color: rgba(255, 255, 255, 200);
                }
            """)
        else:
            self.lock_indicator.setText("")
            self.instructions_input.setReadOnly(False)
            self.clear_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            
    def clear_instructions(self):
        """Clear instructions if not locked"""
        if not self.is_locked:
            self.instructions_input.clear()
        
    def save_instructions(self):
        """Save instructions if not locked"""
        if self.is_locked:
            return
            
        instructions = self.instructions_input.toPlainText().strip()
        
        if self.session_id:
            save_session_custom_instructions(self.session_id, instructions)
            print(f"💾 Saved custom instructions for session {self.session_id}")
        
        self.current_instructions = instructions
        self.accept()
        
    def get_instructions(self):
        """Get current instructions"""
        return self.current_instructions

class CustomInstructionsButton(QPushButton):
    """Enhanced custom instructions button"""
    
    instructions_changed = pyqtSignal(str)
    
    def __init__(self, session_id=None):
        super().__init__("🎯")
        self.session_id = session_id
        self.current_instructions = ""
        self.is_locked = False
        self.setup_ui()
        self.load_instructions()
        
    def setup_ui(self):
        self.setFixedSize(28, 28)
        self.setToolTip("Custom Instructions")
        self.update_button_appearance()
        self.clicked.connect(self.show_instructions_dialog)
        
    def update_session(self, session_id):
        """Update session and reload instructions"""
        self.session_id = session_id
        self.load_instructions()
        
    def load_instructions(self):
        """Load instructions and check lock status"""
        if self.session_id:
            instructions = get_session_custom_instructions(self.session_id)
            self.current_instructions = instructions
            
            # Check lock status
            from database import get_session_history
            history = get_session_history(self.session_id, limit=1)
            self.is_locked = len(history) > 0 and bool(instructions)
            
            self.update_button_appearance()
            
    def show_instructions_dialog(self):
        """Show custom instructions dialog"""
        if not self.session_id:
            print("❌ No session ID available")
            return
            
        dialog = SessionCustomInstructionsDialog(self.parent(), self.session_id)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            instructions = dialog.get_instructions()
            self.current_instructions = instructions
            self.update_button_appearance()
            
            # Emit change signal
            self.instructions_changed.emit(instructions)
            
            print(f"🎯 Custom instructions updated for session {self.session_id}")
            
    def update_button_appearance(self):
        """Enhanced button appearance"""
        if self.current_instructions:
            if self.is_locked:
                # Locked instructions - orange
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255, 159, 10, 120);
                        border: 1px solid rgba(255, 159, 10, 180);
                        border-radius: 14px;
                        color: white;
                        font-size: 14px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 159, 10, 140);
                        border: 1px solid rgba(255, 159, 10, 200);
                    }}
                """)
                self.setToolTip(f"🔒 Custom Instructions Locked ({len(self.current_instructions)} chars)")
            else:
                # Active but unlocked instructions - blue
                self.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(0, 122, 255, 120);
                        border: 1px solid rgba(0, 122, 255, 180);
                        border-radius: 14px;
                        color: white;
                        font-size: 14px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background: rgba(0, 122, 255, 140);
                        border: 1px solid rgba(0, 122, 255, 200);
                    }}
                """)
                self.setToolTip(f"🎯 Custom Instructions Active ({len(self.current_instructions)} chars)")
        else:
            # Default appearance
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(40, 40, 40, 150);
                    border: 1px solid rgba(255, 255, 255, 60);
                    border-radius: 14px;
                    color: rgba(255, 255, 255, 255);
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: rgba(0, 122, 255, 80);
                    border: 1px solid rgba(0, 122, 255, 120);
                }}
            """)
            self.setToolTip("Custom Instructions")
    
    def get_current_instructions(self):
        """Get current instructions"""
        return self.current_instructions

class FastBlurWidget(QWidget):
    """Enhanced widget with higher opacity"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def paintEvent(self, event):
        """Enhanced paint event with glassy black look"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Glassy black gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(15, 15, 15, 200))   # Darker, more opaque
        gradient.setColorAt(1, QColor(8, 8, 8, 180))      # Very dark
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(255, 255, 255, 40), 1))  # Subtle border
        
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRoundedRect(rect, 12, 12)

class EnhancedTextEdit(QTextEdit):
    """Enhanced text edit with fixed hotkey handling"""
    
    enterPressed = pyqtSignal()
    webSearchToggled = pyqtSignal(bool)
    emptyEnterPressed = pyqtSignal()
    
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.base_height = 56
        self.line_height = 26
        self.max_lines = 3
        self.web_search_enabled = False
        self.input_mode_active = False  # Track if we're in input mode
        self.ignore_enter_until = 0  # Timestamp to ignore Enter keys until
        
        self.setMaximumHeight(self.base_height)
        self.setMinimumHeight(self.base_height)
        self.setStyleSheet(self.get_enhanced_style())
        
        self.setup_placeholder_handling()
        
        self.height_animation = QPropertyAnimation(self, b"maximumHeight")
        self.height_animation.setDuration(150)
        self.height_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.textChanged.connect(self.fast_height_adjustment)
        self.setup_web_search_button()
        
    def set_input_mode(self, active):
        """Set whether we're in active input mode"""
        self.input_mode_active = active
        if active:
            # When entering input mode, ignore Enter keys for a short time
            # to prevent global hotkey from being processed by this widget
            import time
            self.ignore_enter_until = time.time() + 0.2  # 200ms protection
        
    def setup_placeholder_handling(self):
        """Setup placeholder with better positioning"""
        self.placeholder_label = QLabel(self.placeholderText(), self)
        self.placeholder_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 180);
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
        """)
        self.placeholder_label.move(22, 20)
        self.placeholder_label.show()
        self.textChanged.connect(self.update_placeholder_visibility)
        
    def update_placeholder_visibility(self):
        """Update placeholder visibility"""
        if self.toPlainText().strip():
            self.placeholder_label.hide()
        else:
            self.placeholder_label.show()
            
    def resizeEvent(self, event):
        """Handle resize"""
        super().resizeEvent(event)
        if hasattr(self, 'web_search_btn'):
            self.position_web_search_button()
        if hasattr(self, 'placeholder_label'):
            self.placeholder_label.move(22, 20)
        
    def setup_web_search_button(self):
        """Setup web search button"""
        self.web_search_btn = QPushButton("🌐", self)
        self.web_search_btn.setFixedSize(28, 28)
        self.web_search_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 25);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 14px;
                color: rgba(255, 255, 255, 200);
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(0, 122, 255, 50);
                border: 1px solid rgba(0, 122, 255, 120);
                color: rgba(0, 122, 255, 255);
            }}
            QPushButton:checked {{
                background: rgba(0, 122, 255, 120);
                border: 1px solid rgba(0, 122, 255, 180);
                color: white;
            }}
        """)
        self.web_search_btn.setCheckable(True)
        self.web_search_btn.clicked.connect(self.toggle_web_search)
        self.web_search_btn.setToolTip("Toggle web search")
        self.position_web_search_button()
        
    def position_web_search_button(self):
        """Position web search button"""
        button_x = self.width() - self.web_search_btn.width() - 15
        button_y = (self.height() - self.web_search_btn.height()) // 2
        self.web_search_btn.move(button_x, button_y)
        
    def toggle_web_search(self):
        """Toggle web search"""
        self.web_search_enabled = self.web_search_btn.isChecked()
        self.webSearchToggled.emit(self.web_search_enabled)
        print(f"🌐 Web search: {'Enabled' if self.web_search_enabled else 'Disabled'}")
        
    def get_enhanced_style(self):
        """Enhanced input styling with modern scrollbar"""
        return f"""
            QTextEdit {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 40),
                    stop: 0.5 rgba(255, 255, 255, 30),
                    stop: 1 rgba(255, 255, 255, 20));
                border: 2px solid rgba(255, 255, 255, 120);
                border-radius: 18px;
                color: rgba(255, 255, 255, 255);
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                padding: 20px 50px 16px 22px;
                selection-background-color: rgba(0, 122, 255, 80);
                line-height: 1.4;
            }}
            QTextEdit:focus {{
                border: 2px solid rgba(0, 122, 255, 200);
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 50),
                    stop: 0.5 rgba(255, 255, 255, 40),
                    stop: 1 rgba(255, 255, 255, 30));
                color: rgba(255, 255, 255, 255);
            }}
            /* Modern scrollbar styling */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 100),
                    stop: 1 rgba(0, 122, 255, 120));
                border-radius: 4px;
                min-height: 20px;
                border: 1px solid rgba(0, 122, 255, 40);
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 140),
                    stop: 1 rgba(0, 122, 255, 160));
            }}
            QScrollBar::handle:vertical:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 180),
                    stop: 1 rgba(0, 122, 255, 200));
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                height: 0px;
                background: transparent;
            }}
            QScrollBar:horizontal {{
                height: 0px;
            }}
        """
        
    def fast_height_adjustment(self):
        """Fast height adjustment"""
        doc = self.document()
        doc.setTextWidth(self.width() - 65)
        content_height = int(doc.size().height())
        
        lines = max(1, content_height // self.line_height)
        
        if lines <= self.max_lines:
            new_height = self.base_height + (lines - 1) * self.line_height
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            new_height = self.base_height + (self.max_lines - 1) * self.line_height
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        if new_height != self.maximumHeight():
            self.height_animation.setStartValue(self.maximumHeight())
            self.height_animation.setEndValue(new_height)
            self.height_animation.start()
            self.setMinimumHeight(new_height)
        
    def keyPressEvent(self, event):
        """Fixed key press event - only handle Enter when in input mode and not during hotkey protection"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Check if we should ignore Enter keys (hotkey protection)
            import time
            current_time = time.time()
            if current_time < self.ignore_enter_until:
                print(f"🔒 Ignoring Enter key during hotkey protection ({self.ignore_enter_until - current_time:.2f}s remaining)")
                return  # Ignore this Enter key
            
            # Only handle Enter key if we're actually in input mode and the widget has focus
            if self.input_mode_active and self.hasFocus():
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter = new line
                    super().keyPressEvent(event)
                else:
                    # Regular Enter = process
                    if self.toPlainText().strip():
                        print("📝 Processing typed question")
                        self.enterPressed.emit()
                    else:
                        print("⚡ Processing empty enter (screen analysis)")
                        self.emptyEnterPressed.emit()
            else:
                # Not in input mode, don't handle the key
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def ensure_focus_immediately(self):
        """Ensure focus is set immediately and visibly"""
        print("🎯 Setting input mode and focus with hotkey protection")
        self.set_input_mode(True)  # This now includes hotkey protection
        self.setFocus(Qt.FocusReason.OtherFocusReason)
        self.activateWindow()
        
        # Multiple focus attempts for reliability
        QTimer.singleShot(10, lambda: self.setFocus())
        QTimer.singleShot(50, lambda: self.setFocus())
        QTimer.singleShot(100, self.ensure_cursor_visible)
        
    def ensure_cursor_visible(self):
        """Ensure cursor is visible and at end"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

class LoadingWidget(QWidget):
    """More discreet loading widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)  # Smaller height
        self.dot_index = 0
        self.web_search_enabled = False
        
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(600)  # Slower animation
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # More subtle header
        self.header_label = QLabel("Processing...")
        self.header_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 150);
                font-weight: 500;
                font-size: 12px;
                letter-spacing: 0.5px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            }}
        """)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)
        
        # Subtle dots
        dots_container = QWidget()
        dots_layout = QHBoxLayout(dots_container)
        dots_layout.setContentsMargins(0, 0, 0, 0)
        dots_layout.setSpacing(6)
        dots_layout.addStretch()
        
        self.dots = []
        for i in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(f"""
                QLabel {{
                    color: rgba(0, 122, 255, 60);
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.dots.append(dot)
            dots_layout.addWidget(dot)
        
        dots_layout.addStretch()
        layout.addWidget(dots_container)
        
        self.setStyleSheet(f"""
            LoadingWidget {{
                background: rgba(15, 15, 15, 80);
                border-radius: 10px;
                border-left: 2px solid rgba(0, 122, 255, 60);
            }}
        """)
        
    def set_web_search_mode(self, enabled):
        """Set web search mode"""
        self.web_search_enabled = enabled
        if enabled:
            self.header_label.setText("Searching...")
        else:
            self.header_label.setText("Processing...")
    
    def set_status(self, status):
        """Set custom status"""
        # Make status more subtle
        if "screenshot" in status.lower():
            self.header_label.setText("Capturing...")
        elif "context" in status.lower():
            self.header_label.setText("Analyzing...")
        elif "response" in status.lower():
            self.header_label.setText("Thinking...")
        else:
            self.header_label.setText("Processing...")
    
    def update_animation(self):
        """Update dot animation"""
        for dot in self.dots:
            dot.setStyleSheet(f"""
                QLabel {{
                    color: rgba(0, 122, 255, 60);
                    font-size: 14px;
                    font-weight: bold;
                }}
            """)
        
        if self.dot_index < len(self.dots):
            self.dots[self.dot_index].setStyleSheet(f"""
                QLabel {{
                    color: rgba(0, 122, 255, 200);
                    font-size: 16px;
                    font-weight: bold;
                }}
            """)
        
        self.dot_index = (self.dot_index + 1) % (len(self.dots) + 1)
        
    def stop_animation(self):
        """Stop animation"""
        if self.animation_timer:
            self.animation_timer.stop()
        
    def start_animation(self):
        """Start animation"""
        if self.animation_timer and not self.animation_timer.isActive():
            self.animation_timer.start(600)

class EnhancedResponseDisplay(QTextBrowser):
    """Enhanced response display with better styling"""
    
    copyRequested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.full_text = ""
        self.current_index = 0
        self.typing_speed = 8
        self.is_typing = False
        
        self.min_height = 120
        self.max_height_ratio = 0.6
        
        self.setStyleSheet(self.get_enhanced_style())
        self.setOpenExternalLinks(True)
        
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        self.height_animation = QPropertyAnimation(self, b"maximumHeight")
        self.height_animation.setDuration(200)
        self.height_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def get_enhanced_style(self):
        """Enhanced styling with modern scrollbar"""
        return f"""
            QTextBrowser {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(25, 25, 25, 200),
                    stop: 0.5 rgba(20, 20, 20, 180),
                    stop: 1 rgba(15, 15, 15, 160));
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 16px;
                color: rgba(255, 255, 255, 255);
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                padding: 20px;
                line-height: 1.6;
                selection-background-color: rgba(0, 122, 255, 80);
            }}
            /* Modern scrollbar styling */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 100),
                    stop: 1 rgba(0, 122, 255, 120));
                border-radius: 4px;
                min-height: 20px;
                border: 1px solid rgba(0, 122, 255, 40);
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 140),
                    stop: 1 rgba(0, 122, 255, 160));
            }}
            QScrollBar::handle:vertical:pressed {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(0, 122, 255, 180),
                    stop: 1 rgba(0, 122, 255, 200));
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                height: 0px;
                background: transparent;
            }}
        """
        
    def show_context_menu(self, position):
        """Show context menu"""
        menu = QMenu(self)
        
        if self.textCursor().hasSelection():
            copy_action = menu.addAction("Copy Selected Text")
            copy_action.triggered.connect(lambda: self.copy_to_clipboard(self.textCursor().selectedText()))
        
        copy_all_action = menu.addAction("Copy All Content")
        copy_all_action.triggered.connect(lambda: self.copy_to_clipboard(self.toPlainText()))
        
        if menu.actions():
            menu.exec(self.mapToGlobal(position))
    
    def copy_to_clipboard(self, text):
        """Copy to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        print(f"📋 Copied: {len(text)} characters")
        
    def smart_height_adjustment(self):
        """Smart height adjustment"""
        doc = self.document()
        doc.setTextWidth(self.width() - 40)
        content_height = int(doc.size().height() + 40)
        
        screen_height = QApplication.primaryScreen().geometry().height()
        max_height = int(screen_height * self.max_height_ratio)
        new_height = max(self.min_height, min(content_height, max_height))
        
        if new_height != self.maximumHeight():
            self.height_animation.setStartValue(self.maximumHeight())
            self.height_animation.setEndValue(new_height)
            self.height_animation.start()
            self.setMinimumHeight(new_height)
        
        if content_height > max_height:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
    def typewrite_text(self, html_text):
        """Typewriter effect"""
        self.clear()
        self.full_text = html_text
        self.current_index = 0
        self.is_typing = True
        QTimer.singleShot(self.typing_speed, self.add_next_chunk)
        
    def add_next_chunk(self):
        """Add text chunks"""
        if not self.is_typing:
            return
            
        if self.current_index < len(self.full_text):
            chunk_size = 15
            end_index = min(self.current_index + chunk_size, len(self.full_text))
            partial_text = self.full_text[:end_index]
            self.setHtml(partial_text)
            self.current_index = end_index
            
            if self.current_index % 300 == 0:
                self.smart_height_adjustment()
            
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            
            QTimer.singleShot(self.typing_speed, self.add_next_chunk)
        else:
            self.is_typing = False
            self.smart_height_adjustment()
            
    def show_immediately(self, html_text):
        """Show text immediately"""
        self.setHtml(html_text)
        QTimer.singleShot(50, self.smart_height_adjustment)

class QuestionDisplay(QWidget):
    """Enhanced question display widget"""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        
        self.content_label = QLabel()
        self.content_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(0, 122, 255, 25),
                    stop: 1 rgba(0, 122, 255, 15));
                border: 1px solid rgba(0, 122, 255, 50);
                border-radius: 10px;
                color: rgba(255, 255, 255, 240);
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 10px 14px;
                line-height: 1.3;
            }}
        """)
        self.content_label.setWordWrap(True)
        content_layout.addWidget(self.content_label)
        
        layout.addWidget(self.content_widget, 1)
        
        self.header_label = QLabel("YOUR QUESTION")
        self.header_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(0, 122, 255, 180);
                font-size: 9px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                letter-spacing: 0.3px;
                padding: 3px 6px;
                background: rgba(0, 122, 255, 15);
                border-radius: 4px;
                border: 1px solid rgba(0, 122, 255, 30);
                min-width: 70px;
                max-width: 100px;
            }}
        """)
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label, 0)
        
        self.hide()
        
    def set_question(self, question, web_search_enabled=False, has_custom_instructions=False):
        """Set question with enhanced indicators"""
        if has_custom_instructions:
            header_text = "🎯 CUSTOM QUESTION"
            # Use orange for custom instructions
            self.content_label.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(255, 159, 10, 40),
                        stop: 1 rgba(255, 159, 10, 25));
                    border: 1px solid rgba(255, 159, 10, 80);
                    border-radius: 12px;
                    color: rgba(255, 255, 255, 255);
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    font-weight: 500;
                    padding: 12px 16px;
                    line-height: 1.4;
                }}
            """)
            self.header_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 159, 10, 255);
                    font-size: 10px;
                    font-weight: 700;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    letter-spacing: 0.5px;
                    padding: 4px 8px;
                    background: rgba(255, 159, 10, 20);
                    border-radius: 6px;
                    border: 1px solid rgba(255, 159, 10, 50);
                    min-width: 80px;
                    max-width: 120px;
                }}
            """)
        elif web_search_enabled:
            header_text = "🌐 WEB SEARCH"
        else:
            header_text = "YOUR QUESTION"
            # Reset to blue for normal questions
            self.content_label.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 rgba(0, 122, 255, 40),
                        stop: 1 rgba(0, 122, 255, 25));
                    border: 1px solid rgba(0, 122, 255, 80);
                    border-radius: 12px;
                    color: rgba(255, 255, 255, 255);
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    font-weight: 500;
                    padding: 12px 16px;
                    line-height: 1.4;
                }}
            """)
            self.header_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(0, 122, 255, 255);
                    font-size: 10px;
                    font-weight: 700;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    letter-spacing: 0.5px;
                    padding: 4px 8px;
                    background: rgba(0, 122, 255, 20);
                    border-radius: 6px;
                    border: 1px solid rgba(0, 122, 255, 50);
                    min-width: 80px;
                    max-width: 120px;
                }}
            """)
            
        self.header_label.setText(header_text)
        self.content_label.setText(question)
        self.show()
        
    def clear_question(self):
        """Clear question"""
        self.content_label.clear()
        self.hide()

class CompactInstructionBar(QWidget):
    """Fixed instruction bar with proper alignment"""
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: transparent;")
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI with better alignment"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        instructions = [
            ("Show", "Ctrl \\"),
            ("Ask", "Ctrl ↵"),
        ]
        
        for i, (label, shortcut) in enumerate(instructions):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(6, 3, 6, 3)
            item_layout.setSpacing(3)
            
            label_widget = QLabel(label)
            label_widget.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 255, 255, 200);
                    font-size: 10px;
                    font-weight: 500;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                }}
            """)
            item_layout.addWidget(label_widget)
            
            shortcut_widget = QLabel(shortcut)
            shortcut_widget.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 255, 255, 150);
                    font-size: 9px;
                    font-weight: 400;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    background: rgba(255, 255, 255, 8);
                    border-radius: 2px;
                    padding: 1px 3px;
                }}
            """)
            item_layout.addWidget(shortcut_widget)
            
            item_widget.setStyleSheet(f"""
                QWidget {{
                    background: rgba(20, 20, 20, 40);
                    border-radius: 5px;
                    border: 1px solid rgba(255, 255, 255, 12);
                }}
            """)
            
            layout.addWidget(item_widget)

class OptimizedDropdown(QComboBox):
    """Enhanced dropdown with sleeker styling"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(120)
        self.setMaximumWidth(180)
        self.setStyleSheet(self.get_optimized_style())
        
    def get_optimized_style(self):
        """Enhanced dropdown styling"""
        return f"""
            QComboBox {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(25, 25, 25, 200),
                    stop: 0.5 rgba(20, 20, 20, 180),
                    stop: 1 rgba(15, 15, 15, 160));
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                color: rgba(255, 255, 255, 255);
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 6px 10px;
            }}
            QComboBox:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(35, 35, 35, 220),
                    stop: 0.5 rgba(30, 30, 30, 200),
                    stop: 1 rgba(25, 25, 25, 180));
                border: 1px solid rgba(255, 255, 255, 60);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 16px;
                background: transparent;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
                width: 0;
                height: 0;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 5px solid rgba(255, 255, 255, 200);
                margin-right: 3px;
            }}
            QComboBox QAbstractItemView {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(25, 25, 25, 250),
                    stop: 1 rgba(15, 15, 15, 240));
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 8px;
                color: rgba(255, 255, 255, 255);
                selection-background-color: rgba(0, 122, 255, 80);
                outline: none;
                padding: 3px;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border: none;
                border-radius: 4px;
                margin: 1px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: rgba(0, 122, 255, 100);
                color: white;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: rgba(255, 255, 255, 20);
            }}
        """

class FixedAPIDialog(QDialog):
    """Enhanced API setup dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("API Setup")
        self.setFixedSize(420, 320)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Center the dialog
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            int(screen.height() * 0.15)
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_widget = FastBlurWidget()
        layout.addWidget(self.main_widget)
        
        content_layout = QVBoxLayout(self.main_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 25, 30, 25)
        
        header_layout = QHBoxLayout()
        
        title_section = QVBoxLayout()
        title_section.setSpacing(8)
        
        title_container = QHBoxLayout()
        title_container.addStretch()
        
        icon = QLabel("🔑")
        icon.setStyleSheet("font-size: 28px; color: rgba(0, 122, 255, 255);")
        title_container.addWidget(icon)
        
        title = QLabel("API Key")
        title.setStyleSheet(f"""
            color: rgba(255, 255, 255, 255);
            font-size: 20px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            margin-left: 10px;
        """)
        title_container.addWidget(title)
        title_container.addStretch()
        
        title_section.addLayout(title_container)
        
        subtitle = QLabel("Enter your OpenAI API key")
        subtitle.setStyleSheet(f"""
            color: rgba(255, 255, 255, 220);
            font-size: 14px;
            font-weight: 400;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_section.addWidget(subtitle)
        
        header_layout.addLayout(title_section)
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 69, 58, 200);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 69, 58, 255);
            }}
        """)
        close_btn.clicked.connect(self.reject)
        header_layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)
        
        content_layout.addLayout(header_layout)
        
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("sk-...")
        self.api_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_input.setMinimumHeight(40)
        self.api_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(40, 40, 40, 180);
                border: 2px solid rgba(255, 255, 255, 80);
                border-radius: 10px;
                color: rgba(255, 255, 255, 255);
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                padding: 12px 16px;
                selection-background-color: rgba(0, 122, 255, 80);
            }}
            QLineEdit:focus {{
                border: 2px solid rgba(0, 122, 255, 150);
                background: rgba(45, 45, 45, 200);
            }}
        """)
        content_layout.addWidget(self.api_input)
        
        self.show_key_checkbox = QCheckBox("Show key")
        self.show_key_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: rgba(255, 255, 255, 200);
                font-size: 12px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 3px;
                border: 1px solid rgba(255, 255, 255, 180);
                background: transparent;
            }}
            QCheckBox::indicator:checked {{
                background: rgba(0, 122, 255, 255);
                border: 1px solid rgba(0, 122, 255, 255);
            }}
        """)
        self.show_key_checkbox.toggled.connect(self.toggle_password_visibility)
        content_layout.addWidget(self.show_key_checkbox)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            color: rgba(255, 69, 58, 255);
            font-size: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            font-weight: 400;
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumHeight(36)
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 25);
                border: 1px solid rgba(255, 255, 255, 70);
                border-radius: 8px;
                color: rgba(255, 255, 255, 255);
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 35);
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Continue")
        self.save_btn.setMinimumHeight(36)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 122, 255, 255);
                border: 1px solid rgba(0, 122, 255, 255);
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: rgba(0, 122, 255, 230);
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

class FixedSettingsDialog(QDialog):
    """Enhanced settings dialog with custom instructions button"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_ui = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(380, 320)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Center the dialog
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            int(screen.height() * 0.15)
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.main_widget = FastBlurWidget()
        layout.addWidget(self.main_widget)
        
        content_layout = QVBoxLayout(self.main_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(25, 20, 25, 20)
        
        header_layout = QHBoxLayout()
        
        header = QLabel("⚙️ Settings")
        header.setStyleSheet(f"""
            color: rgba(255, 255, 255, 255);
            font-size: 18px;
            font-weight: 600;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        """)
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 69, 58, 200);
                border: none;
                border-radius: 11px;
                color: white;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255, 69, 58, 255);
            }}
        """)
        close_btn.clicked.connect(self.accept)
        header_layout.addWidget(close_btn)
        
        content_layout.addLayout(header_layout)
        
        button_style = f"""
            QPushButton {{
                background: rgba(20, 20, 20, 150);
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 8px;
                color: rgba(255, 255, 255, 255);
                font-size: 13px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 12px 15px;
                text-align: left;
                min-height: 18px;
            }}
            QPushButton:hover {{
                background: rgba(30, 30, 30, 180);
                border: 1px solid rgba(255, 255, 255, 80);
            }}
        """
        
        # Check custom instructions status for button text
        custom_status = ""
        if self.parent_ui and hasattr(self.parent_ui, 'session_id'):
            instructions = get_session_custom_instructions(self.parent_ui.session_id)
            if instructions:
                from database import get_session_history
                history = get_session_history(self.parent_ui.session_id, limit=1)
                is_locked = len(history) > 0
                if is_locked:
                    custom_status = " 🔒"
                else:
                    custom_status = " 🎯"
        
        buttons_data = [
            (f"🎯 Custom Instructions{custom_status}", self.show_custom_instructions),
            ("🔐 Change API Key", self.logout),
            ("🌐 Visit Website", self.open_website),
            ("ℹ️ About Wheel4", self.about)
        ]
        
        for text, callback in buttons_data:
            btn = QPushButton(text)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(callback)
            content_layout.addWidget(btn)
        
        content_layout.addStretch()
        
    def show_custom_instructions(self):
        """Show custom instructions dialog"""
        if self.parent_ui and hasattr(self.parent_ui, 'session_id'):
            dialog = SessionCustomInstructionsDialog(self.parent_ui, self.parent_ui.session_id)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                instructions = dialog.get_instructions()
                # Update parent UI
                if hasattr(self.parent_ui, 'current_custom_instructions'):
                    self.parent_ui.current_custom_instructions = instructions
                    self.parent_ui.load_session_custom_instructions()
                    
                # Update this dialog's button text
                self.setup_ui()  # Refresh the dialog
        
    def logout(self):
        self.accept()
        self.parent().reset_data()
        
    def open_website(self):
        import webbrowser
        webbrowser.open("https://thelearnchain.com")
        
    def about(self):
        QMessageBox.information(self, "About Wheel4", "Wheel4 AI Brain v2.0\n\nSleek AI assistant with screen awareness\nBy LearnChain\n\nFeatures:\n• Screen analysis\n• Custom instructions\n• Session management\n• Clean, glassy interface")

class AIBrainUI(QMainWindow):
    """Enhanced Main AI Brain UI with fixed hotkey handling"""
    
    stealth_mode_changed = pyqtSignal(bool)
    
    def __init__(self, session_id):
        super().__init__()
        self.session_id = session_id
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.current_response_data = None
        self.is_stealth_mode = False
        self.web_search_enabled = False
        self.ai_worker = None
        self.input_mode_active = False  # Track if input mode is active
        
        # Enhanced custom instructions state
        self.current_custom_instructions = ""
        self.instructions_locked = False
        
        self.setup_ui()
        self.check_api_key()
        self.load_session_custom_instructions()
        
    def setup_ui(self):
        """Enhanced UI setup with auto-centering"""
        # Window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Auto-detect screen and center properly
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # Smart UI sizing based on screen size
        if self.screen_width >= 2560:  # 4K screens
            self.ui_width = 800
        elif self.screen_width >= 1920:  # 1080p screens  
            self.ui_width = 650
        elif self.screen_width >= 1366:  # Laptop screens
            self.ui_width = 550
        else:  # Small screens
            self.ui_width = 500
            
        # Center horizontally, top positioned
        self.ui_left = (self.screen_width - self.ui_width) // 2
        
        self.setGeometry(self.ui_left, 20, self.ui_width, 70)  # 20px from top
        
        self.container = FastBlurWidget()
        self.setCentralWidget(self.container)
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(16, 10, 16, 10)
        self.main_layout.setSpacing(10)
        
        self.setup_top_bar()
        self.setup_question_input()
        self.setup_question_display()
        self.setup_response_area()
        
        self.resize_animation = QPropertyAnimation(self, b"geometry")
        self.resize_animation.setDuration(200)
        self.resize_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def setup_top_bar(self):
        """Enhanced top bar with proper logo positioning and alignment"""
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        
        # Left side - Logo and brand (leftmost)
        left_layout = QHBoxLayout()
        left_layout.setSpacing(8)
        
        # Wheel4 logo - try to load image first
        logo_label = QLabel()
        logo_loaded = False
        
        # Try multiple logo file formats
        for logo_path in ["wheel4_logo.png", "assets/wheel4_logo.png", "logo.png", "assets/logo.png", "wheel4.svg", "assets/wheel4.svg"]:
            if os.path.exists(logo_path):
                try:
                    if logo_path.endswith('.svg'):
                        # For SVG files (would need additional handling)
                        logo_label.setText("⚡")
                        logo_loaded = True
                        break
                    else:
                        # For PNG/JPG files
                        pixmap = QPixmap(logo_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                            logo_label.setPixmap(scaled_pixmap)
                            logo_loaded = True
                            break
                except Exception as e:
                    print(f"⚠️ Failed to load logo {logo_path}: {e}")
                    continue
        
        # Fallback to emoji if no image found
        if not logo_loaded:
            logo_label.setText("⚡")
            logo_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(0, 122, 255, 255);
                    font-size: 16px;
                    font-weight: 600;
                }}
            """)
        
        left_layout.addWidget(logo_label)
        
        # Wheel4 brand name
        brand_label = QLabel("Wheel4")
        brand_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 255);
                font-size: 14px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                letter-spacing: -0.3px;
            }}
        """)
        left_layout.addWidget(brand_label)
        
        # Fixed instruction bar - proper alignment
        self.compact_instruction_bar = CompactInstructionBar()
        left_layout.addWidget(self.compact_instruction_bar)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        left_widget.setStyleSheet("background: transparent;")
        top_bar.addWidget(left_widget)
        
        # Center - Status indicator
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 180);
                font-size: 11px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: rgba(255, 255, 255, 8);
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                padding: 3px 8px;
            }}
        """)
        top_bar.addWidget(self.status_label)
        
        # Right side - session and controls
        right_layout = QHBoxLayout()
        right_layout.setSpacing(8)
        
        self.session_dropdown = OptimizedDropdown()
        self.session_dropdown.currentTextChanged.connect(self.switch_session)
        self.update_session_dropdown()
        right_layout.addWidget(self.session_dropdown)
        
        self.setup_control_buttons(right_layout)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        right_widget.setStyleSheet("background: transparent;")
        top_bar.addWidget(right_widget)
        
        self.main_layout.addLayout(top_bar)
        
    def setup_control_buttons(self, layout):
        """Enhanced control buttons - moved custom instructions to settings"""
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)
        
        button_style = f"""
            QPushButton {{
                background: rgba(20, 20, 20, 150);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 6px;
                color: rgba(255, 255, 255, 255);
                font-size: 11px;
                font-weight: 500;
                padding: 5px 6px;
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
            }}
            QPushButton:hover {{
                background: rgba(30, 30, 30, 180);
                border: 1px solid rgba(255, 255, 255, 50);
            }}
        """
        
        new_session_btn = QPushButton("➕")
        new_session_btn.setStyleSheet(button_style)
        new_session_btn.clicked.connect(self.create_new_session)
        new_session_btn.setToolTip("New session")
        
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setStyleSheet(button_style)
        self.settings_btn.clicked.connect(self.show_settings)
        
        self.close_btn = QPushButton("×")
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 69, 58, 200);
                border: none;
                border-radius: 5px;
                color: white;
                font-size: 11px;
                font-weight: 600;
                min-width: 14px;
                max-width: 14px;
                min-height: 14px;
                max-height: 14px;
            }}
            QPushButton:hover {{
                background: rgba(255, 69, 58, 255);
            }}
        """)
        self.close_btn.clicked.connect(self.close_application)
        
        controls_layout.addWidget(new_session_btn)
        controls_layout.addWidget(self.settings_btn)
        controls_layout.addWidget(self.close_btn)
        
        layout.addLayout(controls_layout)
        
    def setup_question_input(self):
        """Enhanced question input"""
        self.input_container = QWidget()
        self.input_container.setStyleSheet("background: transparent;")
        input_layout = QVBoxLayout(self.input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        
        self.question_input = EnhancedTextEdit("Type your question or press Enter to analyze screen...")
        self.question_input.enterPressed.connect(self.process_question)
        self.question_input.webSearchToggled.connect(self.toggle_web_search)
        self.question_input.emptyEnterPressed.connect(self.handle_empty_enter)
        
        input_layout.addWidget(self.question_input)
        self.setup_quick_actions(input_layout)
        
        self.input_container.hide()
        self.main_layout.addWidget(self.input_container)
        
    def setup_question_display(self):
        """Setup question display"""
        self.question_display = QuestionDisplay()
        self.main_layout.addWidget(self.question_display)
        
    def setup_quick_actions(self, layout):
        """Setup quick actions"""
        self.quick_actions_container = QWidget()
        self.quick_actions_container.setStyleSheet("background: transparent;")
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setSpacing(8)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        quick_questions = [
            ("Explain", "Explain what I'm looking at"),
            ("How to", "How do I proceed with this?"),
            ("Issues", "What issues should I be aware of?"),
            ("Next", "What's my next step?")
        ]
        
        for label, question in quick_questions:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(40, 40, 40, 150);
                    border: 1px solid rgba(255, 255, 255, 50);
                    border-radius: 8px;
                    color: rgba(255, 255, 255, 240);
                    font-size: 11px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                    font-weight: 500;
                    padding: 6px 12px;
                    min-height: 16px;
                    min-width: 50px;
                }}
                QPushButton:hover {{
                    background: rgba(0, 122, 255, 100);
                    border: 1px solid rgba(0, 122, 255, 140);
                    color: rgba(255, 255, 255, 255);
                }}
            """)
            btn.clicked.connect(lambda checked, q=question: self.quick_question(q))
            actions_layout.addWidget(btn)
        
        actions_layout.insertStretch(0)
        actions_layout.addStretch()
        
        quick_actions_layout = QVBoxLayout(self.quick_actions_container)
        quick_actions_layout.setContentsMargins(0, 0, 0, 0)
        quick_actions_layout.addWidget(actions_widget)
        
        self.quick_actions_container.hide()
        layout.addWidget(self.quick_actions_container)
        
    def setup_response_area(self):
        """Setup response area"""
        self.response_container = QWidget()
        self.response_container.setStyleSheet("background: transparent;")
        response_layout = QVBoxLayout(self.response_container)
        response_layout.setContentsMargins(0, 0, 0, 0)
        response_layout.setSpacing(10)
        
        self.loading_widget = LoadingWidget()
        self.loading_widget.hide()
        response_layout.addWidget(self.loading_widget)
        
        self.response_area = EnhancedResponseDisplay()
        response_layout.addWidget(self.response_area)
        
        self.setup_suggestions_area(response_layout)
        
        self.response_container.hide()
        self.main_layout.addWidget(self.response_container)
        
    def setup_suggestions_area(self, layout):
        """Setup suggestions"""
        self.suggestions_container = QWidget()
        self.suggestions_container.setStyleSheet("background: transparent;")
        suggestions_layout = QVBoxLayout(self.suggestions_container)
        suggestions_layout.setContentsMargins(0, 0, 0, 0)
        suggestions_layout.setSpacing(6)
        
        suggestions_title = QLabel("Suggested Questions")
        suggestions_title.setStyleSheet(f"""
            color: rgba(255, 255, 255, 220);
            font-size: 11px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            font-weight: 600;
            letter-spacing: -0.1px;
            padding: 0 2px;
        """)
        suggestions_layout.addWidget(suggestions_title)
        
        self.suggestions_widget = QWidget()
        self.suggestions_widget.setStyleSheet("background: transparent;")
        self.suggestions_layout = QGridLayout(self.suggestions_widget)
        self.suggestions_layout.setContentsMargins(0, 0, 0, 0)
        self.suggestions_layout.setSpacing(6)
        
        suggestions_layout.addWidget(self.suggestions_widget)
        self.suggestions_container.hide()
        layout.addWidget(self.suggestions_container)
    
    def load_session_custom_instructions(self):
        """Enhanced custom instructions loading with lock check"""
        if self.session_id:
            instructions = get_session_custom_instructions(self.session_id)
            self.current_custom_instructions = instructions
            
            # Check if instructions should be locked
            from database import get_session_history
            history = get_session_history(self.session_id, limit=1)
            self.instructions_locked = len(history) > 0 and bool(instructions)
            
            # Enhanced status updates
            if instructions:
                if self.instructions_locked:
                    self.status_label.setText("🔒 Locked")
                else:
                    self.status_label.setText("🎯 Custom")
            else:
                self.status_label.setText("Ready")
    
    def update_custom_instructions(self, instructions):
        """Enhanced custom instructions update"""
        self.current_custom_instructions = instructions
        print(f"🎯 Updated custom instructions ({len(instructions)} chars)")
        
        # Update lock status
        if instructions and not self.instructions_locked:
            from database import get_session_history
            history = get_session_history(self.session_id, limit=1)
            self.instructions_locked = len(history) > 0
        
        # Enhanced status updates
        if instructions:
            if self.instructions_locked:
                self.status_label.setText("🔒 Locked")
            else:
                self.status_label.setText("🎯 Custom")
        else:
            self.status_label.setText("Ready")
    
    def toggle_web_search(self, enabled):
        """Toggle web search"""
        self.web_search_enabled = enabled
        print(f"🌐 Web search: {'Enabled' if enabled else 'Disabled'}")
        
    def handle_empty_enter(self):
        """Handle empty ctrl+enter - analyze screen automatically"""
        print("⚡ Empty enter - analyzing screen automatically")
        # Treat empty enter as screen analysis request
        self.process_question_internal("")
        
    def process_question(self):
        """Process question from input field"""
        question = self.question_input.toPlainText().strip()
        print(f"🤔 Processing question: '{question}'")
        self.process_question_internal(question)
        
    def process_question_internal(self, question):
        """Internal method to process questions (handles both typed and empty)"""
        print(f"🤔 Starting to process: '{question}' (Web search: {self.web_search_enabled})")
        if self.current_custom_instructions:
            print(f"🎯 Using custom instructions ({len(self.current_custom_instructions)} chars)")
            if self.instructions_locked:
                print(f"🔒 Instructions are locked")
        
        # Lock instructions after first use
        if self.current_custom_instructions and not self.instructions_locked:
            self.instructions_locked = True
            print(f"🔒 Locking custom instructions after first use")
        
        # Check if custom instructions are active
        has_custom_instructions = bool(self.current_custom_instructions)
        
        # For display purposes, show what we're doing
        display_question = question if question else "Analyzing screen..."
        self.question_display.set_question(display_question, self.web_search_enabled, has_custom_instructions)
        
        # Exit input mode
        self.input_mode_active = False
        self.question_input.set_input_mode(False)
        
        self.question_input.clear()
        self.input_container.hide()
        
        self.response_area.clear()
        self.response_area.hide()
        self.suggestions_container.hide()
        
        self.quick_actions_container.show()
        self.status_label.setText("Processing...")
        
        self.loading_widget.set_web_search_mode(self.web_search_enabled)
        self.loading_widget.start_animation()
        self.loading_widget.show()
        
        self.fast_resize(280)
        self.response_container.show()
        
        print("🚀 Starting enhanced AI worker thread...")
        self.start_ai_processing(question)
        
    def fast_resize(self, new_height):
        """Fast window resize with proper centering"""
        current_rect = self.geometry()
        # Maintain center position during resize
        new_left = (self.screen_width - self.ui_width) // 2
        new_rect = QRect(new_left, current_rect.y(), self.ui_width, new_height)
        
        self.resize_animation.setStartValue(current_rect)
        self.resize_animation.setEndValue(new_rect)
        self.resize_animation.start()

    def show_question_input(self):
        """Show question input with instant cursor focus - FIXED"""
        print("🎯 Showing question input with instant focus")
        
        if not self.isVisible():
            self.show()
        
        self.raise_()
        self.activateWindow()
        
        if hasattr(self, 'question_display'):
            self.question_display.clear_question()
        if hasattr(self, 'response_container'):
            self.response_container.hide()
        if hasattr(self, 'suggestions_container'):
            self.suggestions_container.hide()
        
        self.input_container.show()
        self.fast_resize(170)
        self.question_input.clear()
        
        # Enable input mode and focus (includes hotkey protection)
        self.question_input.ensure_focus_immediately()
        
        # Update status to show options
        self.status_label.setText("Type question or press Enter to analyze screen...")
        
    def start_ai_processing(self, question):
        """Enhanced AI processing with better error handling"""
        try:
            if self.ai_worker and self.ai_worker.isRunning():
                print("⚠️ Previous AI worker still running, waiting...")
                self.ai_worker.quit()
                self.ai_worker.wait(3000)  # Increased wait time
            
            self.ai_worker = AIWorkerThread(
                question, 
                self.session_id, 
                self.web_search_enabled,
                custom_instructions=self.current_custom_instructions
            )
            
            self.ai_worker.response_ready.connect(self.handle_ai_response)
            self.ai_worker.error_occurred.connect(self.handle_ai_error)
            self.ai_worker.screenshot_captured.connect(self.handle_screenshot_captured)
            self.ai_worker.status_update.connect(self.handle_status_update)
            
            self.ai_worker.start()
            print("✅ Enhanced AI worker thread started")
            
            # Fixed timeout - longer duration and better handling
            self.timeout_timer = QTimer()
            self.timeout_timer.setSingleShot(True)
            self.timeout_timer.timeout.connect(self.handle_ai_timeout)
            self.timeout_timer.start(60000)  # 60 seconds - much longer timeout
            
        except Exception as e:
            error_msg = f"Failed to start AI processing: {str(e)}"
            print(f"❌ {error_msg}")
            self.handle_ai_error(error_msg)
    
    def handle_screenshot_captured(self):
        """Handle screenshot capture"""
        print("📸 Screenshot captured successfully")
        self.status_label.setText("Analyzing...")
        
    def handle_status_update(self, status):
        """Handle status updates"""
        print(f"📊 Status update: {status}")
        self.status_label.setText(status)
        self.loading_widget.set_status(status)
        
    def handle_ai_timeout(self):
        """Enhanced timeout handling - only timeout if worker is actually stuck"""
        if self.ai_worker and self.ai_worker.isRunning():
            print("⏰ AI processing timed out after 60 seconds")
            self.ai_worker.quit()
            self.ai_worker.wait(2000)
            self.handle_ai_error("Request timed out. The AI service may be experiencing high load. Please try again.")
        else:
            print("⏰ Timeout triggered but worker already finished - ignoring")
    
    def handle_ai_response(self, data):
        """Enhanced AI response handling with timeout cleanup"""
        try:
            # Stop timeout timer immediately
            if hasattr(self, 'timeout_timer') and self.timeout_timer.isActive():
                self.timeout_timer.stop()
                print("✅ Stopped timeout timer - response received")
            
            response, question = data
            print(f"✅ Received AI response in main thread")
            
            self.loading_widget.stop_animation()
            self.loading_widget.hide()
            
            response_data = self.parse_json_response(response)
            print(f"📊 Parsed response data: {len(str(response_data))} chars")
            
            self.show_final_response(response_data, question)
            
        except Exception as e:
            error_msg = f"Error handling AI response: {str(e)}"
            print(f"❌ {error_msg}")
            self.handle_ai_error(error_msg)
    
    def handle_ai_error(self, error_message):
        """Enhanced error handling with timeout cleanup"""
        print(f"❌ AI Error: {error_message}")
        
        # Stop timeout timer
        if hasattr(self, 'timeout_timer') and self.timeout_timer.isActive():
            self.timeout_timer.stop()
            print("🛑 Stopped timeout timer due to error")
        
        self.loading_widget.stop_animation()
        self.loading_widget.hide()
        
        self.show_error(error_message)
        
        if self.ai_worker:
            self.ai_worker.quit()
            self.ai_worker = None
        
    def parse_json_response(self, response_text):
        """Enhanced JSON response parsing"""
        try:
            response_data = extract_json_from_response(response_text)
            if response_data and isinstance(response_data, dict):
                required_fields = ["response", "code_blocks", "links", "suggested_questions"]
                for field in required_fields:
                    if field not in response_data:
                        if field == "response":
                            response_data[field] = str(response_text)[:1000]
                        else:
                            response_data[field] = []
                return response_data
        except Exception as e:
            print(f"❌ JSON parsing error: {e}")
        
        # Enhanced fallback
        return {
            "response": str(response_text)[:1000] if response_text else "Response received successfully.",
            "code_blocks": [],
            "links": [],
            "suggested_questions": [
                "How do I proceed with this?",
                "Can you explain this in more detail?", 
                "What are the key things to understand?",
                "How can I apply this knowledge?",
                "What should I be careful about?",
                "Are there better approaches?"
            ]
        }
        
    def format_response_with_code_blocks(self, response_data):
        """Enhanced response formatting"""
        try:
            html_parts = []
            
            # Main response
            response_text = response_data.get('response', 'Response received successfully.')
            if response_text:
                # Safe HTML processing
                response_text = html.escape(response_text)
                response_text = re.sub(r'\*\*(.*?)\*\*', r'<strong style="color: rgba(0, 122, 255, 255); font-weight: 600;">\1</strong>', response_text)
                response_text = re.sub(r'\*(.*?)\*', r'<em style="color: rgba(255, 255, 255, 255); font-style: italic;">\1</em>', response_text)
                response_text = re.sub(r'`(.*?)`', r'<code style="background: rgba(0, 122, 255, 15); color: rgba(0, 122, 255, 255); padding: 2px 6px; border-radius: 4px; font-family: SF Mono, Monaco, Consolas, monospace; font-size: 13px;">\1</code>', response_text)
                
                response_text = response_text.replace('\n\n', '</p><p style="margin: 12px 0 0 0;">')
                response_text = response_text.replace('\n', '<br>')
                
                html_parts.append(f'<p style="margin: 0; color: rgba(255, 255, 255, 255); line-height: 1.6;">{response_text}</p>')
            
            # Code blocks with unified background like Cluely
            code_blocks = response_data.get('code_blocks', [])
            for i, code_block in enumerate(code_blocks):
                if isinstance(code_block, dict):
                    language = html.escape(str(code_block.get('language', 'text')))
                    code = html.escape(str(code_block.get('code', '')))
                    description = html.escape(str(code_block.get('description', '')))
                    
                    # Unified code block like Cluely - single background, no line strips
                    code_html = f"""
                    <div style="margin: 16px 0; border-radius: 8px; overflow: hidden; background: rgba(10, 10, 10, 90); border: 1px solid rgba(255, 255, 255, 8);">
                        <div style="background: rgba(0, 122, 255, 15); padding: 6px 12px; border-bottom: 1px solid rgba(255, 255, 255, 8);">
                            <span style="color: rgba(0, 122, 255, 255); font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">{language}</span>
                        </div>
                        <div style="padding: 16px; background: rgba(15, 15, 15, 95);">
                            <pre style="margin: 0; color: rgba(255, 255, 255, 240); font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace; font-size: 13px; line-height: 1.5; white-space: pre-wrap; background: transparent;"><code>{code}</code></pre>
                        </div>
                        {f'<div style="padding: 8px 12px; border-top: 1px solid rgba(255, 255, 255, 8); color: rgba(255, 255, 255, 180); font-size: 11px; background: rgba(8, 8, 8, 80); font-style: italic;">{description}</div>' if description else ''}
                    </div>
                    """
                    html_parts.append(code_html)
            
            # Links
            links = response_data.get('links', [])
            if links:
                html_parts.append('<div style="margin: 16px 0;">')
                html_parts.append('<div style="color: rgba(0, 122, 255, 255); font-size: 11px; font-weight: 600; margin-bottom: 8px; letter-spacing: 0.5px;">🔗 USEFUL LINKS</div>')
                
                for link in links:
                    if isinstance(link, dict) and "url" in link:
                        url = html.escape(str(link.get('url', '')))
                        title = html.escape(str(link.get('title', 'Link')))
                        description = html.escape(str(link.get('description', '')))
                        
                        link_html = f"""
                        <div style="border-radius: 6px; padding: 10px; margin: 6px 0; border-left: 2px solid rgba(0, 122, 255, 100); background: rgba(0, 122, 255, 20);">
                            <a href="{url}" style="color: rgba(0, 122, 255, 255); text-decoration: underline; font-weight: 500; font-size: 13px;">{title}</a>
                            {f'<div style="color: rgba(255, 255, 255, 200); font-size: 11px; margin-top: 4px;">{description}</div>' if description else ''}
                        </div>
                        """
                        html_parts.append(link_html)
                
                html_parts.append('</div>')
            
            return ''.join(html_parts) if html_parts else '<p style="margin: 0; color: rgba(255, 255, 255, 255);">Response received successfully.</p>'
            
        except Exception as e:
            print(f"❌ HTML formatting error: {e}")
            # Enhanced fallback
            safe_text = html.escape(str(response_data.get('response', 'Response received successfully.')))
            return f'<p style="margin: 0; color: rgba(255, 255, 255, 255);">{safe_text}</p>'
        
    def show_final_response(self, response_data, question):
        """Enhanced final response display"""
        try:
            self.loading_widget.stop_animation()
            self.loading_widget.hide()
            
            self.response_area.show()
            
            formatted_response = self.format_response_with_code_blocks(response_data)
            
            # Enhanced header based on custom instructions
            if self.current_custom_instructions:
                if self.instructions_locked:
                    header_text = "🔒 LOCKED AI RESPONSE"
                else:
                    header_text = "🎯 CUSTOM AI RESPONSE"
            else:
                header_text = "✨ AI RESPONSE"
            
            full_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; line-height: 1.6;">
                <div style="padding: 20px; background: rgba(25, 25, 25, 120); border-radius: 12px; border-left: 3px solid rgba(0, 122, 255, 120);">
                    <div style="color: rgba(0, 122, 255, 255); font-weight: 700; font-size: 11px; margin-bottom: 12px; letter-spacing: 0.8px; text-align: left;">{header_text}</div>
                    <div style="color: rgba(255, 255, 255, 255); font-size: 14px;">
                        {formatted_response}
                    </div>
                </div>
            </div>
            """
            
            self.response_area.typewrite_text(full_html)
            
            # Enhanced status based on custom instructions
            if self.current_custom_instructions:
                if self.instructions_locked:
                    self.status_label.setText("🔒 Done")
                else:
                    self.status_label.setText("🎯 Done")
            else:
                self.status_label.setText("Done")
            
            suggested_questions = response_data.get('suggested_questions', [])
            if suggested_questions:
                self.show_suggested_questions(suggested_questions)
            
            # Save interaction
            try:
                save_interaction(self.session_id, question, response_data.get('response', ''))
            except Exception as e:
                print(f"⚠️ Error saving interaction: {e}")
                
        except Exception as e:
            print(f"❌ Error showing final response: {e}")
            self.show_error("Response received but display failed. Please try again.")
        
    def show_suggested_questions(self, questions):
        """Enhanced suggested questions display"""
        try:
            # Clear existing
            for i in reversed(range(self.suggestions_layout.count())):
                item = self.suggestions_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
                    
            for i, question in enumerate(questions[:6]):
                btn = QPushButton(str(question)[:80] + "..." if len(str(question)) > 80 else str(question))
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(40, 40, 40, 120);
                        border: 1px solid rgba(255, 255, 255, 40);
                        border-radius: 8px;
                        color: rgba(255, 255, 255, 220);
                        font-size: 11px;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                        font-weight: 500;
                        padding: 8px 12px;
                        text-align: left;
                        min-height: 16px;
                    }}
                    QPushButton:hover {{
                        background: rgba(0, 122, 255, 100);
                        border: 1px solid rgba(0, 122, 255, 140);
                        color: rgba(255, 255, 255, 255);
                    }}
                """)
                btn.clicked.connect(lambda checked, q=str(question): self.ask_suggested_question(q))
                self.suggestions_layout.addWidget(btn, i // 2, i % 2)
                
            self.suggestions_container.show()
            
        except Exception as e:
            print(f"⚠️ Error showing suggested questions: {e}")
        
    def ask_suggested_question(self, question):
        """Ask suggested question"""
        try:
            self.question_input.setPlainText(question)
            self.process_question()
        except Exception as e:
            print(f"⚠️ Error asking suggested question: {e}")
        
    def show_error(self, error):
        """Enhanced error display"""
        try:
            self.loading_widget.stop_animation()
            self.loading_widget.hide()
            
            self.response_area.show()
            
            self.status_label.setText("Error")
            self.fast_resize(180)
            
            safe_error = html.escape(str(error)[:300])  # Increased error length
            error_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;">
                <div style="padding: 20px; background: rgba(60, 20, 20, 120); border-radius: 12px; border-left: 3px solid rgba(255, 69, 58, 180);">
                    <div style="color: rgba(255, 69, 58, 255); font-weight: 700; font-size: 11px; margin-bottom: 8px; letter-spacing: 0.8px;">⚠️ ERROR</div>
                    <div style="color: rgba(255, 255, 255, 255); font-size: 14px; line-height: 1.5;">{safe_error}</div>
                    <div style="color: rgba(255, 255, 255, 180); font-size: 12px; margin-top: 8px;">Try rephrasing your question or check your internet connection.</div>
                </div>
            </div>
            """
            self.response_area.setHtml(error_html)
            self.response_container.show()
            QTimer.singleShot(5000, lambda: self.status_label.setText("Ready"))
            
        except Exception as e:
            print(f"❌ Error showing error: {e}")
        
    def update_session_dropdown(self):
        """Enhanced session dropdown with custom instructions indicators"""
        try:
            self.session_dropdown.clear()
            sessions = get_all_sessions()
            for session_id, name, created_at, total_tokens, is_active, custom_instructions in sessions:
                display_name = f"Session {session_id}"
                if session_id == self.session_id:
                    display_name += " (Current)"
                if custom_instructions:
                    # Check if locked
                    from database import get_session_history
                    history = get_session_history(session_id, limit=1)
                    is_locked = len(history) > 0
                    if is_locked:
                        display_name += " 🔒"
                    else:
                        display_name += " 🎯"
                self.session_dropdown.addItem(display_name, session_id)
            for i in range(self.session_dropdown.count()):
                if self.session_dropdown.itemData(i) == self.session_id:
                    self.session_dropdown.setCurrentIndex(i)
                    break
        except Exception as e:
            print(f"⚠️ Error updating session dropdown: {e}")
                
    def switch_session(self, text):
        """Enhanced session switching"""
        try:
            if not text or "(Current)" in text:
                return
            session_id = self.session_dropdown.currentData()
            if session_id and session_id != self.session_id:
                self.session_id = session_id
                switch_to_session(session_id)
                self.load_session_custom_instructions()
                self.update_session_dropdown()
        except Exception as e:
            print(f"⚠️ Error switching session: {e}")
            
    def create_new_session(self):
        """Enhanced new session creation"""
        try:
            new_session_id = create_new_session()
            self.session_id = new_session_id
            self.current_custom_instructions = ""
            self.instructions_locked = False
            if hasattr(self, 'custom_instructions_btn'):
                self.custom_instructions_btn.update_session(new_session_id)
            self.update_session_dropdown()
            self.status_label.setText("AI Brain")
        except Exception as e:
            print(f"⚠️ Error creating new session: {e}")
        
    def set_stealth_mode(self, enabled):
        """Set stealth mode"""
        self.is_stealth_mode = enabled
        if enabled:
            self.hide()
        else:
            self.show()
        self.stealth_mode_changed.emit(enabled)
        
    def check_api_key(self):
        """Enhanced API key checking"""
        try:
            api_key = get_api_key()
            if not api_key:
                QTimer.singleShot(100, self.show_api_key_setup)
            else:
                # Enhanced status based on custom instructions
                if self.current_custom_instructions:
                    if self.instructions_locked:
                        self.status_label.setText("🔒 Locked AI")
                    else:
                        self.status_label.setText("🎯 Custom AI")
                else:
                    self.status_label.setText("AI Brain")
        except Exception as e:
            print(f"⚠️ Error checking API key: {e}")
            
    def show_api_key_setup(self):
        """Show API key setup"""
        try:
            dialog = FixedAPIDialog(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                save_api_key(dialog.api_key)
                # Enhanced status based on custom instructions
                if self.current_custom_instructions:
                    if self.instructions_locked:
                        self.status_label.setText("🔒 Locked AI")
                    else:
                        self.status_label.setText("🎯 Custom AI")
                else:
                    self.status_label.setText("AI Brain")
            else:
                self.close_application()
        except Exception as e:
            print(f"⚠️ Error showing API key setup: {e}")
            
    def show_settings(self):
        """Show settings"""
        try:
            dialog = FixedSettingsDialog(self)
            dialog.exec()
        except Exception as e:
            print(f"⚠️ Error showing settings: {e}")
        
    def reset_data(self):
        """Reset data"""
        try:
            save_api_key("")
            self.show_api_key_setup()
        except Exception as e:
            print(f"⚠️ Error resetting data: {e}")
        
    def toggle_visibility(self):
        """Toggle visibility"""
        try:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
        except Exception as e:
            print(f"⚠️ Error toggling visibility: {e}")
            
    def quick_question(self, question):
        """Quick question"""
        try:
            self.question_input.setPlainText(question)
            self.process_question()
        except Exception as e:
            print(f"⚠️ Error with quick question: {e}")
        
    def close_application(self):
        """Enhanced application closing"""
        try:
            print("🛑 Closing application...")
            
            if self.ai_worker and self.ai_worker.isRunning():
                print("🛑 Stopping AI worker...")
                self.ai_worker.quit()
                self.ai_worker.wait(3000)  # Increased wait time
            
            if hasattr(self, 'loading_widget'):
                self.loading_widget.stop_animation()
                
            QApplication.instance().quit()
        except Exception as e:
            print(f"⚠️ Error closing application: {e}")
        
    def closeEvent(self, event):
        """Close event"""
        self.close_application()
        event.accept()