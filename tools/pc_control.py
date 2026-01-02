"""
PC Control Tools
Provides tools for controlling the computer: opening apps, files, folders, etc.
"""

import subprocess
import os
import sys
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


@tool("open_application", "Opens an application by name. Supports common apps like notepad, chrome, spotify, vscode, discord, calculator, etc.")
def open_application(app_name: str) -> str:
    """
    Opens an application by name.
    
    Args:
        app_name: The name of the application to open (e.g., 'notepad', 'chrome', 'spotify')
        
    Returns:
        A message indicating success or failure
    """
    try:
        app_path = get_app_path(app_name)
        
        # Try to run the application
        if os.path.exists(app_path):
            subprocess.Popen(app_path, shell=True)
        else:
            # Try running it directly (for system apps like notepad, calc, etc.)
            subprocess.Popen(app_path, shell=True)
        
        return f"Successfully opened {app_name}"
    except FileNotFoundError:
        return f"Could not find application: {app_name}. Please check if it's installed."
    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"


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
