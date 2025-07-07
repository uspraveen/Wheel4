#!/usr/bin/env python3
"""
Wheel4 - Enhanced Windows Ultra-Fast High-Quality Screenshot
Optimized compression and performance improvements with screen validation
"""

import threading
import queue
import time
import io
from PIL import Image, ImageOps
import sys

# Global screen info
_screen_info = None
_best_method = None

def get_screen_info():
    """Get screen dimensions with Windows API"""
    global _screen_info
    if _screen_info is None:
        try:
            # Try Windows API first
            import win32api
            width = win32api.GetSystemMetrics(0)  # SM_CXSCREEN
            height = win32api.GetSystemMetrics(1)  # SM_CYSCREEN
            _screen_info = {'width': width, 'height': height, 'left': 0, 'top': 0}
            print(f"📐 Windows API Screen: {width}x{height}")
        except ImportError:
            try:
                # Fallback to MSS
                import mss
                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    _screen_info = {
                        'width': monitor['width'], 'height': monitor['height'],
                        'left': monitor['left'], 'top': monitor['top']
                    }
                    print(f"📐 MSS Screen: {_screen_info['width']}x{_screen_info['height']}")
            except Exception:
                # Ultimate fallback
                _screen_info = {'width': 1920, 'height': 1080, 'left': 0, 'top': 0}
                print(f"📐 Fallback Screen: 1920x1080")
    
    return _screen_info

def windows_gdi_capture():
    """Windows GDI capture - often fastest on Windows"""
    try:
        import win32gui
        import win32ui
        import win32con
        from PIL import Image
        
        # Get screen dimensions
        screen_info = get_screen_info()
        width, height = screen_info['width'], screen_info['height']
        
        # Create device contexts
        hdesktop = win32gui.GetDesktopWindow()
        desktop_dc = win32gui.GetWindowDC(hdesktop)
        img_dc = win32ui.CreateDCFromHandle(desktop_dc)
        mem_dc = img_dc.CreateCompatibleDC()
        
        # Create bitmap
        screenshot = win32ui.CreateBitmap()
        screenshot.CreateCompatibleBitmap(img_dc, width, height)
        mem_dc.SelectObject(screenshot)
        
        # Copy screen to bitmap
        mem_dc.BitBlt((0, 0), (width, height), img_dc, (0, 0), win32con.SRCCOPY)
        
        # Convert to PIL Image
        bmpinfo = screenshot.GetInfo()
        bmpstr = screenshot.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        
        # Cleanup
        mem_dc.DeleteDC()
        img_dc.DeleteDC()
        win32gui.ReleaseDC(hdesktop, desktop_dc)
        screenshot.DeleteObject()
        
        return img
        
    except Exception as e:
        print(f"❌ Windows GDI capture failed: {e}")
        return None

def windows_imagegrab_capture():
    """PIL ImageGrab optimized for Windows"""
    try:
        from PIL import ImageGrab
        
        # Fast full-screen grab
        img = ImageGrab.grab(all_screens=False)  # Primary screen only for speed
        return img
        
    except Exception as e:
        print(f"❌ PIL ImageGrab capture failed: {e}")
        return None

def windows_mss_optimized():
    """MSS with Windows optimizations"""
    try:
        import mss
        
        screen_info = get_screen_info()
        
        # Configure MSS for Windows performance
        with mss.mss() as sct:
            # Use specific monitor instead of all screens
            monitor = {
                'left': screen_info['left'],
                'top': screen_info['top'],
                'width': screen_info['width'],
                'height': screen_info['height']
            }
            
            # Grab screenshot
            screenshot = sct.grab(monitor)
            
            # Fast conversion
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            return img
            
    except Exception as e:
        print(f"❌ Optimized MSS capture failed: {e}")
        return None

def smart_resize_for_tokens(img, target_tokens=600):
    """Intelligently resize image to target token count while preserving quality"""
    try:
        original_width, original_height = img.size
        total_pixels = original_width * original_height
        
        # Calculate optimal size based on target tokens
        # OpenAI Vision uses ~1 token per 170 pixels at high detail
        target_pixels = target_tokens * 170
        
        if total_pixels <= target_pixels:
            return img  # No resize needed
        
        # Calculate new dimensions maintaining aspect ratio
        scale_factor = (target_pixels / total_pixels) ** 0.5
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Ensure minimum size for readability - but more conservative
        min_width, min_height = 1000, 700  # Increased minimum size
        if new_width < min_width or new_height < min_height:
            aspect_ratio = original_width / original_height
            if aspect_ratio > 1:  # Landscape
                new_width = min_width
                new_height = int(min_width / aspect_ratio)
            else:  # Portrait
                new_height = min_height
                new_width = int(min_height * aspect_ratio)
        
        print(f"🔄 Resizing from {original_width}x{original_height} to {new_width}x{new_height}")
        
        # Use high-quality resampling
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return resized_img
        
    except Exception as e:
        print(f"⚠️ Resize failed: {e}, returning original")
        return img

def ultra_fast_compression(img, target_quality="balanced"):
    """Ultra-fast compression optimized for speed while maintaining quality"""
    
    try:
        # Smart resize first for better token efficiency - but less aggressive
        img = smart_resize_for_tokens(img, target_tokens=800)  # Increased target tokens
        
        if target_quality == "fast":
            # Fastest compression
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=75, optimize=False)  # Increased quality
            return buffer.getvalue()
        
        elif target_quality == "balanced":
            # Balanced speed/quality
            buffer = io.BytesIO()
            
            # Try PNG first for screenshots (often better compression for UI)
            png_buffer = io.BytesIO()
            img.save(png_buffer, format="PNG", optimize=True, compress_level=4)  # Reduced compression for speed
            png_size = len(png_buffer.getvalue())
            
            # Try JPEG
            jpeg_buffer = io.BytesIO()
            if img.mode in ('RGBA', 'LA'):
                # Convert RGBA to RGB for JPEG
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                background.save(jpeg_buffer, format="JPEG", quality=85, optimize=True)  # Increased quality
            else:
                img.save(jpeg_buffer, format="JPEG", quality=85, optimize=True)
            jpeg_size = len(jpeg_buffer.getvalue())
            
            # Choose smaller format, but prefer PNG for UI screenshots
            if png_size < jpeg_size * 1.5:  # Allow PNG to be up to 50% larger
                return png_buffer.getvalue()
            else:
                return jpeg_buffer.getvalue()
        
        else:  # high quality
            # High quality with PNG
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True, compress_level=6)
            return buffer.getvalue()
            
    except Exception as e:
        print(f"⚠️ Ultra-fast compression error: {e}")
        # Fallback to basic JPEG
        try:
            buffer = io.BytesIO()
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                background.save(buffer, format="JPEG", quality=80)
            else:
                img.save(buffer, format="JPEG", quality=80)
            return buffer.getvalue()
        except Exception as e2:
            print(f"❌ Fallback compression failed: {e2}")
            return None

def validate_screenshot_quality(img, original_size):
    """Validate that screenshot captures important screen elements"""
    try:
        # Check if we've lost too much detail
        current_size = img.size
        width_ratio = current_size[0] / original_size[0]
        height_ratio = current_size[1] / original_size[1]
        
        # If we've shrunk too much, warn about potential quality loss
        if width_ratio < 0.4 or height_ratio < 0.4:
            print(f"⚠️  Screenshot significantly reduced: {original_size} -> {current_size}")
            print(f"   Quality may be compromised for detailed screen elements")
            
        # Check if image has enough contrast and detail
        # Convert a small sample to grayscale and check variance
        try:
            sample = img.resize((100, 100))
            grayscale = sample.convert('L')
            pixels = list(grayscale.getdata())
            
            # Calculate variance to check if image has content
            mean = sum(pixels) / len(pixels)
            variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
            
            if variance < 100:  # Very low variance suggests blank/uniform image
                print(f"⚠️  Screenshot may be blank or very uniform (variance: {variance:.1f})")
                
        except Exception as e:
            print(f"⚠️  Could not validate screenshot content: {e}")
            
    except Exception as e:
        print(f"⚠️  Screenshot validation error: {e}")

def benchmark_capture_methods():
    """Benchmark all capture methods to find the fastest"""
    print("🚀 Benchmarking Windows screenshot methods...")
    
    methods = [
        ("Windows GDI", windows_gdi_capture),
        ("PIL ImageGrab", windows_imagegrab_capture),
        ("MSS Optimized", windows_mss_optimized),
    ]
    
    results = []
    
    for name, method in methods:
        print(f"\n🔍 Testing {name}...")
        times = []
        success_count = 0
        
        # Test each method 3 times
        for i in range(3):
            try:
                start = time.time()
                result = method()
                elapsed = time.time() - start
                
                if result:
                    times.append(elapsed)
                    success_count += 1
                    size_mb = (result.width * result.height * 3) / (1024 * 1024)
                    print(f"  Test {i+1}: ✅ {elapsed:.2f}s ({result.width}x{result.height}, {size_mb:.1f}MB)")
                else:
                    print(f"  Test {i+1}: ❌ Failed")
                    
            except Exception as e:
                elapsed = time.time() - start
                print(f"  Test {i+1}: ❌ Error in {elapsed:.2f}s: {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            success_rate = success_count / 3 * 100
            results.append((name, avg_time, min_time, success_rate, method))
            print(f"  📊 {name}: Avg {avg_time:.2f}s, Best {min_time:.2f}s, Success {success_rate:.0f}%")
        else:
            print(f"  📊 {name}: FAILED - 0% success rate")
    
    # Find the best method
    if results:
        # Sort by success rate first, then by speed
        results.sort(key=lambda x: (-x[3], x[1]))  # -success_rate, +avg_time
        
        best = results[0]
        print(f"\n🏆 BEST METHOD: {best[0]} (Avg: {best[1]:.2f}s, Success: {best[3]:.0f}%)")
        
        return best[4]  # Return the method function
    else:
        print(f"\n❌ NO WORKING METHODS FOUND!")
        return None

def enhanced_quality_capture():
    """Enhanced fast high-quality screenshot using the best method"""
    global _best_method
    
    # Auto-detect best method if not cached
    if _best_method is None:
        print("🔧 Auto-detecting best screenshot method...")
        _best_method = benchmark_capture_methods()
        
        if _best_method is None:
            print("❌ No working screenshot methods available!")
            return None
    
    try:
        print(f"📸 Using optimized capture method...")
        start = time.time()
        
        # Capture with best method
        img = _best_method()
        
        if img:
            original_size = img.size
            capture_time = time.time() - start
            
            # Validate screenshot quality before compression
            validate_screenshot_quality(img, original_size)
            
            # Enhanced fast compression
            compress_start = time.time()
            screenshot_bytes = ultra_fast_compression(img, "balanced")
            compress_time = time.time() - compress_start
            
            total_time = time.time() - start
            size_kb = len(screenshot_bytes) / 1024 if screenshot_bytes else 0
            
            print(f"✅ ENHANCED capture: {img.width}x{img.height} -> {size_kb:.1f}KB")
            print(f"   Timing: Capture {capture_time:.2f}s + Compress {compress_time:.2f}s = {total_time:.2f}s total")
            
            return screenshot_bytes
        else:
            print(f"❌ Capture method returned None")
            return None
            
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Enhanced capture failed in {elapsed:.2f}s: {e}")
        return None

def capture_full_screen_with_timeout(timeout=2):
    """Capture full screen with reduced timeout for better performance"""
    result_queue = queue.Queue()
    
    def capture_worker():
        try:
            result = enhanced_quality_capture()
            result_queue.put(("success", result))
        except Exception as e:
            result_queue.put(("error", str(e)))
    
    # Start capture thread
    thread = threading.Thread(target=capture_worker)
    thread.daemon = True
    thread.start()
    
    # Wait with timeout
    try:
        result_type, result = result_queue.get(timeout=timeout)
        if result_type == "success":
            return result
        else:
            print(f"❌ Capture worker error: {result}")
            return None
    except queue.Empty:
        print(f"⏰ Enhanced capture timed out after {timeout} seconds")
        return None

def capture_full_screen(custom_settings=None):
    """Main function: Enhanced fast full-screen capture"""
    print(f"🎯 ENHANCED full-screen capture starting...")
    start_time = time.time()
    
    try:
        # Try enhanced capture with shorter timeout for better performance
        screenshot_bytes = capture_full_screen_with_timeout(timeout=3)  # Reduced from 4 to 3
        
        elapsed = time.time() - start_time
        
        if screenshot_bytes:
            size_kb = len(screenshot_bytes) / 1024
            print(f"🏆 ENHANCED capture SUCCESS: {size_kb:.1f}KB in {elapsed:.2f}s")
            return screenshot_bytes
        else:
            print(f"❌ Enhanced capture failed in {elapsed:.2f}s")
            return None
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Enhanced capture exception in {elapsed:.2f}s: {e}")
        return None

def smart_capture():
    """Smart capture = enhanced capture"""
    return capture_full_screen()

def get_optimal_settings_for_tokens():
    """Enhanced settings optimized for quality + reasonable tokens"""
    screen_info = get_screen_info()
    total_pixels = screen_info['width'] * screen_info['height']
    
    if total_pixels > 8000000:  # 4K+
        return {
            'description': '4K+ screen - enhanced quality with smart compression',
            'estimated_tokens': '700-1000'  # More conservative estimates
        }
    elif total_pixels > 4000000:  # 2K
        return {
            'description': '2K screen - enhanced quality balanced',
            'estimated_tokens': '500-700'   
        }
    else:  # 1080p and below
        return {
            'description': 'Standard resolution - enhanced maximum quality',
            'estimated_tokens': '300-500'   
        }

def force_method_selection():
    """Force re-selection of the best capture method"""
    global _best_method
    _best_method = None
    print("🔄 Forcing re-detection of best capture method...")
    return benchmark_capture_methods()

# Performance monitoring functions
def get_capture_performance_stats():
    """Get performance statistics for capture system"""
    return {
        'best_method': _best_method.__name__ if _best_method else None,
        'screen_info': _screen_info,
        'optimal_settings': get_optimal_settings_for_tokens()
    }

def optimize_for_speed():
    """Optimize capture system for maximum speed"""
    global _best_method
    print("⚡ Optimizing capture system for speed...")
    
    # Force re-benchmark to find fastest method
    _best_method = None
    benchmark_capture_methods()
    
    # Test compression speeds
    if _best_method:
        try:
            test_img = _best_method()
            if test_img:
                start = time.time()
                result = ultra_fast_compression(test_img, "fast")
                elapsed = time.time() - start
                print(f"⚡ Speed optimization complete - compression: {elapsed:.2f}s")
        except Exception as e:
            print(f"⚠️ Speed optimization test failed: {e}")

def get_screen_capture_info():
    """Get detailed information about current screen capture setup"""
    screen_info = get_screen_info()
    optimal_settings = get_optimal_settings_for_tokens()
    
    return {
        'screen_resolution': f"{screen_info['width']}x{screen_info['height']}",
        'capture_method': _best_method.__name__ if _best_method else 'Not detected',
        'estimated_tokens': optimal_settings['estimated_tokens'],
        'description': optimal_settings['description']
    }

if __name__ == "__main__":
    print("🎯 Enhanced Windows Ultra-Fast High-Quality Screenshot System")
    
    # Show screen info
    screen_info = get_screen_info()
    print(f"Screen: {screen_info['width']}x{screen_info['height']}")
    
    # Benchmark methods
    best_method = benchmark_capture_methods()
    
    if best_method:
        print(f"\n🧪 Testing enhanced capture...")
        start = time.time()
        result = capture_full_screen()
        elapsed = time.time() - start
        
        if result:
            size_kb = len(result) / 1024
            print(f"🏆 FINAL TEST: SUCCESS - {size_kb:.1f}KB in {elapsed:.2f}s")
            
            # Test speed optimization
            optimize_for_speed()
            
            # Show capture info
            info = get_screen_capture_info()
            print(f"📊 Capture System Info:")
            print(f"   Resolution: {info['screen_resolution']}")
            print(f"   Method: {info['capture_method']}")
            print(f"   Token estimate: {info['estimated_tokens']}")
            print(f"   Quality: {info['description']}")
        else:
            print(f"❌ FINAL TEST: FAILED in {elapsed:.2f}s")
    else:
        print(f"❌ No working screenshot methods available!")