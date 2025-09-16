import logging
import time
import pyautogui
import keyboard
import os
import base64
import cv2
import numpy as np
import pywinctl as pwc
from io import BytesIO
from PIL import Image
from agents import function_tool

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("OTTO.pc_tools")

# Configure PyAutoGUI for safety
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.5  # Add pause between PyAutoGUI commands

# Correction Utilities


def is_similar_image(img1_data, img2_data, threshold=0.95):
    """
    Compare two images to see if they are similar.

    Args:
        img1_data: First image as a base64 string or PIL Image
        img2_data: Second image as a base64 string or PIL Image
        threshold: Similarity threshold (higher means more similar)

    Returns:
        Boolean indicating if images are similar
    """
    try:
        if isinstance(img1_data, str) and img1_data.startswith("data:image"):
            # Extract base64 data after the comma
            img1_base64 = img1_data.split(",")[1]
            img1_bytes = base64.b64decode(img1_base64)
            img1 = Image.open(BytesIO(img1_bytes))
        elif isinstance(img1_data, Image.Image):
            img1 = img1_data
        else:
            return False

        if isinstance(img2_data, str) and img2_data.startswith("data:image"):
            img2_base64 = img2_data.split(",")[1]
            img2_bytes = base64.b64decode(img2_base64)
            img2 = Image.open(BytesIO(img2_bytes))
        elif isinstance(img2_data, Image.Image):
            img2 = img2_data
        else:
            return False

        # Convert to numpy arrays
        img1_np = np.array(img1)
        img2_np = np.array(img2)

        # Convert to grayscale
        img1_gray = cv2.cvtColor(img1_np, cv2.COLOR_RGB2GRAY)
        img2_gray = cv2.cvtColor(img2_np, cv2.COLOR_RGB2GRAY)

        # Calculate structural similarity index
        score, _ = cv2.compareHist(
            cv2.calcHist([img1_gray], [0], None, [256], [0, 256]),
            cv2.calcHist([img2_gray], [0], None, [256], [0, 256]),
            cv2.HISTCMP_CORREL,
        )

        return score >= threshold
    except Exception as e:
        logger.error(f"Error comparing images: {e}")
        return False


@function_tool
async def undo_last_action() -> str:
    """
    Attempt to undo the last action, such as pressing Ctrl+Z or going back.

    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before undo
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()

        # Try common undo methods
        logger.info("Attempting to undo last action with Ctrl+Z")
        keyboard.press_and_release("ctrl+z")

        # Wait for UI to update
        time.sleep(1.5)

        # Capture screen after undo
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()

        # Build result with before and after screenshots
        result = f"I'm attempting to undo the last action. Here's what I see on the screen first:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After trying to undo, here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"

        return result
    except Exception as e:
        logger.error(f"Error undoing last action: {e}")
        return f"Failed to undo last action: {str(e)}"


@function_tool
async def try_alternate_action(
    action_type: str, original_params: str, alternate_params: str
) -> str:
    """
    Try an alternative approach when the original action fails.

    Args:
        action_type: Type of action to try (e.g., 'click', 'type', 'open', 'key')
        original_params: Description of original failed parameters
        alternate_params: New parameters to try

    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before alternate action
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()

        result_message = ""

        # Try alternative approach based on action type
        if action_type.lower() == "click":
            # Parse x,y coordinates from alternate_params
            try:
                x, y = map(int, alternate_params.split(","))
                logger.info(f"Trying alternate click at: ({x}, {y})")
                pyautogui.click(x, y)
                result_message = f"Tried alternate click at position ({x}, {y})"
            except ValueError:
                result_message = (
                    f"Could not parse alternate click coordinates: {alternate_params}"
                )

        elif action_type.lower() == "type":
            logger.info(f"Trying alternate text: {alternate_params}")
            pyautogui.write(alternate_params)
            result_message = f"Tried typing alternate text: '{alternate_params}'"

        elif action_type.lower() == "open":
            logger.info(f"Trying to open alternate application: {alternate_params}")
            pyautogui.press("win")
            time.sleep(1)
            pyautogui.write(alternate_params)
            time.sleep(1)
            pyautogui.press("enter")
            result_message = (
                f"Tried opening alternate application: '{alternate_params}'"
            )

        elif action_type.lower() == "key":
            logger.info(f"Trying alternate key press: {alternate_params}")
            if "+" in alternate_params:
                keyboard.press_and_release(alternate_params)
            else:
                pyautogui.press(alternate_params)
            result_message = f"Tried pressing alternate key: '{alternate_params}'"

        else:
            return f"Unknown action type: {action_type}"

        # Wait for UI to update
        time.sleep(1.5)

        # Capture screen after alternate action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()

        # Build result with before and after screenshots
        result = (
            f"The original action with {original_params} didn't work as expected.\n"
        )
        result += f"I'm trying an alternative approach: {result_message}\n\n"
        result += f"Before the alternate action, here's what I saw:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After the alternate action, here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"

        return result
    except Exception as e:
        logger.error(f"Error trying alternate action: {e}")
        return f"Failed to perform alternate action: {str(e)}"


# PC Control Tools


@function_tool
async def navigate_to_previous_state(method: str = "back") -> str:
    """
    Navigate back to a previous state or location.

    Args:
        method: Navigation method to use ('back', 'alt+tab', 'esc', 'cancel')

    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before navigation
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()

        # Execute navigation based on method
        if method.lower() == "back":
            logger.info("Navigating back with Alt+Left")
            keyboard.press_and_release("alt+left")
            action_taken = "Pressed Alt+Left to go back"
        elif method.lower() == "alt+tab":
            logger.info("Switching to previous window with Alt+Tab")
            keyboard.press_and_release("alt+tab")
            action_taken = "Pressed Alt+Tab to switch to previous window"
        elif method.lower() == "esc":
            logger.info("Pressing Escape key")
            pyautogui.press("escape")
            action_taken = "Pressed Escape to cancel/close dialog"
        elif method.lower() == "cancel":
            logger.info("Looking for and clicking 'Cancel' button")
            # This is simplified - ideally would use image recognition to find cancel button
            # For now, just press Escape as fallback
            pyautogui.press("escape")
            action_taken = "Tried to cancel the current operation"
        else:
            logger.info(f"Unknown navigation method: {method}, using Escape as default")
            pyautogui.press("escape")
            action_taken = f"Unknown method '{method}', pressed Escape instead"

        # Wait for UI to update
        time.sleep(1.5)

        # Capture screen after navigation
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()

        # Build result with before and after screenshots
        result = (
            f"I'm attempting to navigate to the previous state using: {action_taken}.\n"
        )
        result += "Here's what I see on the screen before navigation:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += "After navigation, here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"

        return result
    except Exception as e:
        logger.error(f"Error navigating to previous state: {e}")
        return f"Failed to navigate to previous state: {str(e)}"


@function_tool
async def retry_with_delay(
    action_type: str, params: str, delay_seconds: int = 2
) -> str:
    """
    Retry the same action after a delay, useful when the system is slow to respond.

    Args:
        action_type: Type of action to retry ('click', 'type', 'open', 'key')
        params: Parameters for the action
        delay_seconds: How long to wait before retrying

    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before retry
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()

        # Wait the specified delay time
        logger.info(f"Waiting {delay_seconds} seconds before retrying action")
        time.sleep(delay_seconds)

        result_message = ""

        # Retry the action based on action type
        if action_type.lower() == "click":
            try:
                x, y = map(int, params.split(","))
                logger.info(f"Retrying click at: ({x}, {y})")
                pyautogui.click(x, y)
                result_message = f"Retried click at position ({x}, {y}) after {delay_seconds} second delay"
            except ValueError:
                result_message = f"Could not parse click coordinates: {params}"

        elif action_type.lower() == "type":
            logger.info(f"Retrying typing text: {params}")
            pyautogui.write(params)
            result_message = (
                f"Retried typing text: '{params}' after {delay_seconds} second delay"
            )

        elif action_type.lower() == "open":
            logger.info(f"Retrying opening application: {params}")
            pyautogui.press("win")
            time.sleep(1)
            pyautogui.write(params)
            time.sleep(1)
            pyautogui.press("enter")
            result_message = f"Retried opening application: '{params}' after {delay_seconds} second delay"

        elif action_type.lower() == "key":
            logger.info(f"Retrying key press: {params}")
            if "+" in params:
                keyboard.press_and_release(params)
            else:
                pyautogui.press(params)
            result_message = (
                f"Retried pressing key: '{params}' after {delay_seconds} second delay"
            )

        else:
            return f"Unknown action type: {action_type}"

        # Wait for UI to update
        time.sleep(1.5)

        # Capture screen after retry
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()

        # Build result with before and after screenshots
        result = f"The previous action may have failed due to timing issues.\n"
        result += f"{result_message}\n\n"
        result += "Before retrying, here's what I saw:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += "After retrying, here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"

        return result
    except Exception as e:
        logger.error(f"Error retrying action: {e}")
        return f"Failed to retry action: {str(e)}"


@function_tool
async def open_application(app_name: str) -> str:
    """
    Open a desktop application.

    Args:
        app_name: Name of the application to open
    """
    try:
        # Capture screen before action
        logger.info(f"Capturing screen before opening application: {app_name}")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()

        # Perform the action
        logger.info(f"Opening application: {app_name}")
        pyautogui.press("win")
        time.sleep(1)
        pyautogui.write(app_name)
        time.sleep(1)
        pyautogui.press("enter")

        # Wait for application to open
        time.sleep(2)

        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()

        result = (
            f"I'm about to open {app_name}. Here's what I see on the screen first:\n"
        )
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After attempting to open {app_name}, here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"

        return result

    except Exception as e:
        logger.error(f"Error opening application: {e}")
        return f"Failed to open application: {str(e)}"


@function_tool
async def click_at_position(x: int = None, y: int = None, element: str = None) -> str:
    """
    Click at specific screen coordinates or on an interface element.

    Args:
        x: X coordinate
        y: Y coordinate
        element: Description of UI element to click (e.g., 'File menu', 'Save button')
    """
    try:
        # First capture the screen before clicking
        logger.info("Capturing screen before clicking")
        pre_screenshot = pyautogui.screenshot()
        pre_buffered = BytesIO()
        pre_screenshot.save(pre_buffered, format="PNG")
        pre_img_str = base64.b64encode(pre_buffered.getvalue()).decode()

        # Determine click action info
        if x is not None and y is not None:
            click_info = f"I'm about to click at position ({x}, {y})"
        elif element is not None:
            click_info = f"I'm trying to find and click on the element: {element}"
        else:
            return "No position or element specified"

        # Perform the click action
        if x is not None and y is not None:
            logger.info(f"Clicking at position: ({x}, {y})")
            pyautogui.click(x, y)
        elif element is not None:
            logger.info(f"Trying to find and click on element: {element}")
            # This functionality is limited for now

        # Wait for UI to update
        time.sleep(1.5)

        # Capture the screen after clicking
        post_screenshot = pyautogui.screenshot()
        post_buffered = BytesIO()
        post_screenshot.save(post_buffered, format="PNG")
        post_img_str = base64.b64encode(post_buffered.getvalue()).decode()

        # Build result with before and after screenshots
        result = f"{click_info}. Here's what I see on the screen first:\n"
        result += f"data:image/png;base64,{pre_img_str}\n\n"

        if x is not None and y is not None:
            result += f"After clicking at position ({x}, {y}), here's what I see now:\n"
        else:
            result += (
                f"After attempting to click on {element}, here's what I see now:\n"
            )

        result += f"data:image/png;base64,{post_img_str}"

        return result

    except Exception as e:
        logger.error(f"Error clicking: {e}")
        return f"Failed to click: {str(e)}"


@function_tool
async def type_text(text: str) -> str:
    """
    Type text using the keyboard.

    Args:
        text: The text to type
    """
    try:
        if text:
            # Capture screen before typing
            logger.info(f"Capturing screen before typing text: {text}")
            before_screenshot = pyautogui.screenshot()
            before_buffered = BytesIO()
            before_screenshot.save(before_buffered, format="PNG")
            before_img_str = base64.b64encode(before_buffered.getvalue()).decode()

            # Type the text
            logger.info(f"Typing text: {text}")
            pyautogui.write(text)

            # Wait briefly
            time.sleep(1)

            # Capture after typing
            after_screenshot = pyautogui.screenshot()
            after_buffered = BytesIO()
            after_screenshot.save(after_buffered, format="PNG")
            after_img_str = base64.b64encode(after_buffered.getvalue()).decode()

            # Build result with before and after screenshots
            result = (
                f"I'm about to type: '{text}'. Here's what I see on the screen first:\n"
            )
            result += f"data:image/png;base64,{before_img_str}\n\n"
            result += f"After typing '{text}', here's what I see now:\n"
            result += f"data:image/png;base64,{after_img_str}"

            return result
        else:
            return "No text specified"

    except Exception as e:
        logger.error(f"Error typing text: {e}")
        return f"Failed to type text: {str(e)}"


@function_tool
async def press_key(key: str) -> str:
    """
    Press a specific keyboard key or key combination.

    Args:
        key: Key or key combination to press (e.g., 'enter', 'ctrl+s')
    """
    try:
        if key:
            # Capture screen before pressing key
            logger.info(f"Capturing screen before pressing key: {key}")
            before_screenshot = pyautogui.screenshot()
            before_buffered = BytesIO()
            before_screenshot.save(before_buffered, format="PNG")
            before_img_str = base64.b64encode(before_buffered.getvalue()).decode()

            # Press the key
            logger.info(f"Pressing key: {key}")
            if "+" in key:
                keyboard.press_and_release(key)
            else:
                pyautogui.press(key)

            # Wait briefly for UI to update
            time.sleep(1.5)

            # Capture screen after key press
            after_screenshot = pyautogui.screenshot()
            after_buffered = BytesIO()
            after_screenshot.save(after_buffered, format="PNG")
            after_img_str = base64.b64encode(after_buffered.getvalue()).decode()

            # Build result with before and after screenshots
            result = (
                f"I'm about to press: '{key}'. Here's what I see on the screen first:\n"
            )
            result += f"data:image/png;base64,{before_img_str}\n\n"
            result += f"After pressing '{key}', here's what I see now:\n"
            result += f"data:image/png;base64,{after_img_str}"

            return result
        else:
            return "No key specified"

    except Exception as e:
        logger.error(f"Error pressing key: {e}")
        return f"Failed to press key: {str(e)}"


@function_tool
async def get_screen_info() -> str:
    """Get information about the current screen."""
    try:
        # Get screen size
        screen_width, screen_height = pyautogui.size()

        # Get current mouse position
        mouse_x, mouse_y = pyautogui.position()

        screen_info = {
            "screen_size": {"width": screen_width, "height": screen_height},
            "mouse_position": {"x": mouse_x, "y": mouse_y},
        }

        logger.info(f"Screen info: {screen_info}")
        return f"Screen resolution: {screen_width}x{screen_height}, Mouse position: ({mouse_x}, {mouse_y})"

    except Exception as e:
        logger.error(f"Error getting screen info: {e}")
        return f"Failed to get screen info: {str(e)}"


@function_tool
async def capture_screen(region: str = None, description: bool = True) -> str:
    """
    Capture the screen or a specific region and return information about what's visible.

    Args:
        region: Optional region to capture in format "left,top,width,height" (e.g., "0,0,800,600")
        description: Whether to include a request for description of the screen

    Returns:
        Base64 encoded image data with description request
    """
    try:
        # Capture the screen
        if region:
            try:
                # Parse region string into coordinates
                left, top, width, height = map(int, region.split(","))
                screenshot = pyautogui.screenshot(region=(left, top, width, height))
                logger.info(f"Captured screen region: {region}")
            except ValueError:
                logger.error(f"Invalid region format: {region}")
                screenshot = pyautogui.screenshot()
                logger.info("Capturing full screen instead")
        else:
            screenshot = pyautogui.screenshot()
            logger.info("Captured full screen")

        # Convert to base64 for transmission
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Prepare message with image data
        if description:
            return f"data:image/png;base64,{img_str}\nPlease describe what you see on this screen."
        else:
            return f"data:image/png;base64,{img_str}"

    except Exception as e:
        logger.error(f"Error capturing screen: {e}")
        return f"Failed to capture screen: {str(e)}"


# Window Management Tools using pywinctl

@function_tool
async def list_windows() -> str:
    """
    List all open windows with their titles and basic information.
    
    Returns:
        String containing information about all open windows
    """
    try:
        logger.info("Getting list of all open windows")
        windows = pwc.getAllWindows()
        
        if not windows:
            return "No open windows found."
        
        result = "Open Windows:\n"
        result += "=" * 50 + "\n"
        
        for i, window in enumerate(windows, 1):
            try:
                title = window.title if window.title else "No Title"
                visible = "Visible" if window.visible else "Hidden"
                minimized = "Minimized" if window.isMinimized else "Normal"
                
                # Get window position and size
                box = window.box
                position = f"Position: ({box.left}, {box.top})"
                size = f"Size: {box.width}x{box.height}"
                
                result += f"{i}. {title}\n"
                result += f"   Status: {visible}, {minimized}\n"
                result += f"   {position}, {size}\n"
                result += f"   Process: {getattr(window, 'app', 'Unknown')}\n\n"
                
            except Exception as e:
                result += f"{i}. Error reading window info: {str(e)}\n\n"
        
        logger.info(f"Found {len(windows)} windows")
        return result
        
    except Exception as e:
        logger.error(f"Error listing windows: {e}")
        return f"Failed to list windows: {str(e)}"


@function_tool
async def get_active_window() -> str:
    """
    Get information about the currently active/focused window.
    
    Returns:
        String containing information about the active window
    """
    try:
        logger.info("Getting active window information")
        active_window = pwc.getActiveWindow()
        
        if not active_window:
            return "No active window found."
        
        title = active_window.title if active_window.title else "No Title"
        visible = "Visible" if active_window.visible else "Hidden"
        minimized = "Minimized" if active_window.isMinimized else "Normal"
        
        # Get window position and size
        box = active_window.box
        position = f"Position: ({box.left}, {box.top})"
        size = f"Size: {box.width}x{box.height}"
        
        result = "Active Window Information:\n"
        result += "=" * 30 + "\n"
        result += f"Title: {title}\n"
        result += f"Status: {visible}, {minimized}\n"
        result += f"{position}, {size}\n"
        result += f"Process: {getattr(active_window, 'app', 'Unknown')}\n"
        
        logger.info(f"Active window: {title}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting active window: {e}")
        return f"Failed to get active window: {str(e)}"


@function_tool
async def find_windows_by_title(title_pattern: str) -> str:
    """
    Find windows that match a title pattern.
    
    Args:
        title_pattern: Pattern to search for in window titles (case-insensitive)
    
    Returns:
        String containing information about matching windows
    """
    try:
        logger.info(f"Searching for windows with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        result = f"Windows matching '{title_pattern}':\n"
        result += "=" * 50 + "\n"
        
        for i, window in enumerate(windows, 1):
            try:
                title = window.title if window.title else "No Title"
                visible = "Visible" if window.visible else "Hidden"
                minimized = "Minimized" if window.isMinimized else "Normal"
                
                # Get window position and size
                box = window.box
                position = f"Position: ({box.left}, {box.top})"
                size = f"Size: {box.width}x{box.height}"
                
                result += f"{i}. {title}\n"
                result += f"   Status: {visible}, {minimized}\n"
                result += f"   {position}, {size}\n"
                result += f"   Process: {getattr(window, 'app', 'Unknown')}\n\n"
                
            except Exception as e:
                result += f"{i}. Error reading window info: {str(e)}\n\n"
        
        logger.info(f"Found {len(windows)} matching windows")
        return result
        
    except Exception as e:
        logger.error(f"Error finding windows by title: {e}")
        return f"Failed to find windows: {str(e)}"


@function_tool
async def activate_window(title_pattern: str) -> str:
    """
    Activate (bring to front and focus) a window by title pattern.
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before activating window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Activating window: {window_title}")
        
        # Restore if minimized, then activate
        if window.isMinimized:
            window.restore()
            time.sleep(0.5)
        
        window.activate()
        time.sleep(1.5)  # Wait for window to become active
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm activating the window: '{window_title}'. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After activating '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error activating window: {e}")
        return f"Failed to activate window: {str(e)}"


@function_tool
async def minimize_window(title_pattern: str) -> str:
    """
    Minimize a window by title pattern.
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before minimizing window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Minimizing window: {window_title}")
        window.minimize()
        time.sleep(1.5)  # Wait for window to minimize
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm minimizing the window: '{window_title}'. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After minimizing '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error minimizing window: {e}")
        return f"Failed to minimize window: {str(e)}"


@function_tool
async def maximize_window(title_pattern: str) -> str:
    """
    Maximize a window by title pattern.
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before maximizing window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Maximizing window: {window_title}")
        window.maximize()
        time.sleep(1.5)  # Wait for window to maximize
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm maximizing the window: '{window_title}'. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After maximizing '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error maximizing window: {e}")
        return f"Failed to maximize window: {str(e)}"


@function_tool
async def close_window(title_pattern: str) -> str:
    """
    Close a window by title pattern.
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before closing window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Closing window: {window_title}")
        window.close()
        time.sleep(1.5)  # Wait for window to close
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm closing the window: '{window_title}'. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After closing '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error closing window: {e}")
        return f"Failed to close window: {str(e)}"


@function_tool
async def resize_window(title_pattern: str, width: int, height: int) -> str:
    """
    Resize a window by title pattern.
    
    Args:
        title_pattern: Pattern to search for in window titles
        width: New width for the window
        height: New height for the window
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before resizing window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Resizing window '{window_title}' to {width}x{height}")
        window.resize(width, height)
        time.sleep(1.5)  # Wait for window to resize
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm resizing window '{window_title}' to {width}x{height}. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After resizing '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error resizing window: {e}")
        return f"Failed to resize window: {str(e)}"


@function_tool
async def move_window(title_pattern: str, x: int, y: int) -> str:
    """
    Move a window to a specific position by title pattern.
    
    Args:
        title_pattern: Pattern to search for in window titles
        x: New X position for the window
        y: New Y position for the window
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before moving window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Moving window '{window_title}' to position ({x}, {y})")
        window.moveTo(x, y)
        time.sleep(1.5)  # Wait for window to move
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm moving window '{window_title}' to position ({x}, {y}). Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After moving '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error moving window: {e}")
        return f"Failed to move window: {str(e)}"


@function_tool
async def get_all_app_names() -> str:
    """
    Get a list of all running application names.
    
    Returns:
        String containing all running application names
    """
    try:
        logger.info("Getting all application names")
        app_names = pwc.getAllAppsNames()
        
        if not app_names:
            return "No running applications found."
        
        result = "Running Applications:\n"
        result += "=" * 30 + "\n"
        
        # Remove duplicates and sort
        unique_apps = sorted(set(app_names))
        
        for i, app_name in enumerate(unique_apps, 1):
            result += f"{i}. {app_name}\n"
        
        logger.info(f"Found {len(unique_apps)} unique applications")
        return result
        
    except Exception as e:
        logger.error(f"Error getting app names: {e}")
        return f"Failed to get app names: {str(e)}"


@function_tool
async def get_apps_with_name(app_name: str) -> str:
    """
    Get all windows belonging to a specific application.
    
    Args:
        app_name: Name of the application to search for
    
    Returns:
        String containing information about windows for the specified app
    """
    try:
        logger.info(f"Getting windows for application: {app_name}")
        app_windows = pwc.getAppsWithName(app_name)
        
        if not app_windows:
            return f"No windows found for application: '{app_name}'"
        
        result = f"Windows for '{app_name}':\n"
        result += "=" * 40 + "\n"
        
        for i, window in enumerate(app_windows, 1):
            try:
                title = window.title if window.title else "No Title"
                visible = "Visible" if window.visible else "Hidden"
                minimized = "Minimized" if window.isMinimized else "Normal"
                active = "Active" if window.isActive else "Inactive"
                
                # Get window position and size
                box = window.box
                position = f"Position: ({box.left}, {box.top})"
                size = f"Size: {box.width}x{box.height}"
                
                result += f"{i}. {title}\n"
                result += f"   Status: {visible}, {minimized}, {active}\n"
                result += f"   {position}, {size}\n\n"
                
            except Exception as e:
                result += f"{i}. Error reading window info: {str(e)}\n\n"
        
        logger.info(f"Found {len(app_windows)} windows for {app_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting apps with name: {e}")
        return f"Failed to get apps with name: {str(e)}"


@function_tool
async def hide_window(title_pattern: str) -> str:
    """
    Hide a window (different from minimize - completely hides from taskbar).
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before hiding window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Hiding window: {window_title}")
        window.hide()
        time.sleep(1.5)  # Wait for window to hide
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm hiding the window: '{window_title}'. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After hiding '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error hiding window: {e}")
        return f"Failed to hide window: {str(e)}"


@function_tool
async def show_window(title_pattern: str) -> str:
    """
    Show a previously hidden window.
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before showing window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Showing window: {window_title}")
        window.show()
        time.sleep(1.5)  # Wait for window to show
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm showing the window: '{window_title}'. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After showing '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error showing window: {e}")
        return f"Failed to show window: {str(e)}"


@function_tool
async def restore_window(title_pattern: str) -> str:
    """
    Restore a window from minimized or maximized state to normal.
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before restoring window")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        logger.info(f"Restoring window: {window_title}")
        window.restore()
        time.sleep(1.5)  # Wait for window to restore
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm restoring the window: '{window_title}' to normal size. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After restoring '{window_title}', here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error restoring window: {e}")
        return f"Failed to restore window: {str(e)}"


@function_tool
async def set_window_always_on_top(title_pattern: str, always_on_top: bool = True) -> str:
    """
    Set a window to always stay on top of other windows.
    
    Args:
        title_pattern: Pattern to search for in window titles
        always_on_top: True to set always on top, False to remove
    
    Returns:
        Status message with before and after screenshots
    """
    try:
        # Capture screen before action
        logger.info("Capturing screen before setting window always on top")
        before_screenshot = pyautogui.screenshot()
        before_buffered = BytesIO()
        before_screenshot.save(before_buffered, format="PNG")
        before_img_str = base64.b64encode(before_buffered.getvalue()).decode()
        
        logger.info(f"Searching for window with title pattern: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        window_title = window.title if window.title else "No Title"
        
        action_text = "on top" if always_on_top else "normal"
        logger.info(f"Setting window '{window_title}' always on top: {always_on_top}")
        window.alwaysOnTop(always_on_top)
        time.sleep(1.5)  # Wait for setting to apply
        
        # Capture screen after action
        after_screenshot = pyautogui.screenshot()
        after_buffered = BytesIO()
        after_screenshot.save(after_buffered, format="PNG")
        after_img_str = base64.b64encode(after_buffered.getvalue()).decode()
        
        # Build result with before and after screenshots
        result = f"I'm setting window '{window_title}' to {action_text}. Here's what I see before:\n"
        result += f"data:image/png;base64,{before_img_str}\n\n"
        result += f"After setting '{window_title}' to {action_text}, here's what I see now:\n"
        result += f"data:image/png;base64,{after_img_str}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error setting window always on top: {e}")
        return f"Failed to set window always on top: {str(e)}"


@function_tool
async def get_window_details(title_pattern: str) -> str:
    """
    Get comprehensive details about a specific window.
    
    Args:
        title_pattern: Pattern to search for in window titles
    
    Returns:
        Detailed information about the window
    """
    try:
        logger.info(f"Getting detailed info for window: {title_pattern}")
        windows = pwc.getWindowsWithTitle(title_pattern)
        
        if not windows:
            return f"No windows found matching title pattern: '{title_pattern}'"
        
        # Use the first matching window
        window = windows[0]
        
        result = "Window Details:\n"
        result += "=" * 30 + "\n"
        
        try:
            # Basic info
            result += f"Title: {window.title if window.title else 'No Title'}\n"
            result += f"App Name: {getattr(window, 'app', 'Unknown')}\n"
            
            # State information
            result += f"Visible: {window.visible}\n"
            result += f"Active: {window.isActive}\n"
            result += f"Minimized: {window.isMinimized}\n"
            result += f"Maximized: {window.isMaximized}\n"
            result += f"Alive: {window.isAlive}\n"
            
            # Position and size
            box = window.box
            result += f"Position: ({box.left}, {box.top})\n"
            result += f"Size: {box.width} x {box.height}\n"
            result += f"Center: ({window.center[0]}, {window.center[1]})\n"
            
            # Advanced properties
            try:
                result += f"PID: {window.getPID()}\n"
            except Exception:
                result += "PID: Not available\n"
                
            try:
                handle = window.getHandle()
                result += f"Handle: {handle}\n"
            except Exception:
                result += "Handle: Not available\n"
            
        except Exception as e:
            result += f"Error getting window details: {str(e)}\n"
        
        logger.info(f"Retrieved details for window: {window.title}")
        return result
        
    except Exception as e:
        logger.error(f"Error getting window details: {e}")
        return f"Failed to get window details: {str(e)}"


@function_tool
async def get_windows_at_position(x: int, y: int) -> str:
    """
    Get all windows at a specific screen position.
    
    Args:
        x: X coordinate
        y: Y coordinate
    
    Returns:
        Information about windows at the specified position
    """
    try:
        logger.info(f"Getting windows at position ({x}, {y})")
        windows = pwc.getWindowsAt(x, y)
        
        if not windows:
            return f"No windows found at position ({x}, {y})"
        
        result = f"Windows at position ({x}, {y}):\n"
        result += "=" * 40 + "\n"
        
        for i, window in enumerate(windows, 1):
            try:
                title = window.title if window.title else "No Title"
                visible = "Visible" if window.visible else "Hidden"
                active = "Active" if window.isActive else "Inactive"
                
                # Get window position and size
                box = window.box
                position = f"Position: ({box.left}, {box.top})"
                size = f"Size: {box.width}x{box.height}"
                
                result += f"{i}. {title}\n"
                result += f"   Status: {visible}, {active}\n"
                result += f"   {position}, {size}\n"
                result += f"   App: {getattr(window, 'app', 'Unknown')}\n\n"
                
            except Exception as e:
                result += f"{i}. Error reading window info: {str(e)}\n\n"
        
        logger.info(f"Found {len(windows)} windows at position ({x}, {y})")
        return result
        
    except Exception as e:
        logger.error(f"Error getting windows at position: {e}")
        return f"Failed to get windows at position: {str(e)}"
