#!/usr/bin/env python3
"""
Wheel4 - Settings Dialog
Clean settings with neon blue theme
"""

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Import theme colors from ui.py
NEON_BLUE = "#00D4FF"
NEON_BLUE_LIGHT = "#5CE1FF"
NEON_BLUE_DARK = "#0099CC"
GLASS_BG = "rgba(20, 25, 40, 0.85)"
GLASS_BORDER = "rgba(0, 212, 255, 0.15)"

class SettingsDialog(QDialog):
    """Clean settings dialog with liquid glass effect"""
    
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
        
        # Main container with glass effect
        main_widget = QWidget()
        main_widget.setStyleSheet(f"""
            QWidget {{
                background: {GLASS_BG};
                border-radius: 16px;
                border: 1px solid {GLASS_BORDER};
            }}
        """)
        layout.addWidget(main_widget)
        
        # Content layout
        content_layout = QVBoxLayout(main_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("⚙️ Settings")
        header.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 24px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                background: transparent;
                border: none;
            }}
        """)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(header)
        
        # Settings buttons with glass effect
        button_style = f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.04);
                border: 2px solid {GLASS_BORDER};
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
                background: rgba(0, 212, 255, 0.08);
                border: 2px solid rgba(0, 212, 255, 0.3);
                color: white;
                filter: drop-shadow(0 0 5px rgba(0, 212, 255, 0.3));
            }}
            QPushButton:pressed {{
                background: rgba(0, 212, 255, 0.04);
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
                background: {NEON_BLUE};
                border: 2px solid {NEON_BLUE};
                border-radius: 10px;
                color: white;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                padding: 12px 20px;
            }}
            QPushButton:hover {{
                background: {NEON_BLUE_LIGHT};
                border: 2px solid {NEON_BLUE_LIGHT};
                box-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
                filter: drop-shadow(0 0 10px {NEON_BLUE});
            }}
            QPushButton:pressed {{
                background: {NEON_BLUE_DARK};
                border: 2px solid {NEON_BLUE_DARK};
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

    def reset_data(self):
        """Reset all data"""
        from database import save_api_key
        save_api_key("")
        self.parent().show_api_key_setup()
