# Wheel4 - Simple On-Screen AI Brain

A clean, fast AI assistant that sees your screen and provides contextual help with beautiful glassmorphism UI.

## ✨ Features

- 🧠 **AI Vision**: Advanced screen analysis with GPT-4o
- 🎨 **Clean UI**: Simple glassmorphism design without clutter
- ⌨️ **Smart Input**: Shift+Enter for new lines, Enter to send
- 💾 **Session Memory**: Conversation history within sessions
- 🔄 **Data Reset**: Clear API keys and start fresh anytime
- 🔐 **Secure**: Local API key storage
- 🚀 **Fast**: Optimized for quick responses

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **Setup API key:**
   - Clean setup dialog on first run
   - Get yours at: https://platform.openai.com/api-keys

4. **Use hotkeys:**
   - `Ctrl + \` - Toggle AI Brain visibility
   - `Ctrl + Enter` - Ask a question about what you see

## 💡 How It Works

1. **Activate**: Press `Ctrl + Enter` to open question input
2. **Ask**: Type your question (Shift+Enter for new lines)
3. **Quick Questions**: Click preset buttons for common queries
4. **AI Analysis**: AI captures and analyzes your screen
5. **Smart Response**: Get contextual help with conversation memory
6. **Auto-minimize**: Interface hides automatically after response

## 🏗️ Clean Architecture

- **Simple Threading**: Background AI processing without UI blocking
- **Session Management**: Each run creates a new session
- **Context Aware**: Remembers conversation within session
- **Error Handling**: Robust error recovery

## 📁 File Structure

```
wheel4/
├── main.py              # Simple application entry point
├── ui.py                # Clean overlay interface
├── ai_service.py        # OpenAI integration
├── database.py          # SQLite with session management
├── screen_capture.py    # Optimized screen capture
├── hotkeys.py           # Global hotkey handling
├── prompts.py           # Dynamic prompt loading
├── config.py            # Configuration settings
├── prompts.md           # Editable AI prompts
└── requirements.txt     # Python dependencies
```

## 🎛️ Customization

### Reset Data
- Click "Reset" button in UI to clear API keys and data
- Useful for switching accounts or starting fresh

### Hotkeys
Edit `config.py` to change hotkey combinations:
```python
TOGGLE_HOTKEY = "<ctrl>+\\"
QUESTION_HOTKEY = "<ctrl>+<enter>"
```

### AI Behavior
Edit `prompts.md` to customize AI responses:
- **System Prompt**: AI personality and capabilities
- **User Prompt**: Question formatting template

## 🗃️ Database Schema

### Sessions Table
- Each app run creates a new session
- Tracks start and end times

### Interactions Table
- Question-response pairs with timestamps
- Linked to session for context

### API Keys Table
- Secure local storage of OpenAI API keys

## 🔧 Key Features

### Session Memory
- AI remembers previous conversations within session
- Context automatically included in new requests
- Fresh session on each app restart

### Smart Input
- **Enter**: Send question immediately
- **Shift+Enter**: Add new line to question
- **Quick buttons**: Common question shortcuts
- **Auto-focus**: Input ready when activated

### Clean UI
- Simple glassmorphism effects
- Cyan color scheme for clarity
- No overwhelming gradients or animations
- Focus on functionality over flashy design

## 🐛 Troubleshooting

**No API key dialog?**
- Click "Reset" button to clear existing data
- Fresh setup dialog will appear

**UI not responding?**
- Fixed Qt threading issues in this version
- All UI updates happen on main thread

**Hotkeys not working?**
- Run as administrator (Windows)
- Grant accessibility permissions (macOS)

**Slow responses?**
- Optimized screenshot capture
- Simplified architecture for speed
- Check OpenAI API key and credits

## 🔒 Privacy & Security

- All data stored locally in SQLite
- API keys stored securely in database
- Screenshots only sent when you ask questions
- No external data collection
- Easy data reset functionality

## 🎯 Design Philosophy

This version focuses on:
- **Simplicity**: Clean, uncluttered interface
- **Reliability**: Robust threading without complexity
- **Speed**: Optimized for quick responses
- **Usability**: Intuitive interactions and controls