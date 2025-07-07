#!/usr/bin/env python3
"""
Wheel4 - Screen-Aware AI Service 
Always analyzes screen context with user requests
"""

import openai
import json
import re
import time
import html
import os
from datetime import datetime
from database import get_api_key, get_session_context
from prompts import get_personalized_prompts, get_user_prompt
import base64
import threading
import queue
import requests

def get_ai_response(question, screenshot=None, context="", template_key=None, custom_instructions=""):
    """Screen-aware AI response - always acknowledges screen context"""
    print(f"🔍 DEBUG: Starting screen-aware get_ai_response")
    print(f"🔍 DEBUG: Question: '{question}' (empty = auto screen analysis)")
    print(f"🔍 DEBUG: Screenshot: {'Present' if screenshot else 'None'}")
    print(f"🔍 DEBUG: Context length: {len(context) if context else 0}")
    print(f"🔍 DEBUG: Custom instructions: {'Yes' if custom_instructions else 'No'}")
    
    max_retries = 3
    base_delay = 2
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** (attempt - 1))
                print(f"🔄 Retry attempt {attempt + 1}/{max_retries} after {delay}s delay")
                time.sleep(delay)
            
            result = _make_simple_ai_request(
                question, screenshot, context, template_key, 
                custom_instructions, attempt
            )
            
            if result and not (isinstance(result, dict) and "error" in result):
                print(f"✅ Success on attempt {attempt + 1}")
                return result
            elif attempt < max_retries - 1:
                print(f"⚠️ Attempt {attempt + 1} failed, retrying...")
                continue
            else:
                return result
                
        except Exception as e:
            error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            if attempt < max_retries - 1:
                continue
            else:
                return {"error": f"All {max_retries} attempts failed. Last error: {str(e)}"}

def _make_simple_ai_request(question, screenshot, context, template_key, custom_instructions, attempt_num):
    """Screen-aware AI request - always includes screen context"""
    try:
        # Step 1: Save screenshot for testing if available
        if screenshot:
            save_screenshot_for_testing(screenshot)
        
        # Step 2: Get API key
        print(f"🔍 DEBUG: Step 2 - Getting API key...")
        api_key = get_api_key()
        if not api_key:
            print(f"❌ DEBUG: No API key configured")
            return {"error": "No API key configured"}
        print(f"🔍 DEBUG: API key found (length: {len(api_key)})")
        
        # Step 3: Initialize OpenAI client
        print(f"🔍 DEBUG: Step 3 - Initializing OpenAI client...")
        try:
            client = openai.OpenAI(
                api_key=api_key,
                timeout=30.0,
                max_retries=1
            )
            print(f"✅ DEBUG: OpenAI client initialized successfully")
        except Exception as e:
            print(f"❌ DEBUG: Failed to initialize OpenAI client: {e}")
            return {"error": f"Failed to initialize OpenAI client: {str(e)}"}
        
        # Step 4: Get simple prompts
        print(f"🔍 DEBUG: Step 4 - Getting simple prompts...")
        try:
            system_prompt, user_template = get_personalized_prompts(None, custom_instructions)
            print(f"✅ DEBUG: Prompts loaded (system: {len(system_prompt)}, user: {len(user_template)})")
            if custom_instructions:
                print(f"🎯 DEBUG: Custom instructions applied ({len(custom_instructions)} chars)")
        except Exception as e:
            print(f"❌ DEBUG: Failed to get prompts: {e}")
            return {"error": f"Failed to get prompts: {str(e)}"}
        
        # Step 5: Format simple user prompt
        print(f"🔍 DEBUG: Step 5 - Formatting simple user prompt...")
        try:
            user_prompt = get_user_prompt(question, context)
            print(f"✅ DEBUG: Simple user prompt formatted (length: {len(user_prompt)})")
        except Exception as e:
            print(f"❌ DEBUG: Failed to format user prompt: {e}")
            return {"error": f"Failed to format user prompt: {str(e)}"}
        
        # Step 6: Simple token management
        print(f"🔍 DEBUG: Step 6 - Simple token management...")
        MAX_TOTAL_TOKENS = 32000
        MAX_RESPONSE_TOKENS = 4000
        TOKEN_BUFFER = 1000
        
        system_tokens = estimate_tokens_accurately(system_prompt)
        user_tokens = estimate_tokens_accurately(user_prompt)
        screenshot_tokens = estimate_image_tokens(screenshot) if screenshot else 0
        
        total_input_tokens = system_tokens + user_tokens + screenshot_tokens
        available_tokens = MAX_TOTAL_TOKENS - total_input_tokens - TOKEN_BUFFER
        response_tokens = min(MAX_RESPONSE_TOKENS, max(1000, available_tokens))
        
        print(f"📊 DEBUG: Simple token allocation:")
        print(f"   System: {system_tokens}, Question: {user_tokens}")
        print(f"   Screenshot: {screenshot_tokens}, Available: {available_tokens}")
        print(f"   Max Response: {response_tokens}")
        
        # Step 7: Prepare messages
        print(f"🔍 DEBUG: Step 7 - Preparing messages...")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Step 8: Simple screenshot processing
        if screenshot:
            print(f"🔍 DEBUG: Step 8 - Processing screenshot...")
            try:
                screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
                screenshot_size_kb = len(screenshot) / 1024
                print(f"🖼️  DEBUG: Screenshot encoded ({screenshot_size_kb:.1f}KB)")
                
                messages[1]["content"] = [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_base64}",
                            "detail": "high"
                        }
                    }
                ]
                print(f"✅ DEBUG: Screenshot added to message")
            except Exception as e:
                print(f"⚠️  DEBUG: Screenshot encoding error: {e}")
        else:
            print(f"🔍 DEBUG: Step 8 - No screenshot")
        
        # Step 9: Simple API call
        print(f"🔍 DEBUG: Step 9 - Making simple API call (attempt {attempt_num + 1})...")
        start_time = time.time()
        
        try:
            print(f"🤖 DEBUG: Calling OpenAI API...")
            
            response = call_openai_with_enhanced_timeout(
                client, messages, response_tokens, 
                timeout=40,
                attempt_num=attempt_num
            )
            
            print(f"✅ DEBUG: API call completed successfully")
            
        except TimeoutError:
            print(f"❌ DEBUG: API call timed out after 40 seconds")
            return {"error": "API call timed out. Please check your internet connection and try again."}
        except openai.RateLimitError as e:
            print(f"❌ DEBUG: Rate limit exceeded: {e}")
            return {"error": "API rate limit exceeded. Please try again in a moment."}
        except openai.AuthenticationError as e:
            print(f"❌ DEBUG: Authentication error: {e}")
            return {"error": "Invalid API key. Please check your OpenAI API key in settings."}
        except Exception as e:
            print(f"❌ DEBUG: Unexpected API error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"API error: {str(e)}. Please try again."}
        
        # Step 10: Extract response
        print(f"🔍 DEBUG: Step 10 - Extracting response...")
        try:
            ai_response = response.choices[0].message.content
            print(f"✅ DEBUG: Response extracted (length: {len(ai_response)})")
            
            if not ai_response or len(ai_response.strip()) < 10:
                print(f"⚠️  DEBUG: Response too short, might be malformed")
                return {"error": "Received empty or invalid response from AI"}
                
        except Exception as e:
            print(f"❌ DEBUG: Failed to extract response: {e}")
            return {"error": f"Failed to extract response: {str(e)}"}
        
        # Step 11: Token usage tracking
        print(f"🔍 DEBUG: Step 11 - Processing usage stats...")
        try:
            usage = response.usage
            elapsed = time.time() - start_time
            
            print(f"✅ DEBUG: AI response received ({len(ai_response)} chars)")
            print(f"📊 DEBUG: Token usage: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")
            print(f"⏱️  DEBUG: Response time: {elapsed:.2f}s")
        except Exception as e:
            print(f"⚠️  DEBUG: Error processing usage stats: {e}")
        
        print(f"✅ DEBUG: Simple get_ai_response completed successfully")
        return ai_response
        
    except Exception as e:
        error_msg = f"AI service error: {str(e)}"
        print(f"❌ DEBUG: {error_msg}")
        import traceback
        traceback.print_exc()
        return {"error": error_msg}

def save_screenshot_for_testing(screenshot_bytes):
    """Save screenshot to disk for testing"""
    try:
        screenshots_dir = "screenshots_test"
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screen_test_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(screenshot_bytes)
        
        size_kb = len(screenshot_bytes) / 1024
        print(f"💾 DEBUG: Screenshot saved for testing: {filepath} ({size_kb:.1f}KB)")
        
        cleanup_old_screenshots(screenshots_dir, keep_count=5)
        
    except Exception as e:
        print(f"⚠️  DEBUG: Failed to save screenshot for testing: {e}")

def cleanup_old_screenshots(directory, keep_count=5):
    """Keep only the most recent screenshots"""
    try:
        files = []
        for filename in os.listdir(directory):
            if filename.startswith("screen_test_") and filename.endswith(".png"):
                filepath = os.path.join(directory, filename)
                files.append((filepath, os.path.getctime(filepath)))
        
        files.sort(key=lambda x: x[1], reverse=True)
        
        for filepath, _ in files[keep_count:]:
            try:
                os.remove(filepath)
                print(f"🗑️  DEBUG: Removed old screenshot: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"⚠️  DEBUG: Failed to remove old screenshot: {e}")
                
    except Exception as e:
        print(f"⚠️  DEBUG: Error cleaning up screenshots: {e}")

def call_openai_with_enhanced_timeout(client, messages, response_tokens, timeout=40, attempt_num=0):
    """Enhanced API call with timeout handling"""
    result_queue = queue.Queue()
    
    def api_call():
        try:
            print(f"🔍 DEBUG: Starting API call in thread (attempt {attempt_num + 1})...")
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=int(response_tokens),
                temperature=0.3,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
                stream=False,
                timeout=timeout - 5
            )
            print(f"✅ DEBUG: API call completed in thread")
            result_queue.put(("success", response))
            
        except openai.APITimeoutError as e:
            print(f"❌ DEBUG: OpenAI API timeout: {e}")
            result_queue.put(("timeout", e))
        except openai.APIConnectionError as e:
            print(f"❌ DEBUG: OpenAI API connection error: {e}")
            result_queue.put(("connection_error", e))
        except Exception as e:
            print(f"❌ DEBUG: API call failed in thread: {e}")
            result_queue.put(("error", e))
    
    api_thread = threading.Thread(target=api_call)
    api_thread.daemon = True
    api_thread.start()
    
    try:
        result_type, result = result_queue.get(timeout=timeout)
        
        if result_type == "success":
            return result
        elif result_type == "timeout":
            raise TimeoutError(f"OpenAI API timed out: {result}")
        elif result_type == "connection_error":
            raise Exception(f"Connection error: {result}")
        else:
            raise result
            
    except queue.Empty:
        print(f"❌ DEBUG: API call wrapper timed out after {timeout} seconds")
        raise TimeoutError(f"API call timed out after {timeout} seconds")

def estimate_tokens_accurately(text):
    """Token estimation"""
    if not text:
        return 0
    
    char_count = len(str(text))
    word_count = len(str(text).split())
    
    base_tokens = char_count / 3.5
    word_tokens = word_count * 1.3
    estimated = int((base_tokens + word_tokens) / 2 * 1.1)
    
    return max(estimated, word_count)

def estimate_image_tokens(image_bytes):
    """Image token estimation"""
    if not image_bytes:
        return 0
    
    size_kb = len(image_bytes) / 1024
    
    if size_kb < 100:
        return 400
    elif size_kb < 300:
        return 600
    else:
        return 1000

def extract_json_from_response(response_text):
    """Enhanced JSON extraction"""
    try:
        print("🔍 Starting JSON extraction...")
        
        if isinstance(response_text, dict):
            print("✅ Response is already a dict")
            return validate_and_fix_json_structure(response_text)
        
        if not isinstance(response_text, str):
            response_text = str(response_text)
        
        cleaned_text = response_text.strip()
        print(f"📝 Processing {len(cleaned_text)} characters...")
        
        if len(cleaned_text) < 10:
            print("⚠️  Response too short, using fallback")
            return create_fallback_response("Response was too short or empty")
        
        # Try direct JSON parsing first
        try:
            parsed = json.loads(cleaned_text)
            print("✅ Direct JSON parsing successful")
            result = validate_and_fix_json_structure(parsed)
            if result and result.get("response") and len(str(result["response"]).strip()) > 10:
                return result
            else:
                print("⚠️  Direct parsing succeeded but response field is empty")
        except json.JSONDecodeError:
            pass
        
        # JSON pattern matching
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',
            r'\{[\s\S]*?\}',
            r'```(?:json)?\s*(\{[\s\S]*?\})\s*```',
            r'```\s*(\{[\s\S]*?\})\s*```',
            r'(?:^|\n)\s*(\{[\s\S]*?\})\s*(?:\n|$)',
        ]
        
        potential_jsons = []
        for pattern in json_patterns:
            matches = re.findall(pattern, cleaned_text, re.DOTALL)
            potential_jsons.extend(matches)
        
        # Find between first { and last }
        if not potential_jsons:
            first_brace = cleaned_text.find('{')
            last_brace = cleaned_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                potential_jsons.append(cleaned_text[first_brace:last_brace + 1])
        
        # Try parsing each potential JSON
        for i, potential_json in enumerate(potential_jsons):
            print(f"🔧 Trying JSON candidate {i+1}...")
            
            try:
                cleaned_json = clean_json_string(potential_json)
                parsed_json = json.loads(cleaned_json)
                
                if isinstance(parsed_json, dict) and parsed_json.get("response") and len(str(parsed_json["response"]).strip()) > 10:
                    print(f"✅ JSON candidate {i+1} parsed successfully with content")
                    return validate_and_fix_json_structure(parsed_json)
                else:
                    print(f"⚠️  JSON candidate {i+1} parsed but missing response content")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON candidate {i+1} failed: {e}")
                fixed_json = fix_common_json_issues(potential_json)
                try:
                    parsed_json = json.loads(fixed_json)
                    if isinstance(parsed_json, dict) and parsed_json.get("response") and len(str(parsed_json["response"]).strip()) > 10:
                        print(f"✅ JSON candidate {i+1} fixed and parsed successfully")
                        return validate_and_fix_json_structure(parsed_json)
                    else:
                        print(f"⚠️  JSON candidate {i+1} fixed but missing response content")
                except json.JSONDecodeError:
                    continue
        
        # Content extraction fallback
        print("🧠 Attempting content extraction...")
        extracted_data = enhanced_content_extraction(cleaned_text)
        if extracted_data and extracted_data.get("response"):
            return extracted_data
        
        print("🔧 Using manual field extraction as fallback...")
        return manual_field_extraction(cleaned_text)
    
    except Exception as e:
        print(f"❌ JSON extraction error: {e}")
        return create_fallback_response(response_text)

def enhanced_content_extraction(text):
    """Enhanced content extraction"""
    try:
        print("🧠 Performing content extraction...")
        
        result = {
            "response": "",
            "code_blocks": [],
            "links": [],
            "suggested_questions": []
        }
        
        response_text = text
        
        # Remove code blocks first and save them
        code_pattern = r'```(\w+)?\s*(.*?)```'
        code_matches = re.findall(code_pattern, text, re.DOTALL)
        for match in code_matches:
            language = match[0] if match[0] else "text"
            code = match[1].strip()
            if code:
                result["code_blocks"].append({
                    "language": language,
                    "code": code,
                    "description": f"Code block in {language}"
                })
                response_text = re.sub(code_pattern, '', response_text, count=1, flags=re.DOTALL)
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        url_matches = re.findall(url_pattern, text)
        for url in url_matches:
            if url not in [link["url"] for link in result["links"]]:
                result["links"].append({
                    "url": url,
                    "title": extract_title_from_context(url, text),
                    "description": "Extracted URL from response"
                })
        
        response_text = re.sub(r'\n\s*\n', '\n\n', response_text).strip()
        
        if not response_text or len(response_text) < 20:
            lines = text.split('\n')
            substantial_lines = [line.strip() for line in lines if len(line.strip()) > 10]
            if substantial_lines:
                response_text = '\n'.join(substantial_lines[:10])
        
        result["response"] = response_text if response_text else "AI response received but content could not be extracted properly."
        
        result["suggested_questions"] = [
            "Can you explain this in more detail?",
            "What should I do next?",
            "Are there any potential issues?",
            "How can I improve this further?",
            "What are the best practices here?",
            "Can you provide alternatives?"
        ]
        
        print(f"✅ Content extraction completed - Response length: {len(result['response'])}")
        return result
        
    except Exception as e:
        print(f"❌ Content extraction error: {e}")
        return None

def clean_json_string(json_str):
    """JSON string cleaning"""
    if not json_str:
        return json_str
    
    json_str = json_str.strip()
    
    # Remove markdown code blocks
    json_str = re.sub(r'^```(?:json)?\s*', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'\s*```$', '', json_str, flags=re.MULTILINE)
    
    # Fix common quote issues
    json_str = json_str.replace('"', '"').replace('"', '"')
    json_str = json_str.replace(''', "'").replace(''', "'")
    
    # Fix newlines in strings
    json_str = re.sub(r'(?<!\\)\\n', '\\\\n', json_str)
    
    # Remove any text before first { or after last }
    first_brace = json_str.find('{')
    last_brace = json_str.rfind('}')
    if first_brace != -1 and last_brace != -1:
        json_str = json_str[first_brace:last_brace + 1]
    
    return json_str

def fix_common_json_issues(json_str):
    """JSON issue fixing"""
    try:
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix unescaped newlines in strings
        json_str = re.sub(r'(?<!\\)\n(?=\s*")', '\\n', json_str)
        
        # Fix unquoted keys
        json_str = re.sub(r'(\w+)(\s*:)', r'"\1"\2', json_str)
        
        # Fix unquoted string values
        json_str = re.sub(r':\s*([^"{\[\d\-][^,}\]]*?)(\s*[,}\]])', r': "\1"\2', json_str)
        
        return json_str
    except Exception as e:
        print(f"❌ JSON fix error: {e}")
        return json_str

def manual_field_extraction(text):
    """Manual extraction as fallback"""
    try:
        print("🔧 Performing manual field extraction...")
        
        result = {
            "response": text,
            "code_blocks": [],
            "links": [],
            "suggested_questions": [
                "Can you walk me through this step by step?",
                "How do I troubleshoot any issues here?",
                "What are the best practices for this?",
                "How can I improve my workflow?",
                "What should I learn more about?",
                "Are there better tools for this task?"
            ]
        }
        
        # Code block extraction
        code_matches = re.findall(r'```(\w+)?\s*(.*?)```', text, re.DOTALL)
        for match in code_matches:
            result["code_blocks"].append({
                "language": match[0] or "text",
                "code": match[1].strip(),
                "description": f"Extracted code block"
            })
        
        # URL extraction
        url_matches = re.findall(r'https?://[^\s<>"]+', text)
        for url in url_matches:
            result["links"].append({
                "url": url,
                "title": "Extracted Link",
                "description": "URL found in response"
            })
        
        if len(result["response"]) > 3000:
            result["response"] = result["response"][:3000] + "..."
        
        print(f"✅ Manual extraction completed - Response length: {len(result['response'])}")
        return result
        
    except Exception as e:
        print(f"❌ Manual extraction error: {e}")
        return create_fallback_response(text)

def validate_and_fix_json_structure(data):
    """Validate and fix JSON structure"""
    if not isinstance(data, dict):
        return create_fallback_response(str(data))
    
    required_fields = ["response", "code_blocks", "links", "suggested_questions"]
    
    for field in required_fields:
        if field not in data:
            if field == "response":
                content = (data.get("content", "") or 
                          data.get("text", "") or 
                          data.get("message", "") or
                          data.get("answer", "") or
                          str(data))
                data[field] = content
            else:
                data[field] = []
        elif field == "response" and (not data[field] or len(str(data[field]).strip()) < 10):
            for key, value in data.items():
                if isinstance(value, str) and len(value.strip()) > 10:
                    data[field] = value
                    break
        elif not isinstance(data[field], list) and field != "response":
            data[field] = []
    
    if not isinstance(data["response"], str):
        data["response"] = str(data["response"])
    
    if not data["response"] or len(data["response"].strip()) < 10:
        data["response"] = "AI response was received but the content could not be properly extracted. Please try asking your question again."
    
    # Validate code blocks
    valid_code_blocks = []
    for block in data.get("code_blocks", []):
        if isinstance(block, dict):
            valid_block = {
                "language": str(block.get("language", "text")),
                "code": str(block.get("code", "")),
                "description": str(block.get("description", "Code block"))
            }
            valid_code_blocks.append(valid_block)
    data["code_blocks"] = valid_code_blocks
    
    # Validate links
    valid_links = []
    for link in data.get("links", []):
        if isinstance(link, dict) and "url" in link:
            valid_link = {
                "url": str(link["url"]),
                "title": str(link.get("title", "Link")),
                "description": str(link.get("description", ""))
            }
            valid_links.append(valid_link)
    data["links"] = valid_links
    
    # Validate suggested questions
    valid_questions = []
    for question in data.get("suggested_questions", []):
        if isinstance(question, str) and question.strip():
            valid_questions.append(question.strip())
    
    if not valid_questions:
        valid_questions = [
            "How do I understand this better?",
            "What are the practical next steps?",
            "Can you explain the key concepts?",
            "How do I troubleshoot issues?",
            "What are the best practices here?",
            "How can I optimize my approach?"
        ]
    
    data["suggested_questions"] = valid_questions[:6]
    
    print(f"✅ Validation completed - Response length: {len(data['response'])}")
    return data

def create_fallback_response(text):
    """Fallback response"""
    clean_text = str(text).strip() if text else ""
    
    if len(clean_text) < 10:
        clean_text = "AI response was received but could not be processed properly. Please try asking your question again."
    
    return {
        "response": clean_text[:3000],
        "code_blocks": [],
        "links": [],
        "suggested_questions": [
            "Can you explain this step by step?",
            "How do I implement this solution?",
            "What are the best practices here?",
            "Are there any alternatives I should consider?",
            "What potential issues should I watch for?",
            "How can I optimize this approach?"
        ]
    }

def extract_title_from_context(url, text):
    """Extract a title for a URL from surrounding context"""
    try:
        url_index = text.find(url)
        if url_index != -1:
            context_start = max(0, url_index - 100)
            context = text[context_start:url_index].strip()
            context_words = context.split()[-5:]
            if context_words:
                return " ".join(context_words).rstrip(':-([')
        
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            return domain_match.group(1)
        
        return "Reference Link"
    except Exception:
        return "Link"

if __name__ == "__main__":
    print("🤖 Screen-Aware AI Service Module")
    
    # Test basic functionality
    print("Testing screen-aware AI service...")
    test_response = get_ai_response("Hello, how are you?", None, "", None, "")
    if isinstance(test_response, dict) and "error" in test_response:
        print(f"❌ Test failed: {test_response['error']}")
    else:
        print(f"✅ Test successful: {str(test_response)[:100]}...")