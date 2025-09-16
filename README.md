# Otto - OpenAI Voice Agent for PC Control

Otto is a Python application that creates a voice assistant powered by OpenAI's API to control your PC using voice commands. It allows for continuous speech-to-speech interaction without requiring wake words.

## Features

- **Voice Control**: Continuous speech-to-speech interaction
- **PC Control**:
  - Open applications
  - Click at specific screen positions
  - Type text using the keyboard
  - Press keyboard keys and combinations
  - Get screen information

## Implementation Options

This repository contains two implementations:

1. **Custom WebSocket Implementation** (`otto_agent.py`): A custom implementation using OpenAI's WebSocket API directly.
2. **OpenAI Agents SDK Implementation** (`otto_agent_sdk.py`): A cleaner implementation using the official OpenAI Agents SDK.

The SDK implementation is recommended for new projects as it provides a more streamlined approach.

## Setup

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Microphone and speakers

### Installation

1. Clone or download this repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
   
   If you're using the OpenAI Agents SDK implementation, make sure to install these additional packages:
   ```
   pip install openai-agents websockets
   ```

4. Create a `.env` file in the project directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Using the OpenAI Agents SDK Implementation (Recommended)

Run the application:

```
python otto_agent_sdk.py
```

### Using the Custom WebSocket Implementation

Run the application:

```
python otto_agent.py
```

### Testing

For a simple test of the SDK implementation without PC control features:

```
python test_otto_sdk.py
```

## Microphone Configuration

The application requires a properly configured microphone to work. The updated SDK implementation now includes microphone testing capabilities:

1. When you start the application, it will:
   - List all available audio devices
   - Test your microphone by recording for 3 seconds
   - Show a warning if no audio is detected

2. If your microphone isn't working:
   - Check if the correct microphone is selected as your default input device in Windows
   - Make sure your microphone isn't muted
   - Ensure your microphone has the necessary permissions
   - Check the audio levels in your system settings

3. To manually test your microphone:
   - Run `python test_otto_sdk.py` which now includes a microphone test
   - Speak during the 3-second test to verify audio detection

## Example Commands

- "Open Chrome"
- "Click on the File menu"
- "Type hello world"
- "Press Control plus S to save"
- "What's the resolution of my screen?"

## Safety Features

- PyAutoGUI failsafe: Move your mouse to the top-left corner of the screen to abort any automated actions
- 0.5-second pause between PyAutoGUI commands for safety

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   - For the SDK implementation, make sure you have `openai-agents` and `websockets` installed:
     ```
     pip install openai-agents websockets
     ```

2. **API Key Issues**:
   - Ensure your OpenAI API key is valid and has access to the required models
   - The API key should have access to both the Assistants API and the Audio API

3. **Configuration Issues**:
   - If you get an error about invalid modalities, make sure to only use `["audio"]` for the modalities setting, not `["text", "audio"]`. The OpenAI Agents SDK currently only supports one modality at a time.

4. **Connection Issues**:
   - Check your internet connection
   - Ensure your firewall isn't blocking the WebSocket connections
   - The OpenAI Audio API endpoints might experience occasional outages

5. **Microphone/Speaker Issues**:
   - Make sure your default microphone and speakers are working properly
   - Test them with another application before running Otto

### Error Logs

If you encounter errors, check the log output in the terminal. The application logs detailed information about:
- Connection attempts
- Audio processing
- Tool executions
- Error messages

## License

[MIT License](LICENSE)
