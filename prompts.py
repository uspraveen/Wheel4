#!/usr/bin/env python3
"""
Wheel4 - Simple Universal AI Prompts
One prompt that handles everything naturally
"""

import os
import json
from datetime import datetime

PROMPTS_FILE = "prompts.md"

# Universal system prompt that handles everything
DEFAULT_SYSTEM_PROMPT = """# ROLE
You are Wheel4, a helpful AI assistant that can see the user's screen and provide contextual assistance. You ALWAYS acknowledge what you can see on their screen and provide relevant, helpful responses based on both their question AND the visual context.

# CORE BEHAVIOR
- **ALWAYS reference what you see on screen** - acknowledge the current context, applications, content, etc.
- **Combine screen analysis with user requests** - answer their question while being aware of what they're looking at
- **Be proactive and helpful** - suggest relevant next steps based on what you observe
- **Provide complete solutions** - give full implementations, complete code, detailed explanations
- **For quizes and questions on screen, just answer them** - no need to ask for clarification, just provide the answer based on what you see
# RESPONSE REQUIREMENTS
You MUST respond with ONLY a valid JSON object in this exact format:

```json
{
    "response": "Your helpful response that ALWAYS references what you see on screen, with **bold** and *italic* markdown formatting",
    "code_blocks": [
        {
            "language": "python",
            "code": "# Complete, commented code here - always provide FULL implementations",
            "description": "Clear explanation of what this code accomplishes"
        }
    ],
    "links": [
        {
            "url": "https://example.com",
            "title": "Relevant Resource Title", 
            "description": "Why this resource is helpful for the current context"
        }
    ],
    "suggested_questions": [
        "Context-specific follow-up based on what you see on screen",
        "How can I optimize this code/workflow?",
        "What's the next step in this process?",
        "Are there any issues I should watch for?",
        "How can I improve this implementation?",
        "What are the best practices here?"
    ]
}
```

# FORMATTING RULES
- Response must be ONLY the JSON object - no other text before or after
- All 4 fields are required: response, code_blocks, links, suggested_questions  
- Use empty arrays [] if no code blocks or links are needed
- Always provide 4-6 contextual suggested_questions based on what you see
- Escape all quotes properly in JSON strings
- Use markdown formatting (*italic*, **bold**) in response text only
- Put code in code_blocks array with proper language and description
- Put URLs in links array with title and description

# RESPONSE STYLE
- **If what you see is not a quiz/exam/something like that - Always start by acknowledging what you see** - "I can see you're working in VS Code...", "I notice you're watching a YouTube video about...", etc.
- **For quizzes or questions on screen** - just start with the full correctanswer based on what you see, no need to ask for clarification provide explanations towards the end. Give the direct answer with 0 extra text.
- **Be concise and contextually helpful** - provide direc tassistance that's relevant to what's on screen
- **Give complete solutions** - full code implementations, not snippets
- **Be proactive** - suggest improvements, next steps, potential issues
- **Be conversational but informative** - friendly but focused on being useful

# SPECIFIC SCENARIOS
- **When user says "hi" or greets you**: Acknowledge what you see on screen and offer contextual help
- **When user submits empty/minimal input**: Analyze what's on screen and provide relevant assistance, solutions, or explanations
- **When user asks specific questions**: Answer while referencing the screen context
- **When you see code**: Provide complete implementations, not just snippets. Include code usage aswell.
- **When you see errors**: Identify the issue and provide full solutions
- **When you see applications**: Acknowledge the tool and provide relevant workflow assistance

# GUIDELINES
- NEVER ignore the screen context - always reference what you see
- Provide COMPLETE code solutions, not partial snippets
- Give actionable, specific advice based on the visual context  
- Suggest relevant next steps and improvements
- Make suggested questions specific to what's currently on screen"""

# Simple user prompt template
DEFAULT_USER_PROMPT = """I can see my screen. {question_text}

{context_section}

Please help me with this while acknowledging what you can see on my screen."""

def get_system_prompt(custom_instructions=""):
    """Get system prompt with optional custom instructions"""
    base_prompt = DEFAULT_SYSTEM_PROMPT
    
    if custom_instructions and custom_instructions.strip():
        # Add custom instructions 
        custom_section = f"""

# CUSTOM INSTRUCTIONS
{custom_instructions.strip()}

Follow these custom instructions while maintaining the response format above."""
        
        # Insert custom instructions before formatting rules
        base_prompt = base_prompt.replace("# FORMATTING RULES", custom_section + "\n\n# FORMATTING RULES")
    
    return base_prompt

def get_user_prompt(question, context=""):
    """Get simple user prompt that always expects screen context"""
    context_section = ""
    if context and context.strip():
        context_section = f"""
Previous conversation:
{context.strip()[:500]}"""
    
    # Handle empty or minimal questions
    if not question or question.strip() == "":
        question_text = "Please analyze what's on my screen and provide helpful assistance."
    else:
        question_text = f'My request: "{question}"'
    
    return DEFAULT_USER_PROMPT.format(
        question_text=question_text,
        context_section=context_section
    )

def format_user_prompt_with_personalization(question, context="", template_key=None, custom_instructions=""):
    """Simple wrapper for compatibility"""
    return get_user_prompt(question, context)

def get_personalized_prompts(template_key=None, custom_instructions=""):
    """Get prompts with custom instructions"""
    system_prompt = get_system_prompt(custom_instructions)
    user_template = DEFAULT_USER_PROMPT
    
    if custom_instructions:
        print(f"✅ Applied custom instructions ({len(custom_instructions)} chars)")
    
    return system_prompt, user_template

def validate_prompt_structure():
    """Validate prompt structure"""
    errors = []
    
    if "# ROLE" not in DEFAULT_SYSTEM_PROMPT:
        errors.append("System prompt missing ROLE section")
    if "# RESPONSE REQUIREMENTS" not in DEFAULT_SYSTEM_PROMPT:
        errors.append("System prompt missing RESPONSE REQUIREMENTS section")
    if "suggested_questions" not in DEFAULT_SYSTEM_PROMPT:
        errors.append("System prompt missing suggested_questions in JSON structure")
    if "{question}" not in DEFAULT_USER_PROMPT:
        errors.append("User prompt missing question placeholder")
    
    if errors:
        print("❌ Prompt validation errors:")
        for error in errors:
            print(f"   • {error}")
        return False
    
    return True

def create_prompts_file():
    """Create prompts.md file"""
    content = f"""# Wheel4 Screen-Aware AI Prompts

## Screen-Aware System Prompt
{DEFAULT_SYSTEM_PROMPT}

## User Prompt Template
{DEFAULT_USER_PROMPT}

---

## Design Philosophy

### Always Screen-Aware
- **Screenshot is ALWAYS provided** - every interaction includes screen context
- **Always acknowledge what you see** - reference the current screen, applications, content
- **Contextual responses** - combine user requests with visual analysis
- **Proactive assistance** - suggest relevant help based on screen content

### Usage Scenarios
- **"hi" while in VS Code** → "Hi! I can see you're working in VS Code on a Python project. How can I help?"
- **Empty enter on coding problem** → Analyzes code and provides complete solution
- **"explain this" on YouTube video** → Explains what's visible in the video
- **Web search mode** → Searches web instead of analyzing screen

### Key Features
- **Always contextual**: Every response references screen content
- **Complete solutions**: Full code implementations, not snippets
- **Proactive**: Suggests improvements and next steps
- **Consistent format**: Same JSON response structure
- **Custom instructions**: Session-based behavior modification

### Response Quality
- Acknowledge current screen context first
- Provide complete, actionable solutions
- Reference specific UI elements, code, content seen
- Suggest contextually relevant follow-up questions
- Give full implementations and detailed explanations
"""
    
    try:
        with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📝 Created {PROMPTS_FILE}")
    except Exception as e:
        print(f"❌ Failed to create prompts file: {e}")

def get_prompt_stats():
    """Get statistics about current prompts"""
    return {
        'system_prompt_length': len(DEFAULT_SYSTEM_PROMPT),
        'user_prompt_length': len(DEFAULT_USER_PROMPT),
        'has_role_definition': '# ROLE' in DEFAULT_SYSTEM_PROMPT,
        'has_json_structure': 'suggested_questions' in DEFAULT_SYSTEM_PROMPT,
        'validation_passed': validate_prompt_structure()
    }

# Backward compatibility functions
def get_available_templates():
    """Returns empty list"""
    return []

def get_template_by_key(template_key):
    """Returns None"""
    return None

def load_enhanced_prompts():
    """Backward compatibility"""
    return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT

def get_optimized_prompts(has_context=False):
    """Backward compatibility"""
    return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT

def format_user_prompt_with_context(question, context=""):
    """Backward compatibility"""
    return get_user_prompt(question, context)

# Remove all the detection logic - not needed!
def is_general_chat_query(question):
    """Removed - not needed with universal prompt"""
    return True

if __name__ == "__main__":
    print(f"🚀 Wheel4 Screen-Aware AI Prompts")
    print(f"📝 Always acknowledges screen context - no detection logic needed")
    
    if validate_prompt_structure():
        print("✅ Prompt validation passed")
        
        stats = get_prompt_stats()
        print(f"📊 Prompt stats:")
        print(f"   • System prompt: {stats['system_prompt_length']} chars")
        print(f"   • User prompt: {stats['user_prompt_length']} chars") 
        print(f"   • Role definition: {'✅' if stats['has_role_definition'] else '❌'}")
        print(f"   • JSON structure: {'✅' if stats['has_json_structure'] else '❌'}")
    else:
        print("❌ Prompt validation failed")
    
    create_prompts_file()
    
    print("🎉 Screen-aware prompts ready!")
    print("   • Always acknowledges screen context")
    print("   • Contextual responses to any input") 
    print("   • Empty enter = automatic screen analysis")
    print("   • Complete solutions and implementations")