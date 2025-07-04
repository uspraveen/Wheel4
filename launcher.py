#!/usr/bin/env python3
"""
Simple launcher for debugging
"""

import sys
import os


def main():
    print("🚀 Wheel4 AI Brain Launcher")
    print("=" * 40)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    
    # List files in current directory
    files = os.listdir('.')
    print(f"Files in directory: {files}")
    
    # Check if all required files exist
    required_files = [
        'main.py', 'ui.py', 'database.py', 'ai_service.py', 
        'screen_capture.py', 'hotkeys.py', 'prompts.py', 'config.py'
    ]
    
    print("\nChecking required files:")
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING!")
    
    # Try to import main function
    print("\nTrying to import main...")
    try:
        from main import main as main_func
        print("✅ Main function imported successfully")
        
        print("\nStarting main application...")
        main_func()
        
    except Exception as e:
        print(f"❌ Failed to import/run main: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")

if __name__ == "__main__":
    main()