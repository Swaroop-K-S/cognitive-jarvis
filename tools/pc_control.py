"""
PC Control Tools
Provides tools for controlling the computer: opening apps, files, folders, etc.
"""

import subprocess
import os
import sys
import time
from datetime import datetime
from typing import Optional

# Handle imports gracefully if libraries aren't installed yet
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_app_path

from .registry import tool

# Process name mapping for common apps
APP_PROCESS_MAP = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "firefox": ["firefox.exe"],
    "notepad": ["notepad.exe"],
    "spotify": ["spotify.exe"],
    "discord": ["discord.exe", "update.exe"],
    "vscode": ["code.exe"],
    "vs code": ["code.exe"],
    "code": ["code.exe"],
    "edge": ["msedge.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "explorer": ["explorer.exe"],
}


def is_app_running(app_name: str) -> bool:
    """Check if an application is currently running."""
    if not PSUTIL_AVAILABLE:
        return False
    
    app_lower = app_name.lower()
    expected = APP_PROCESS_MAP.get(app_lower, [])
    
    if not expected:
        # For unknown apps, try matching the name directly
        expected = [f"{app_lower}.exe"]
    
    for proc in psutil.process_iter(['name']):
        try:
            proc_name = proc.info['name'].lower()
            if proc_name in [e.lower() for e in expected]:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


@tool("check_app_running", "Checks if an application is currently running on the computer.")
def check_app_running(app_name: str) -> str:
    """Check if an app is running and return status."""
    if is_app_running(app_name):
        return f"✓ {app_name} is currently running."
    else:
        return f"✗ {app_name} is NOT running."


@tool("close_application", "Closes/terminates an application by name. Use for 'close chrome', 'quit spotify', etc.")
def close_application(app_name: str) -> str:
    """
    Close an application by terminating its process.
    
    Args:
        app_name: Name of the app to close (e.g., 'chrome', 'notepad', 'spotify')
        
    Returns:
        Message indicating success or failure
    """
    if not PSUTIL_AVAILABLE:
        return "❌ Cannot close apps: psutil not installed."
    
    app_lower = app_name.lower()
    expected = APP_PROCESS_MAP.get(app_lower, [])
    
    if not expected:
        # For unknown apps, try matching the name directly
        expected = [f"{app_lower}.exe"]
    
    closed_count = 0
    errors = []
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            if proc_name in [e.lower() for e in expected]:
                proc.terminate()  # Graceful termination
                closed_count += 1
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            errors.append(f"Access denied for {proc.info['name']}")
        except Exception as e:
            errors.append(str(e))
    
    if closed_count > 0:
        return f"✓ Closed {app_name}! ({closed_count} process{'es' if closed_count > 1 else ''} terminated)"
    elif errors:
        return f"❌ Could not close {app_name}: {', '.join(errors)}"
    else:
        return f"⚠️ {app_name} is not running, nothing to close."


@tool("open_application", "Opens an application or file. If the app is already running, it will tell you so.")
def open_application(app_name: str) -> str:
    """
    Opens an application, file, or URI. Checks if already running first.
    
    Args:
        app_name: The name of the app, path to a file, or command to run
        
    Returns:
        A message indicating success or failure
    """
    try:
        # 1. Check if already running (for known apps)
        app_lower = app_name.lower()
        if app_lower in APP_PROCESS_MAP and is_app_running(app_name):
            return f"✓ {app_name} is already running! Would you like me to open a new window or do something in it?"
        
        # 2. Get resolved path if it's a common app alias
        target = get_app_path(app_name)
        
        # Check if target exists (for file paths)
        is_file_path = os.path.exists(target) or target.startswith("http")
        
        # 3. Try os.startfile (Windows native "Run")
        try:
            os.startfile(target)
            # Give it a moment to start
            time.sleep(0.8)
            
            # Verify: For known apps, check if process appeared
            if PSUTIL_AVAILABLE and not is_file_path:
                expected = APP_PROCESS_MAP.get(app_lower, [])
                if expected:
                    if is_app_running(app_name):
                        return f"✓ Opened {app_name} successfully! What would you like to do next?"
                    else:
                        return f"⚠️ Tried to open {app_name}, but couldn't verify it started. It might still be loading, or the path may be wrong."
            
            return f"✓ Opened: {target}"
            
        except OSError as e:
            # 4. Fallback to subprocess for commands that aren't files/registered
            try:
                result = subprocess.Popen(target, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(0.5)
                if result.poll() is None or result.returncode == 0:
                    return f"✓ Running command: {target}"
                else:
                    return f"❌ Command failed: {target}"
            except Exception as sub_e:
                return f"❌ Could not open '{app_name}': {str(e)}"
            
    except Exception as e:
        return f"❌ Error opening '{app_name}': {str(e)}. Try the exact path or 'locate' it first."


@tool("type_text", "Types text using the keyboard. Useful for entering messages into opened applications.")
def type_text(text: str, interval: float = 0.05) -> str:
    """
    Types text using the keyboard.
    
    Args:
        text: The text to type
        interval: Delay between key presses (default 0.05s)
        
    Returns:
        Success message
    """
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"
    
    try:
        # Give user time to switch focus if running manually, but for BRO
        # we usually open an app first. Add small safety delay.
        time.sleep(1) 
        
        pyautogui.write(text, interval=interval)
        return f"Typed: {text}"
    except Exception as e:
        return f"Error typing text: {str(e)}"


@tool("press_key", "Presses a specific key (e.g., 'enter', 'tab', 'ctrl', 'a')")
def press_key(key: str, times: int = 1) -> str:
    """
    Presses a specific key.
    
    Args:
        key: The key to press
        times: Number of times to press
        
    Returns:
        Success message
    """
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui is not installed"
        
    try:
        pyautogui.press(key, presses=times)
        return f"Pressed key: {key} ({times} times)"
    except Exception as e:
        return f"Error pressing key: {str(e)}"


@tool("open_file", "Opens a file with its default application")
def open_file(file_path: str) -> str:
    """
    Opens a file with its default application.
    
    Args:
        file_path: The full path to the file to open
        
    Returns:
        A message indicating success or failure
    """
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        # Use os.startfile on Windows to open with default app
        os.startfile(file_path)
        return f"Opened file: {file_path}"
    except Exception as e:
        return f"Error opening file: {str(e)}"


@tool("open_folder", "Opens a folder in File Explorer")
def open_folder(folder_path: str) -> str:
    """
    Opens a folder in File Explorer.
    
    Args:
        folder_path: The path to the folder to open
        
    Returns:
        A message indicating success or failure
    """
    try:
        # Expand common folder shortcuts
        folder_mappings = {
            "documents": os.path.expanduser("~\\Documents"),
            "downloads": os.path.expanduser("~\\Downloads"),
            "desktop": os.path.expanduser("~\\Desktop"),
            "pictures": os.path.expanduser("~\\Pictures"),
            "music": os.path.expanduser("~\\Music"),
            "videos": os.path.expanduser("~\\Videos"),
            "home": os.path.expanduser("~"),
        }
        
        # Check if it's a shortcut name
        folder_lower = folder_path.lower()
        if folder_lower in folder_mappings:
            folder_path = folder_mappings[folder_lower]
        
        if not os.path.exists(folder_path):
            return f"Folder not found: {folder_path}"
        
        subprocess.Popen(f'explorer "{folder_path}"')
        return f"Opened folder: {folder_path}"
    except Exception as e:
        return f"Error opening folder: {str(e)}"


@tool("take_screenshot", "Takes a screenshot of the current screen and saves it")
def take_screenshot(save_path: Optional[str] = None) -> str:
    """
    Takes a screenshot of the current screen.
    
    Args:
        save_path: Optional path to save the screenshot. If not provided, saves to Pictures folder.
        
    Returns:
        The path where the screenshot was saved
    """
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"
    
    try:
        if save_path is None:
            # Create a default filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pictures_folder = os.path.expanduser("~\\Pictures")
            save_path = os.path.join(pictures_folder, f"screenshot_{timestamp}.png")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Take the screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        
        return f"Screenshot saved to: {save_path}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


@tool("list_processes", "Lists currently running processes on the computer")
def list_processes(limit: int = 15) -> str:
    """
    Lists the currently running processes.
    
    Args:
        limit: Maximum number of processes to list (default 15)
        
    Returns:
        A formatted list of running processes
    """
    if not PSUTIL_AVAILABLE:
        return "Error: psutil is not installed. Run: pip install psutil"
    
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                info = proc.info
                processes.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'memory': info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory'] or 0, reverse=True)
        
        # Format output
        result = "Top running processes:\n"
        result += "-" * 50 + "\n"
        result += f"{'PID':<10} {'Name':<30} {'Memory %':<10}\n"
        result += "-" * 50 + "\n"
        
        for proc in processes[:limit]:
            mem = f"{proc['memory']:.1f}%" if proc['memory'] else "N/A"
            result += f"{proc['pid']:<10} {proc['name'][:28]:<30} {mem:<10}\n"
        
        return result
    except Exception as e:
        return f"Error listing processes: {str(e)}"


@tool("get_system_info", "Gets basic system information like CPU, memory, and disk usage")
def get_system_info() -> str:
    """
    Gets basic system information.
    
    Returns:
        A formatted string with system information
    """
    if not PSUTIL_AVAILABLE:
        return "Error: psutil is not installed. Run: pip install psutil"
    
    try:
        # CPU info
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory info
        memory = psutil.virtual_memory()
        mem_total = memory.total / (1024 ** 3)  # GB
        mem_used = memory.used / (1024 ** 3)
        mem_percent = memory.percent
        
        # Disk info
        disk = psutil.disk_usage('/')
        disk_total = disk.total / (1024 ** 3)
        disk_used = disk.used / (1024 ** 3)
        disk_percent = disk.percent
        
        result = f"""
System Information:
==================
CPU Usage: {cpu_percent}% (Cores: {cpu_count})
Memory: {mem_used:.1f} GB / {mem_total:.1f} GB ({mem_percent}%)
Disk: {disk_used:.1f} GB / {disk_total:.1f} GB ({disk_percent}%)
"""
        return result
    except Exception as e:
        return f"Error getting system info: {str(e)}"
