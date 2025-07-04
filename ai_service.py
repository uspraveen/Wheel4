#!/usr/bin/env python3
"""
Wheel4 - AI Service
Robust OpenAI API integration with JSON responses
"""

import openai
import base64
import json
import re
from database import get_api_key
from prompts import load_prompts

def get_ai_response(question, screenshot_bytes, context=""):
    """Get AI response with structured output"""
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ No API key found")
        return {"error": "No API key configured. Please set up your OpenAI API key."}
    
    # Initialize OpenAI client
    try:
        client = openai.OpenAI(api_key=api_key)
    except Exception as e:
        print(f"❌ OpenAI client error: {e}")
        return {"error": "Invalid API key. Please check your configuration."}
    
    # Load prompts
    system_prompt, user_prompt_template = load_prompts()
    
    # Build enhanced system prompt with context
    enhanced_system_prompt = system_prompt
    if context:
        enhanced_system_prompt += f"\n\nConversation context:\n{context}"
    
    # Prepare messages
    messages = [
        {"role": "system", "content": enhanced_system_prompt}
    ]
    
    # Format user message
    user_content = [
        {"type": "text", "text": user_prompt_template.format(question=question)}
    ]
    
    # Add screenshot if available
    if screenshot_bytes:
        try:
            # Encode screenshot to base64
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"
                }
            })
            print("🖼️  Screenshot attached to request")
        except Exception as e:
            print(f"⚠️  Screenshot encoding failed: {e}")
    else:
        print("⚠️  No screenshot available")
    
    messages.append({"role": "user", "content": user_content})
    
    # Make API call with optimized parameters
    try:
        print("🤖 Calling OpenAI API...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        
        ai_response = response.choices[0].message.content
        
        # Log usage for debugging
        usage = response.usage
        print(f"✅ AI response received ({len(ai_response)} chars)")
        print(f"📊 Tokens used: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")
        
        return ai_response
        
    except openai.RateLimitError as e:
        print(f"❌ OpenAI rate limit exceeded: {e}")
        return {"error": "Rate limit exceeded. Please wait a moment and try again."}
        
    except openai.AuthenticationError as e:
        print(f"❌ OpenAI authentication failed: {e}")
        return {"error": "Invalid API key. Please check your OpenAI API key configuration."}
        
    except openai.BadRequestError as e:
        print(f"❌ OpenAI bad request: {e}")
        return {"error": "Invalid request. The image might be too large or corrupted."}
        
    except openai.APIConnectionError as e:
        print(f"❌ OpenAI connection error: {e}")
        return {"error": "Unable to connect to OpenAI. Please check your internet connection."}
        
    except Exception as e:
        print(f"❌ Unexpected OpenAI error: {e}")
        return {"error": f"Error: {str(e)}"}

def test_api_key(api_key):
    """Test if API key is valid with minimal cost"""
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Very simple test call to minimize cost
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        
        print("✅ API key test successful")
        return True
        
    except openai.AuthenticationError:
        print("❌ API key test failed: Invalid authentication")
        return False
        
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

def extract_json_from_response(text):
    """Extract JSON from response text using multiple strategies"""
    # Strategy 1: Try to parse the entire response as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Look for JSON block markers
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{.*?\})'
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    # Strategy 3: Clean up common JSON issues and try again
    cleaned_text = text.strip()
    
    # Remove common prefixes
    prefixes_to_remove = [
        "Here's the JSON response:",
        "Here is the JSON response:",
        "Response:",
        "JSON:",
        "```json",
        "```"
    ]
    
    for prefix in prefixes_to_remove:
        if cleaned_text.startswith(prefix):
            cleaned_text = cleaned_text[len(prefix):].strip()
    
    # Remove trailing ```
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3].strip()
    
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 4: Return None if all strategies fail
    return None