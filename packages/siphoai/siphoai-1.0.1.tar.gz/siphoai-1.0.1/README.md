# Sipho AI - Voice Command Assistant

An AI-powered voice command assistant for desktop automation that uses natural language processing to execute commands on your PC. Built  "alternative_message": "Message when app is missing"

## Command Examplesth Flask API and OpenAI integration for intelligent conversation handling.

[![PyPI version](https://badge.fury.io/py/siphoai.svg)](https://badge.fury.io/py/siphoai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

## Features

- **AI-Powered Conversations**: Natural language processing with OpenAI integration
- **Smart Command Detection**: Automatically distinguishes between commands and conversations
- **REST API**: Flask-based API for web and mobile integration
- **JSON-Based Commands**: All commands stored in `commands.json` for easy management
- **Voice Confirmation**: Sensitive commands require confirmation for safety
- **Third-Party App Detection**: Automatically checks if required applications are installed
- **System Checker**: Comprehensive system scanning and installation suggestions
- **Web Integration**: Open websites, perform searches, launch applications
- **System Control**: Shutdown, restart, lock, volume control, and more

## Quick Start

### Installation

```bash
pip install siphoai
```

### Basic Usage

```bash
# Start the API server
siphoai

# View available commands
siphoai help-commands

# Test a command
siphoai test "open youtube"
```

The server will start on `http://localhost:5000` with the following endpoints:
- `POST /api/command` - Execute commands & handle conversations
- `GET /api/help` - Get available commands  
- `GET /api/status` - Server status

## Configuration

Create a `.env` file for AI features:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false
```

Get your free API key from [OpenRouter](https://openrouter.ai/keys).

## Enhanced Features

### AI Integration
- Powered by OpenAI through OpenRouter API
- Natural conversation handling
- Smart command vs conversation detection
- Context-aware responses
- Enhanced command feedback

### Voice Confirmation
Sensitive commands (shutdown, restart, lock) require confirmation:
- Server asks "Are you sure you want to [action]?"
- Respond with confirmation to proceed
- Automatic timeout for safety

### Third-Party App Detection
- Automatically detects if required applications are installed
- Provides download links for missing apps
- Supports environment variable expansion
- Installation instructions included

### System Checker
Built-in utility to scan your system:
- Detects installed applications
- Checks voice command requirements  
- Generates installation suggestions
- Comprehensive system reports

## Package Structure

```
siphoai/
├── __init__.py           # Package initialization
├── app.py               # Main Flask application
├── cli.py               # Command-line interface
├── data/
│   └── commands.json    # Command configurations
└── utils/
    ├── command_manager.py # Command management tools
    └── system_checker.py  # System scanning utilities
```

## Supported Commands

The package comes with pre-configured commands in multiple categories:

### Web Commands
- **Social Media**: "Open YouTube", "Open Facebook", "Open Twitter", "Open Instagram"
- **Professional**: "Open LinkedIn", "Open GitHub"
- **Search**: "Open Google", "Search for [term]"
- **Entertainment**: "Open Netflix"

### Application Commands
- **System Tools**: "Open Calculator", "Open Notepad", "Open Paint"
- **File Management**: "Open File Explorer", "Open Command Prompt"
- **System**: "Open Task Manager", "Open Control Panel", "Open Settings"
- **Development**: "Open Visual Studio Code", "Open PowerShell"

### System Commands
- **Power**: "Shutdown computer", "Restart computer", "Sleep computer"
- **Security**: "Lock computer"
- **Control**: "Cancel shutdown", "Minimize all windows"

### Information Commands
- **Time**: "What time is it?"
- **Date**: "What date is it?" or "Today"

### Volume Control (requires nircmd)
- **Audio**: "Volume up", "Volume down", "Mute"

### Media Commands  
- **Players**: "Open music player", "Open photos"

### Vision Commands
- **Screenshot**: "Take screenshot", "Analyze screen"
- **AI Analysis**: "What's on my screen?", "Describe my screen"

## Adding New Commands

### Method 1: Using Command Manager (Recommended)
1. Run `launcher.bat` and select option 2
2. Choose the type of command to add
3. Follow the interactive prompts
4. Save your changes

### Method 2: Edit JSON Directly
Edit `commands.json` to add new commands. Each command has this structure:

```json
{
  "triggers": ["phrase1", "phrase2"],
  "action": "action_type",
  "response": "What the app will say",
  "url": "https://example.com",  // For web commands
  "command": ["executable", "arg1", "arg2"]  // For app/system commands
}
```

### Available Action Types:
- `web_open` - Opens a URL in the browser
- `run_application` - Runs an application/executable
- `system_command` - Executes a system command
- `volume_control` - Controls system volume
- `get_time` - Gets current time
- `get_date` - Gets current date
- `web_search` - Performs a web search
- `show_help` - Shows help information
- `exit_app` - Exits the application

### Additional Properties:
- `requires_confirmation` - Set to `true` for sensitive commands
- `confirmation_message` - Custom confirmation question
- `requires_third_party` - Object with third-party app information:
  - `app_name` - Display name of the application
  - `executable` - Path or name of executable to check
  - `download_url` - Where to download the app
  - `install_instructions` - How to install the app
  - `alternative_message` - Message when app is missing

## Command Examples

### Basic Command
```json
{
  "triggers": ["open notepad", "notepad"],
  "action": "run_application",
  "command": ["notepad.exe"],
  "response": "Opening Notepad"
}
```

### Command with Confirmation
```json
{
  "triggers": ["shutdown computer"],
  "action": "system_command",
  "command": ["shutdown", "/s", "/t", "30"],
  "response": "Shutting down computer",
  "requires_confirmation": true,
  "confirmation_message": "Are you sure you want to shutdown?"
}
```

### Third-Party App Command
```json
{
  "triggers": ["open discord"],
  "action": "run_application",
  "command": ["C:\\Users\\%USERNAME%\\AppData\\Local\\Discord\\Discord.exe"],
  "response": "Opening Discord",
  "requires_third_party": {
    "app_name": "Discord",
    "executable": "C:\\Users\\%USERNAME%\\AppData\\Local\\Discord\\Discord.exe",
    "download_url": "https://discord.com/download",
    "install_instructions": "Download and install Discord from the official website.",
    "alternative_message": "Discord is not installed."
  }
}
```

## API Usage

### Command Execution
```python
import requests

# Execute a command
response = requests.post('http://localhost:5000/api/command', 
                        json={'command': 'open youtube'})
print(response.json())

# Handle conversation
response = requests.post('http://localhost:5000/api/command',
                        json={'command': 'how are you today?'})
print(response.json())
```

### JavaScript Integration
```javascript
// Execute command from web app
async function executeCommand(command) {
    const response = await fetch('http://localhost:5000/api/command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: command})
    });
    return await response.json();
}

// Usage
executeCommand('open calculator').then(result => console.log(result));
```

### Response Format
```json
{
  "success": true,
  "message": "Opening YouTube",
  "action": "web_open", 
  "url": "https://www.youtube.com",
  "ai_message": "I've opened YouTube for you!",
  "processing_time": 0.123
}
```

## Requirements

- **Python**: 3.7 or higher
- **OS**: Windows, macOS, or Linux (some commands are OS-specific)
- **Internet**: Required for AI features and web commands
- **Optional**: Microphone for voice input (when integrated with speech recognition)

## Command Management Tools

### Command Manager (`command_manager.py`)
- Add new commands interactively
- List all current commands
- Save/reload command configurations
- User-friendly interface for command management

### Backup Manager (`backup_manager.py`)
- Create timestamped backups of your commands
- Restore from previous backups
- Export commands to readable text format
- List all available backups

## Examples

### Adding a New Web Command
```json
{
  "triggers": ["open stackoverflow", "stack overflow"],
  "action": "web_open",
  "url": "https://stackoverflow.com",
  "response": "Opening Stack Overflow"
}
```

### Adding a New Application Command
```json
{
  "triggers": ["open discord", "discord"],
  "action": "run_application",
  "command": ["C:\\Users\\YourName\\AppData\\Local\\Discord\\Discord.exe"],
  "response": "Opening Discord"
}
```

## Notes

- The app uses Google's speech recognition service, so an internet connection is required
- For volume control commands, you may need to install nircmd (optional)
- Speak clearly and wait for the app to process your command before giving the next one
- Say "help" to hear the available commands
- Press Ctrl+C to force quit the application

## Troubleshooting

- If you get audio-related errors, make sure your microphone is working and properly configured
- If speech recognition isn't working, check your internet connection
- The app adjusts for ambient noise when it starts, so wait for the ready message before speaking

## Security Note

This app can execute system commands like shutdown and restart. Use with caution and only run commands you understand.
