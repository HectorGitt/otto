# Otto — Voice Agent for Windows PC Control

Otto is a realtime voice assistant that controls your Windows PC through natural conversation. It uses the OpenAI Agents SDK, a FastAPI server with WebSocket streaming, and desktop automation libraries (PyAutoGUI, keyboard, and pywinctl for window management).

The web UI (dark theme) shows conversation, an event stream, and tool actions side-by-side.

## Features

-   Realtime speech-to-speech interaction (no wake word required)
-   Safe PC control with confirmations and step-by-step narration
-   Screen understanding loop: capture → describe → confirm → act → verify
-   Desktop actions: open apps, click, type, press keys, get screen info
-   Advanced window management via pywinctl (activate, move, resize, hide/show, always-on-top, etc.)
-   Modern web UI with chat, event stream, and tools panels

## Project layout

-   `app/agent.py` — Realtime agent configuration and instructions
-   `app/server.py` — FastAPI server + WebSocket; serves the UI
-   `app/pc_tools.py` — Tool implementations (PyAutoGUI, keyboard, pywinctl)
-   `app/static/index.html` — Web UI (chat, event stream, tools)
-   `app/static/app.js` — Client for realtime connection and UI rendering

## Requirements

-   Windows 10/11
-   Python 3.10+
-   OpenAI API key
-   Microphone and speakers

## Setup (PowerShell)

```powershell
# From repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies (if requirements.txt exists)
pip install -r requirements.txt  # optional

# Minimal manual install (if the line above fails)
pip install openai-agents fastapi uvicorn websockets python-dotenv pyautogui keyboard pillow opencv-python pywinctl

# Set your API key for this session
$env:OPENAI_API_KEY = "sk-..."
```

Create a `.env` file (optional):

```env
OPENAI_API_KEY=sk-...
```

## Run

Start the server from the repo root:

```powershell
python -m app.server
# or
python app\server.py
```

Open the UI:

-   http://localhost:8000

Click Connect in the UI to start the realtime session.

## Using Otto

Otto describes every step and asks before important actions. Typical flow:

1. “I’ll capture the screen to see context.”
2. “Here’s what I see…”
3. “Plan: click X, then type Y. Proceed?”
4. Executes step-by-step with verification screenshots.

### Example voice commands

-   “Open Chrome”
-   “Click the Start button”
-   “Type hello world”
-   “Press Control S”
-   “What’s my screen resolution?”
-   “Switch to Notepad and make it full screen”
-   “Move the browser to the left and resize to 800 by 600”

## Tools overview

Core PC control:

-   `open_application(app_name)`
-   `click_at_position(x, y, element?)`
-   `type_text(text)`
-   `press_key(key_or_combo)`
-   `get_screen_info()`
-   `capture_screen(region?, description?)`

Recovery/self-correction:

-   `undo_last_action()`
-   `try_alternate_action(action_type, original_params, alternate_params)`
-   `navigate_to_previous_state(method)`
-   `retry_with_delay(action_type, params, delay_seconds)`

Window management (pywinctl):

-   Info/find: `list_windows()`, `get_active_window()`, `find_windows_by_title(pattern)`, `get_all_app_names()`, `get_apps_with_name(app)`
-   Focus/state: `activate_window(pattern)`, `minimize_window(pattern)`, `maximize_window(pattern)`, `restore_window(pattern)`, `close_window(pattern)`
-   Position/size: `move_window(pattern, x, y)`, `resize_window(pattern, w, h)`
-   Visibility/pinning: `hide_window(pattern)`, `show_window(pattern)`, `set_window_always_on_top(pattern, bool)`
-   Diagnostics: `get_window_details(pattern)`, `get_windows_at_position(x, y)`

All window operations include before/after screenshots and friendly narration.

## UI notes

-   Conversation (left) remains primary; event stream and tools are constrained so they don’t cover chat history.
-   Status indicators show connection state and microphone status.

## Safety

-   PyAutoGUI failsafe enabled: move mouse to the top-left corner to abort.
-   Small pauses are added between actions for stability.
-   Otto asks for confirmation before impactful actions and multi-step plans.

## Troubleshooting

1. Server won’t start

    - Ensure the virtual environment is activated.
    - Verify dependencies are installed (see Setup).
    - Try running from repo root: `python -m app.server`.

2. UI doesn’t load at http://localhost:8000

    - Check server logs for errors.
    - Ensure static files are served from `app/static` (configured in `app/server.py`).

3. Import errors

    - Code imports use the `app.` package (e.g., `from app.pc_tools import ...`).

4. Automation not behaving

    - Some apps require focus; use window tools to activate first.
    - Try `retry_with_delay` or `undo_last_action` if timing is off.

5. Permissions (Windows)
    - pywinctl/pyautogui may require standard desktop session (not elevated/UAC prompts).

## License

[MIT License](LICENSE)
