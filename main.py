#!/usr/bin/env python3
"""
Wheel4 - Enhanced Main Entry Point
Fixed hotkey handling to prevent conflicts with input processing
"""

import sys
import signal
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread, Qt

from ui import AIBrainUI
from database import initialize_database, get_current_session, close_session
from hotkeys import HotkeyManager
from screen_capture import get_screen_info, get_optimal_settings_for_tokens

class FastHotkeyBridge(QObject):
    """Fixed hotkey bridge that separates toggle and question actions"""
    toggle_requested = pyqtSignal()
    show_input_requested = pyqtSignal()  # Changed from question_requested

class OptimizedSessionManager(QObject):
    """Lightweight session manager"""
    
    def __init__(self):
        super().__init__()
        self.current_session_id = None
        
    def start_session(self):
        """Fast session start"""
        self.current_session_id = get_current_session()
        print(f"📝 Session {self.current_session_id} active")
        return self.current_session_id
        
    def end_session(self):
        """End current session"""
        if self.current_session_id:
            close_session(self.current_session_id)

class ScreenOptimizer(QThread):
    """Background screen optimization and info gathering"""
    
    def run(self):
        """Run screen optimization in background"""
        try:
            # Get screen info and optimal settings
            screen_info = get_screen_info()
            optimal_settings = get_optimal_settings_for_tokens()
            
            print(f"📐 Screen: {screen_info['width']}x{screen_info['height']}")
            print(f"⚡ {optimal_settings['description']}")
            print(f"🎯 Estimated tokens: {optimal_settings['estimated_tokens']}")
            
            # Test screenshot capability
            from screen_capture import smart_capture
            test_screenshot = smart_capture()
            if test_screenshot:
                size_kb = len(test_screenshot) / 1024
                print(f"✅ Screenshot system ready ({size_kb:.1f}KB test)")
            else:
                print("⚠️  Screenshot system may have issues")
                
        except Exception as e:
            print(f"⚠️  Screen optimization error: {e}")

def setup_fast_application():
    """Setup application with performance optimizations"""
    print("🚀 Starting Wheel4 AI Brain v2.0...")
    
    # Create Qt application with optimizations
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # Set application properties
    app.setApplicationName("Wheel4 AI Brain")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Wheel4")
    
    # High DPI scaling is enabled by default in PyQt6
    # No need to set AA_EnableHighDpiScaling (removed in PyQt6)
    
    return app

def fast_database_setup():
    """Fast database initialization"""
    print("🗃️  Initializing database...")
    
    try:
        initialize_database()
        print("✅ Database ready")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

def main():
    """Enhanced main entry point with fixed hotkey handling"""
    start_total = time.time()
    
    try:
        # Fast application setup
        app = setup_fast_application()
        
        # Fast database setup
        if not fast_database_setup():
            print("❌ Database initialization failed")
            return 1
        
        # Session management
        session_manager = OptimizedSessionManager()
        session_id = session_manager.start_session()
        
        # Create main UI with error handling
        try:
            ui = AIBrainUI(session_id)
        except Exception as e:
            print(f"❌ UI initialization failed: {e}")
            return 1
        
        # Setup hotkey bridge with FIXED handling
        hotkey_bridge = FastHotkeyBridge()
        
        # Connect bridge signals - FIXED
        hotkey_bridge.toggle_requested.connect(ui.toggle_visibility)
        hotkey_bridge.show_input_requested.connect(ui.show_question_input)  # Fixed connection
        
        # Setup hotkeys with FIXED handlers
        def safe_toggle():
            """Safe toggle with error handling"""
            try:
                print("🔄 Toggle visibility")
                hotkey_bridge.toggle_requested.emit()
            except Exception as e:
                print(f"⚠️  Toggle error: {e}")
        
        def safe_show_input():
            """FIXED: Show input box only - no immediate processing"""
            try:
                print("❓ Show input box")
                hotkey_bridge.show_input_requested.emit()  # Just show input, don't process
            except Exception as e:
                print(f"⚠️  Show input error: {e}")
        
        # Create hotkey manager with FIXED callbacks
        try:
            hotkey_manager = HotkeyManager(
                toggle_hotkey="<ctrl>+\\",
                toggle_callback=safe_toggle,
                question_hotkey="<ctrl>+<enter>",
                question_callback=safe_show_input  # Fixed: just show input box
            )
            hotkey_manager.start()
            print("⌨️  Hotkeys ready:")
            print("   • Ctrl+\\ → Toggle visibility")
            print("   • Ctrl+Enter → Show input box (then type or press Enter)")
        except Exception as e:
            print(f"⚠️  Hotkey setup failed: {e}")
            hotkey_manager = None
        
        # Show UI
        ui.show()
        ui.raise_()
        ui.activateWindow()
        
        # Start background screen optimizer
        screen_optimizer = ScreenOptimizer()
        screen_optimizer.start()
        
        # Enhanced cleanup handler
        def enhanced_cleanup():
            """Enhanced cleanup with better error handling"""
            print("🛑 Shutting down...")
            try:
                # Stop hotkeys
                if hotkey_manager:
                    hotkey_manager.stop()
                
                # End session
                session_manager.end_session()
                
                # Stop background threads
                screen_optimizer.quit()
                if screen_optimizer.isRunning():
                    screen_optimizer.wait(2000)  # Wait max 2 seconds
                
                print("✅ Cleanup completed")
                
            except Exception as e:
                print(f"⚠️  Cleanup error: {e}")
        
        # Setup signal handlers with error handling
        def signal_handler(sig, frame):
            """Handle system signals gracefully"""
            print(f"\n🔔 Received signal {sig}")
            enhanced_cleanup()
            app.quit()
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception as e:
            print(f"⚠️  Signal handler setup failed: {e}")
        
        # Connect cleanup to app quit
        app.aboutToQuit.connect(enhanced_cleanup)
        
        # Setup session refresh timer
        try:
            refresh_timer = QTimer()
            refresh_timer.timeout.connect(ui.update_session_dropdown)
            refresh_timer.start(60000)  # Every 60 seconds
        except Exception as e:
            print(f"⚠️  Timer setup failed: {e}")
        
        # Calculate and display startup time
        startup_time = time.time() - start_total
        print(f"🎉 Wheel4 ready in {startup_time:.2f}s!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("   FIXED Controls:")
        print("   • Ctrl+\\ → Toggle visibility")
        print("   • Ctrl+Enter → Show input box")
        print("   • Then: Type & Enter → Process question")
        print("   • Or: Just Enter → Analyze screen")
        print("   • Custom Instructions: Set before first use")
        print("   • Instructions lock after first interaction")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Run application
        return app.exec()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)