#!/usr/bin/env python3
"""
Debug Test Script - Run this to identify where the hang occurs
Save this as debug_hang.py and run it to find the problem
"""

import sys
import time
import threading
import os

# Add the current directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_with_timeout(func, timeout=10, description=""):
    """Test a function with timeout"""
    print(f"🔍 Testing: {description}")
    
    result = {"completed": False, "error": None, "result": None}
    
    def run_test():
        try:
            start_time = time.time()
            result["result"] = func()
            result["completed"] = True
            elapsed = time.time() - start_time
            print(f"✅ {description} completed in {elapsed:.2f}s")
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ {description} failed: {e}")
    
    # Run test in thread with timeout
    thread = threading.Thread(target=run_test)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        print(f"⏰ {description} TIMED OUT after {timeout} seconds - THIS IS WHERE THE HANG OCCURS!")
        return None
    elif result["completed"]:
        return result["result"]
    elif result["error"]:
        print(f"❌ {description} error: {result['error']}")
        return None
    else:
        print(f"❓ {description} unknown state")
        return None

def test_imports():
    """Test all imports"""
    try:
        print("Testing imports...")
        import openai
        print(f"✅ OpenAI imported (version: {openai.__version__})")
        
        import mss
        print(f"✅ MSS imported")
        
        from database import get_api_key
        print(f"✅ Database module imported")
        
        from screen_capture import capture_full_screen
        print(f"✅ Screen capture module imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_api_key():
    """Test API key retrieval"""
    try:
        from database import get_api_key
        api_key = get_api_key()
        if api_key:
            print(f"✅ API key found (length: {len(api_key)})")
            return api_key
        else:
            print(f"❌ No API key found")
            return None
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return None

def test_openai_client(api_key):
    """Test OpenAI client initialization"""
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        print(f"✅ OpenAI client initialized")
        return client
    except Exception as e:
        print(f"❌ OpenAI client initialization failed: {e}")
        return None

def test_simple_api_call(client):
    """Test simple API call"""
    try:
        print(f"🤖 Making simple API call...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        result = response.choices[0].message.content
        print(f"✅ API call successful: {result}")
        return True
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

def test_screenshot():
    """Test screenshot capture"""
    try:
        from screen_capture import capture_full_screen
        screenshot = capture_full_screen()
        if screenshot:
            size_kb = len(screenshot) / 1024
            print(f"✅ Screenshot captured: {size_kb:.1f}KB")
            return True
        else:
            print(f"❌ Screenshot capture returned None")
            return False
    except Exception as e:
        print(f"❌ Screenshot capture failed: {e}")
        return False

def test_ai_service_simple():
    """Test simple AI service call"""
    try:
        from ai_service import get_ai_response
        print(f"🤖 Testing AI service with simple question...")
        response = get_ai_response("Hello, just say 'test successful'", None, "")
        if isinstance(response, dict) and "error" in response:
            print(f"❌ AI service returned error: {response['error']}")
            return False
        elif response:
            print(f"✅ AI service successful: {str(response)[:100]}...")
            return True
        else:
            print(f"❌ AI service returned empty response")
            return False
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        return False

def test_ai_service_with_screenshot():
    """Test AI service with screenshot"""
    try:
        from ai_service import get_ai_response
        from screen_capture import capture_full_screen
        
        print(f"🤖 Testing AI service with screenshot...")
        screenshot = capture_full_screen()
        response = get_ai_response("What can you see in this screenshot?", screenshot, "")
        
        if isinstance(response, dict) and "error" in response:
            print(f"❌ AI service with screenshot returned error: {response['error']}")
            return False
        elif response:
            print(f"✅ AI service with screenshot successful: {str(response)[:100]}...")
            return True
        else:
            print(f"❌ AI service with screenshot returned empty response")
            return False
    except Exception as e:
        print(f"❌ AI service with screenshot test failed: {e}")
        return False

def main():
    """Run all tests to identify the hang location"""
    print("=" * 60)
    print("🔍 WHEEL4 DEBUG TEST - Identifying Hang Location")
    print("=" * 60)
    print()
    
    # Test 1: Imports
    print("TEST 1: Module Imports")
    imports_result = test_with_timeout(
        test_imports,
        timeout=5,
        description="Module imports"
    )
    if not imports_result:
        print("❌ Cannot proceed without imports")
        return
    print()
    
    # Test 2: API Key
    print("TEST 2: API Key")
    api_key = test_with_timeout(
        test_api_key,
        timeout=5,
        description="API key retrieval"
    )
    if not api_key:
        print("❌ Cannot proceed without API key")
        return
    print()
    
    # Test 3: OpenAI Client
    print("TEST 3: OpenAI Client Initialization")
    client = test_with_timeout(
        lambda: test_openai_client(api_key),
        timeout=10,
        description="OpenAI client initialization"
    )
    if not client:
        print("❌ Cannot proceed without OpenAI client")
        return
    print()
    
    # Test 4: Screenshot Capture
    print("TEST 4: Screenshot Capture")
    screenshot_result = test_with_timeout(
        test_screenshot,
        timeout=15,
        description="Screenshot capture"
    )
    print()
    
    # Test 5: Simple API Call
    print("TEST 5: Simple API Call")
    api_result = test_with_timeout(
        lambda: test_simple_api_call(client),
        timeout=30,
        description="Simple API call"
    )
    print()
    
    # Test 6: AI Service Simple
    print("TEST 6: AI Service (Simple)")
    ai_simple_result = test_with_timeout(
        test_ai_service_simple,
        timeout=30,
        description="AI service simple test"
    )
    print()
    
    # Test 7: AI Service with Screenshot
    print("TEST 7: AI Service (With Screenshot)")
    ai_screenshot_result = test_with_timeout(
        test_ai_service_with_screenshot,
        timeout=45,
        description="AI service with screenshot"
    )
    print()
    
    # Summary
    print("=" * 60)
    print("🎯 HANG DETECTION SUMMARY")
    print("=" * 60)
    
    hang_detected = False
    
    if screenshot_result is None:
        print("❌ HANG DETECTED in Screenshot Capture!")
        print("💡 Problem: screen_capture.py or MSS library")
        print("🔧 Solution: Check screen permissions, try different screenshot library")
        hang_detected = True
    
    if api_result is None:
        print("❌ HANG DETECTED in OpenAI API Call!")
        print("💡 Problem: Network connection or OpenAI API")
        print("🔧 Solution: Check internet connection, try different API endpoint")
        hang_detected = True
    
    if ai_simple_result is None:
        print("❌ HANG DETECTED in AI Service (Simple)!")
        print("💡 Problem: ai_service.py internal logic")
        print("🔧 Solution: Use the fixed ai_service.py with timeout protection")
        hang_detected = True
    
    if ai_screenshot_result is None:
        print("❌ HANG DETECTED in AI Service (With Screenshot)!")
        print("💡 Problem: Screenshot processing in AI service")
        print("🔧 Solution: Use threading or skip screenshot mode")
        hang_detected = True
    
    if not hang_detected:
        print("✅ No hangs detected in individual components!")
        print("💡 The hang might be in the UI thread interaction")
        print("🔧 Solution: Use the threaded UI version provided")
    
    print()
    print("NEXT STEPS:")
    print("1. If screenshot hangs: Check screen capture permissions")
    print("2. If API call hangs: Check internet connection and API key")
    print("3. If AI service hangs: Replace ai_service.py with the fixed version")
    print("4. If no hangs detected: Replace ui.py with the threaded version")
    print()
    print("FILES TO REPLACE:")
    print("- ui.py: Use the complete fixed version with threading")
    print("- ai_service.py: Use the version with timeout protection")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Critical test error: {e}")
        import traceback
        traceback.print_exc()