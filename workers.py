#!/usr/bin/env python3
"""
Wheel4 - Worker Threads
High-performance threading for DB and AI operations
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import threading
import queue
import time

from database import save_interaction, get_session_history, save_api_key, get_api_key
from ai_service import get_ai_response, test_api_key
from screen_capture import capture_full_screen

class DatabaseWorker(QObject):
    """High-performance database worker with queue processing"""
    
    # Signals for UI updates
    interaction_saved = pyqtSignal(bool)
    api_key_saved = pyqtSignal(bool)
    history_loaded = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.running = True
        
    def run(self):
        """Main worker loop"""
        while self.running:
            try:
                # Process tasks from queue
                if not self.task_queue.empty():
                    task = self.task_queue.get(timeout=0.1)
                    self.process_task(task)
                else:
                    time.sleep(0.01)  # Small delay to prevent CPU spinning
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Database worker error: {e}")
                
    def process_task(self, task):
        """Process a database task"""
        task_type = task.get('type')
        
        try:
            if task_type == 'save_interaction':
                session_id = task['session_id']
                question = task['question']
                response = task['response']
                
                save_interaction(session_id, question, response)
                self.interaction_saved.emit(True)
                print(f"💾 Interaction saved for session {session_id}")
                
            elif task_type == 'save_api_key':
                api_key = task['api_key']
                save_api_key(api_key)
                self.api_key_saved.emit(True)
                print("🔑 API key saved")
                
            elif task_type == 'load_history':
                session_id = task['session_id']
                limit = task.get('limit', 20)
                
                history = get_session_history(session_id, limit)
                self.history_loaded.emit(history)
                print(f"📚 Loaded {len(history)} history items")
                
        except Exception as e:
            print(f"❌ Database task error: {e}")
            if task_type == 'save_interaction':
                self.interaction_saved.emit(False)
            elif task_type == 'save_api_key':
                self.api_key_saved.emit(False)
                
    def queue_save_interaction(self, session_id, question, response):
        """Queue interaction save task"""
        self.task_queue.put({
            'type': 'save_interaction',
            'session_id': session_id,
            'question': question,
            'response': response
        })
        
    def queue_save_api_key(self, api_key):
        """Queue API key save task"""
        self.task_queue.put({
            'type': 'save_api_key',
            'api_key': api_key
        })
        
    def queue_load_history(self, session_id, limit=20):
        """Queue history load task"""
        self.task_queue.put({
            'type': 'load_history',
            'session_id': session_id,
            'limit': limit
        })
        
    def stop(self):
        """Stop the worker"""
        self.running = False

class AIWorker(QObject):
    """High-performance AI worker with caching and optimization"""
    
    # Signals for UI updates
    response_ready = pyqtSignal(str, str, str)  # question, response, session_context
    error_occurred = pyqtSignal(str)
    processing_started = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.running = True
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.screenshot_cache_duration = 1.0  # Cache for 1 second
        
    def run(self):
        """Main worker loop"""
        while self.running:
            try:
                if not self.task_queue.empty():
                    task = self.task_queue.get(timeout=0.1)
                    self.process_task(task)
                else:
                    time.sleep(0.01)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ AI worker error: {e}")
                self.error_occurred.emit(str(e))
                
    def process_task(self, task):
        """Process an AI task"""
        task_type = task.get('type')
        
        if task_type == 'get_response':
            self.processing_started.emit()
            
            question = task['question']
            session_id = task['session_id']
            use_history = task.get('use_history', True)
            
            try:
                # Get optimized screenshot
                screenshot = self.get_optimized_screenshot()
                
                # Build context from session history if needed
                context = ""
                if use_history:
                    context = self.build_session_context(session_id)
                
                # Get AI response
                print("🤖 Getting AI response...")
                start_time = time.time()
                
                response = get_ai_response(question, screenshot, context)
                
                elapsed = time.time() - start_time
                print(f"✅ AI response received in {elapsed:.2f}s")
                
                self.response_ready.emit(question, response, context)
                
            except Exception as e:
                print(f"❌ AI processing error: {e}")
                self.error_occurred.emit(str(e))
                
        elif task_type == 'test_api_key':
            api_key = task['api_key']
            try:
                is_valid = test_api_key(api_key)
                self.response_ready.emit("test", str(is_valid), "")
            except Exception as e:
                self.error_occurred.emit(str(e))
                
    def get_optimized_screenshot(self):
        """Get screenshot with caching for performance"""
        current_time = time.time()
        
        # Use cached screenshot if recent
        if (self.last_screenshot and 
            current_time - self.last_screenshot_time < self.screenshot_cache_duration):
            print("📸 Using cached screenshot")
            return self.last_screenshot
            
        # Capture new screenshot
        print("📸 Capturing fresh screenshot...")
        screenshot = capture_full_screen()
        
        if screenshot:
            self.last_screenshot = screenshot
            self.last_screenshot_time = current_time
            
        return screenshot
        
    def build_session_context(self, session_id):
        """Build context string from session history"""
        try:
            history = get_session_history(session_id, limit=10)  # Last 10 interactions
            if not history:
                return ""
                
            context_parts = ["Previous conversation context:"]
            for question, response, timestamp in history:
                context_parts.append(f"Q: {question}")
                context_parts.append(f"A: {response[:200]}...")  # Truncate long responses
                
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"⚠️  Context building error: {e}")
            return ""
        
    def queue_get_response(self, question, session_id, use_history=True):
        """Queue AI response task"""
        self.task_queue.put({
            'type': 'get_response',
            'question': question,
            'session_id': session_id,
            'use_history': use_history
        })
        
    def queue_test_api_key(self, api_key):
        """Queue API key test task"""
        self.task_queue.put({
            'type': 'test_api_key',
            'api_key': api_key
        })
        
    def stop(self):
        """Stop the worker"""
        self.running = False