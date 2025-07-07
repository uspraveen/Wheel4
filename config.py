#!/usr/bin/env python3
"""
Wheel4 - Configuration
Enhanced app configuration with liquid glass settings
"""

# Application info
APP_NAME = "Wheel4 AI Brain"
APP_VERSION = "2.0"
APP_DESCRIPTION = "Intelligent on-screen AI assistant with liquid glass interface"

# Hotkeys (can be modified here)
TOGGLE_HOTKEY = "<ctrl>+\\"
QUESTION_HOTKEY = "<ctrl>+<enter>"

# UI Settings - Liquid Glass Theme
WINDOW_HEIGHT_NORMAL = 80       # Normal height (just status bar)
WINDOW_HEIGHT_INPUT = 280       # Height when showing input
WINDOW_HEIGHT_RESPONSE = 450    # Height when showing response

# UI Margins and Positioning
UI_MARGIN_HORIZONTAL = 200      # Margins on left/right sides
UI_MAX_WIDTH = 1200            # Maximum UI width
UI_MIN_WIDTH = 800             # Minimum UI width

# Liquid Glass Visual Effects
GLASS_BLUR_RADIUS = 25         # Backdrop blur radius
GLASS_OPACITY = 0.75           # Base glass opacity
GLASS_BORDER_OPACITY = 0.12    # Border opacity
GLASS_HIGHLIGHT_OPACITY = 0.08 # Highlight opacity

# Color Scheme - Silvery Gray (UI) + Blue (AI highlights)
COLOR_SILVER_PRIMARY = "#8B8B8B"
COLOR_SILVER_LIGHT = "#A5A5A5"
COLOR_SILVER_DARK = "#6B6B6B"
COLOR_SILVER_ACCENT = "#B8B8B8"
COLOR_BLUE_HIGHLIGHT = "#4A90E2"
COLOR_BLUE_ACCENT = "#5BA0F2"

# Auto-hide settings
AUTO_HIDE_DELAY = 15000        # ms (15 seconds)
AUTO_MINIMIZE_DELAY = 5000     # ms (5 seconds)

# Database settings
DATABASE_FILE = "ai_brain.db"
PROMPTS_FILE = "prompts.md"

# Session Management
MAX_SESSIONS = 50              # Maximum sessions to keep
SESSION_CLEANUP_DAYS = 7       # Days before session cleanup
SESSION_ARCHIVE_DAYS = 30      # Days before session archival

# Performance Settings
SCREENSHOT_CACHE_SIZE = 5      # Number of screenshots to cache
SCREENSHOT_CACHE_TTL = 3.0     # Cache time-to-live in seconds
SCREENSHOT_MAX_SIZE = 2048     # Maximum screenshot dimension
SCREENSHOT_QUALITY = 85        # JPEG quality for compression

# AI Settings
MAX_CONTEXT_TOKENS = 8000      # Maximum tokens for context
MAX_TOTAL_TOKENS = 32000       # Maximum total tokens per request
DEFAULT_RESPONSE_TOKENS = 2000 # Default max response tokens
TOKEN_BUFFER = 1000            # Token buffer for safety

# Stealth Mode
STEALTH_DELAY = 100            # ms delay before stealth screenshot
STEALTH_FADE_DURATION = 200    # ms fade duration for stealth mode

# Typewriter Effect
TYPEWRITER_SPEED = 15          # ms between characters
TYPEWRITER_CHUNK_SIZE = 3      # Characters per chunk
TYPEWRITER_ENABLED = True      # Enable typewriter effect

# Cache Settings
CACHE_CLEANUP_INTERVAL = 30    # seconds
CACHE_MAX_AGE = 600           # seconds (10 minutes)
CACHE_MAX_SIZE = 50           # MB

# Performance Monitoring
PERFORMANCE_MONITORING = True  # Enable performance monitoring
BENCHMARK_ON_STARTUP = True   # Run benchmark on startup
MEMORY_MONITORING = True      # Monitor memory usage

# Animation Settings
ANIMATION_DURATION = 300       # ms
ANIMATION_EASING = "ease-out"  # CSS easing function
SMOOTH_SCROLLING = True       # Enable smooth scrolling

# Debug settings
DEBUG_LOGS = True
DEBUG_PERFORMANCE = True
DEBUG_SCREENSHOTS = False
DEBUG_DATABASE = False
DEBUG_TOKENS = True

# Window behavior
WINDOW_STAY_ON_TOP = True
WINDOW_FRAMELESS = True
WINDOW_TRANSPARENT = True
WINDOW_MINIMIZE_TO_TRAY = False

# Suggestions
MAX_SUGGESTIONS = 6            # Maximum suggested questions
SUGGESTION_GRID_COLUMNS = 3    # Grid layout columns
SUGGESTION_TRUNCATE_LENGTH = 60 # Characters before truncation

# Quick Actions
QUICK_ACTION_GRID_COLUMNS = 4  # Grid layout columns
QUICK_ACTION_MAX_COUNT = 8     # Maximum quick actions

# Error Handling
ERROR_DISPLAY_DURATION = 5000  # ms to show errors
ERROR_FADE_DURATION = 1000     # ms fade duration
ERROR_MAX_LENGTH = 200         # Characters before truncation

# Network Settings
REQUEST_TIMEOUT = 30           # seconds
MAX_RETRIES = 3               # Maximum API retries
RETRY_DELAY = 1.0             # seconds between retries

# File Settings
MAX_FILE_SIZE = 10             # MB
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
BACKUP_INTERVAL = 86400        # seconds (24 hours)

# Accessibility
HIGH_CONTRAST_MODE = False     # Enable high contrast mode
LARGE_TEXT_MODE = False        # Enable large text mode
KEYBOARD_NAVIGATION = True     # Enable keyboard navigation
SCREEN_READER_SUPPORT = True   # Enable screen reader support

# Security
SECURE_API_KEY_STORAGE = True  # Use secure storage for API keys
ENCRYPT_SESSION_DATA = False   # Encrypt session data (future feature)
AUTOMATIC_LOGOUT = False       # Automatic logout after inactivity

# Experimental Features
EXPERIMENTAL_FEATURES = False  # Enable experimental features
BETA_FEATURES = False         # Enable beta features
ADVANCED_CONTEXT = True       # Enable advanced context management

def log(message, level="INFO"):
    """Enhanced logging function with levels"""
    if DEBUG_LOGS:
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

def get_ui_dimensions():
    """Get UI dimensions based on screen size"""
    from PyQt6.QtWidgets import QApplication
    
    if QApplication.instance():
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        
        # Calculate UI width with margins
        ui_width = min(UI_MAX_WIDTH, max(UI_MIN_WIDTH, screen_width - (UI_MARGIN_HORIZONTAL * 2)))
        ui_left = (screen_width - ui_width) // 2
        
        return {
            'width': ui_width,
            'left': ui_left,
            'margin': UI_MARGIN_HORIZONTAL
        }
    
    return {
        'width': UI_MAX_WIDTH,
        'left': UI_MARGIN_HORIZONTAL,
        'margin': UI_MARGIN_HORIZONTAL
    }

def get_performance_config():
    """Get performance configuration"""
    return {
        'screenshot_cache_size': SCREENSHOT_CACHE_SIZE,
        'screenshot_cache_ttl': SCREENSHOT_CACHE_TTL,
        'screenshot_max_size': SCREENSHOT_MAX_SIZE,
        'screenshot_quality': SCREENSHOT_QUALITY,
        'typewriter_speed': TYPEWRITER_SPEED,
        'animation_duration': ANIMATION_DURATION,
        'cache_cleanup_interval': CACHE_CLEANUP_INTERVAL,
        'cache_max_age': CACHE_MAX_AGE
    }

def get_ai_config():
    """Get AI configuration"""
    return {
        'max_context_tokens': MAX_CONTEXT_TOKENS,
        'max_total_tokens': MAX_TOTAL_TOKENS,
        'default_response_tokens': DEFAULT_RESPONSE_TOKENS,
        'token_buffer': TOKEN_BUFFER,
        'request_timeout': REQUEST_TIMEOUT,
        'max_retries': MAX_RETRIES,
        'retry_delay': RETRY_DELAY
    }

def get_ui_config():
    """Get UI configuration"""
    return {
        'colors': {
            'primary': COLOR_SILVER_PRIMARY,
            'light': COLOR_SILVER_LIGHT,
            'dark': COLOR_SILVER_DARK,
            'accent': COLOR_SILVER_ACCENT,
            'blue_highlight': COLOR_BLUE_HIGHLIGHT,
            'blue_accent': COLOR_BLUE_ACCENT
        },
        'glass': {
            'blur_radius': GLASS_BLUR_RADIUS,
            'opacity': GLASS_OPACITY,
            'border_opacity': GLASS_BORDER_OPACITY,
            'highlight_opacity': GLASS_HIGHLIGHT_OPACITY
        },
        'animations': {
            'duration': ANIMATION_DURATION,
            'easing': ANIMATION_EASING,
            'typewriter_speed': TYPEWRITER_SPEED,
            'smooth_scrolling': SMOOTH_SCROLLING
        },
        'dimensions': get_ui_dimensions()
    }

def validate_config():
    """Validate configuration values"""
    errors = []
    
    # Validate token limits
    if MAX_CONTEXT_TOKENS >= MAX_TOTAL_TOKENS:
        errors.append("MAX_CONTEXT_TOKENS must be less than MAX_TOTAL_TOKENS")
    
    # Validate UI dimensions
    if UI_MIN_WIDTH > UI_MAX_WIDTH:
        errors.append("UI_MIN_WIDTH must be less than UI_MAX_WIDTH")
    
    # Validate cache settings
    if SCREENSHOT_CACHE_TTL <= 0:
        errors.append("SCREENSHOT_CACHE_TTL must be positive")
    
    # Validate timeouts
    if REQUEST_TIMEOUT <= 0:
        errors.append("REQUEST_TIMEOUT must be positive")
    
    if errors:
        print("❌ Configuration validation errors:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    return True

def apply_debug_config():
    """Apply debug configuration"""
    if DEBUG_PERFORMANCE:
        log("Performance debugging enabled", "DEBUG")
    
    if DEBUG_SCREENSHOTS:
        log("Screenshot debugging enabled", "DEBUG")
    
    if DEBUG_DATABASE:
        log("Database debugging enabled", "DEBUG")
    
    if DEBUG_TOKENS:
        log("Token debugging enabled", "DEBUG")

# Initialize configuration
if __name__ == "__main__":
    print(f"🔧 {APP_NAME} v{APP_VERSION} Configuration")
    print(f"📝 {APP_DESCRIPTION}")
    
    if validate_config():
        print("✅ Configuration valid")
        apply_debug_config()
        
        # Print key settings
        ui_config = get_ui_config()
        print(f"🎨 UI Width: {ui_config['dimensions']['width']}px")
        print(f"⚡ Performance monitoring: {'Enabled' if PERFORMANCE_MONITORING else 'Disabled'}")
        print(f"🔍 Debug logging: {'Enabled' if DEBUG_LOGS else 'Disabled'}")
        print(f"✨ Typewriter effect: {'Enabled' if TYPEWRITER_ENABLED else 'Disabled'}")
    else:
        print("❌ Configuration validation failed")