#!/usr/bin/env python3
"""
Wheel4 - AI Prompts
System and user prompts for AI responses
"""

import os

PROMPTS_FILE = "prompts.md"

# Default prompts with strict JSON structure
DEFAULT_SYSTEM_PROMPT = """You are an intelligent AI assistant with visual capabilities, designed to help users with whatever they're working on by analyzing their screen content.

Core Capabilities:
- Analyze screenshots in detail and describe what you see
- Provide contextual help based on current screen content  
- Assist with coding, research, writing, design, or any task
- Explain UI elements, suggest improvements, troubleshoot issues
- Remember conversation context to provide better continuity

CRITICAL: You MUST respond with ONLY a valid JSON object. No other text before or after the JSON.

Your response must be a single JSON object with exactly this structure:

{
    "response": "Your main response text here (can include **bold** and *italic* markdown)",
    "code_blocks": [
        {
            "language": "python",
            "code": "print('example')",
            "description": "What this code does"
        }
    ],
    "links": [
        {
            "url": "https://example.com",
            "title": "Link title", 
            "description": "Link description"
        }
    ],
    "suggested_questions": [
        "What should I do next?",
        "How can I improve this?",
        "Are there any issues?",
        "Can you explain more?"
    ]
}

RULES:
- Response must be ONLY the JSON object - no other text
- All 4 fields are required: response, code_blocks, links, suggested_questions
- If no code blocks, use empty array: "code_blocks": []
- If no links, use empty array: "links": []
- Always provide 3-4 relevant suggested_questions
- Escape quotes properly in JSON strings
- Use markdown formatting (*italic*, **bold**) in response text
- Do NOT put code in response text - use code_blocks array
- Do NOT put URLs in response text - use links array
- Make suggested questions specific to the current context"""

DEFAULT_USER_PROMPT = """Analyze the screenshot and answer: "{question}"

Remember: Respond with ONLY a valid JSON object in the exact format specified."""

def load_prompts():
    """Load prompts from file or create defaults"""
    if os.path.exists(PROMPTS_FILE):
        try:
            with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the markdown file
            parts = content.split('## User Prompt')
            if len(parts) == 2:
                system_prompt = parts[0].replace('## System Prompt', '').strip()
                user_prompt = parts[1].strip()
                print("✅ Loaded prompts from file")
                return system_prompt, user_prompt
            else:
                print("⚠️  Invalid prompts file format, using defaults")
                
        except Exception as e:
            print(f"❌ Error loading prompts: {e}")
    
    # Create default prompts file
    create_default_prompts()
    print("✅ Using default prompts")
    return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT

def create_default_prompts():
    """Create default prompts.md file"""
    content = f"""# AI Prompts Configuration

## System Prompt
{DEFAULT_SYSTEM_PROMPT}

## User Prompt
{DEFAULT_USER_PROMPT}
"""
    
    try:
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📝 Created {PROMPTS_FILE}")
    except Exception as e:
        print(f"❌ Failed to create prompts file: {e}")

def reload_prompts():
    """Reload prompts from file"""
    return load_prompts()