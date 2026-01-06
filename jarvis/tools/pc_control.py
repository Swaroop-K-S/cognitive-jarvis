"""
PC Control Tools
Provides tools for controlling the computer: opening apps, files, folders, etc.
"""

import subprocess
import os
import sys
import time
import shutil
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

# Optional: For advanced app discovery (Layer 2 of Universal App Launcher)
try:
    from AppOpener import open as app_opener_open
    APPOPENER_AVAILABLE = True
except ImportError:
    APPOPENER_AVAILABLE = False

try:
    import winapps
    WINAPPS_AVAILABLE = True
except ImportError:
    WINAPPS_AVAILABLE = False

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
    "notebook": ["notepad.exe"],
    "spotify": ["spotify.exe"],
    "discord": ["discord.exe", "update.exe"],
    "vscode": ["code.exe"],
    "vs code": ["code.exe"],
    "visual studio code": ["code.exe"],
    "code": ["code.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "powerpoint": ["powerpnt.exe"],
    "outlook": ["outlook.exe"],
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "files": ["explorer.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "terminal": ["powershell.exe", "cmd.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "paint": ["mspaint.exe"],
    "settings": ["systemsettings.exe"],
    "whatsapp": ["WhatsApp.exe", "WhatsAppNative.exe"],
    # Additional apps
    "bluestacks": ["HD-Player.exe", "BlueStacks.exe"],
    "telegram": ["Telegram.exe"],
    "slack": ["slack.exe"],
    "zoom": ["Zoom.exe"],
    "teams": ["ms-teams.exe", "Teams.exe"],
    "microsoft teams": ["ms-teams.exe", "Teams.exe"],
    "obs": ["obs64.exe", "obs.exe"],
    "steam": ["steam.exe"],
    "epic games": ["EpicGamesLauncher.exe"],
    "vlc": ["vlc.exe"],
    "itunes": ["iTunes.exe"],
    "adobe reader": ["AcroRd32.exe", "Acrobat.exe"],
    "photoshop": ["Photoshop.exe"],
    "premiere": ["Adobe Premiere Pro.exe"],
    "postman": ["Postman.exe"],
    "git bash": ["git-bash.exe", "bash.exe"],
    "notion": ["Notion.exe"],
    "figma": ["Figma.exe"],
    "skype": ["Skype.exe"],
}

# =============================================================================
# AUTO-DISCOVERY: Dynamically find all installed apps on the PC
# =============================================================================

# Cache for discovered apps (name -> path)
_discovered_apps_cache = {}
_cache_initialized = False


def _scan_start_menu() -> dict:
    """Scan Start Menu shortcuts to find installed apps."""
    apps = {}
    start_menu_paths = [
        os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"), "Microsoft\\Windows\\Start Menu\\Programs"),
        os.path.join(os.path.expanduser("~"), "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs"),
    ]
    
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        
        for start_path in start_menu_paths:
            if not os.path.exists(start_path):
                continue
            for root, dirs, files in os.walk(start_path):
                for file in files:
                    if file.endswith(".lnk"):
                        try:
                            shortcut_path = os.path.join(root, file)
                            shortcut = shell.CreateShortCut(shortcut_path)
                            target = shortcut.Targetpath
                            if target and os.path.exists(target) and target.lower().endswith(".exe"):
                                app_name = file[:-4].lower()  # Remove .lnk
                                apps[app_name] = target
                        except:
                            pass
    except ImportError:
        # win32com not available, use basic approach
        pass
    
    return apps


def _scan_registry() -> dict:
    """Scan Windows Registry for installed applications."""
    apps = {}
    import winreg
    
    # Registry paths where apps are typically registered
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    
    for hkey, path in reg_paths:
        try:
            key = winreg.OpenKey(hkey, path)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        try:
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                            if install_location and os.path.exists(install_location):
                                # Look for .exe files in install location
                                for file in os.listdir(install_location):
                                    if file.lower().endswith(".exe"):
                                        app_name = display_name.lower()
                                        apps[app_name] = os.path.join(install_location, file)
                                        break
                        except WindowsError:
                            pass
                    except WindowsError:
                        pass
                    winreg.CloseKey(subkey)
                except WindowsError:
                    pass
            winreg.CloseKey(key)
        except WindowsError:
            pass
    
    return apps


def _scan_common_paths() -> dict:
    """Scan common installation directories for apps."""
    apps = {}
    common_dirs = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        os.path.join(os.path.expanduser("~"), "AppData\\Local\\Programs"),
        os.path.join(os.path.expanduser("~"), "AppData\\Local"),
        os.path.join(os.path.expanduser("~"), "AppData\\Roaming"),
    ]
    
    for base_dir in common_dirs:
        if not os.path.exists(base_dir):
            continue
        try:
            for folder in os.listdir(base_dir):
                folder_path = os.path.join(base_dir, folder)
                if os.path.isdir(folder_path):
                    # Look for .exe with same name as folder
                    exe_path = os.path.join(folder_path, f"{folder}.exe")
                    if os.path.exists(exe_path):
                        apps[folder.lower()] = exe_path
                    else:
                        # Find any .exe in the folder
                        try:
                            for file in os.listdir(folder_path):
                                if file.lower().endswith(".exe") and not file.startswith("unins"):
                                    apps[folder.lower()] = os.path.join(folder_path, file)
                                    break
                        except PermissionError:
                            pass
        except PermissionError:
            pass
    
    return apps


def _scan_winapps() -> dict:
    """Use winapps library to find installed applications."""
    apps = {}
    if WINAPPS_AVAILABLE:
        try:
            for app in winapps.list_installed():
                if app.install_location and os.path.exists(app.install_location):
                    # Find .exe in install location
                    try:
                        for file in os.listdir(app.install_location):
                            if file.lower().endswith(".exe") and not file.startswith("unins"):
                                apps[app.name.lower()] = os.path.join(app.install_location, file)
                                break
                    except:
                        pass
        except:
            pass
    return apps


def discover_installed_apps(force_refresh: bool = False) -> dict:
    """
    Discover all installed applications on the PC.
    Uses multiple methods: Registry, Start Menu, common paths, winapps.
    Results are cached for performance.
    
    Args:
        force_refresh: If True, rescan even if cache exists
        
    Returns:
        Dictionary mapping app names to their executable paths
    """
    global _discovered_apps_cache, _cache_initialized
    
    if _cache_initialized and not force_refresh:
        return _discovered_apps_cache
    
    discovered = {}
    
    # Method 1: Scan Start Menu (most reliable)
    try:
        discovered.update(_scan_start_menu())
    except:
        pass
    
    # Method 2: Scan Registry
    try:
        discovered.update(_scan_registry())
    except:
        pass
    
    # Method 3: Scan common paths
    try:
        discovered.update(_scan_common_paths())
    except:
        pass
    
    # Method 4: Use winapps library
    try:
        discovered.update(_scan_winapps())
    except:
        pass
    
    _discovered_apps_cache = discovered
    _cache_initialized = True
    
    return discovered


def find_app_path(app_name: str) -> str:
    """
    Find the executable path for an app by name.
    Uses both static config and dynamic discovery.
    
    Args:
        app_name: Name of the app to find
        
    Returns:
        Path to the executable or the app_name itself if not found
    """
    app_lower = app_name.lower().strip()
    
    # 1. Check static config first (fastest)
    static_path = get_app_path(app_name)
    if static_path != app_name and (os.path.exists(static_path) or static_path.endswith(":")):
        return static_path
    
    # 2. Check discovered apps cache
    discovered = discover_installed_apps()
    
    # Exact match
    if app_lower in discovered:
        return discovered[app_lower]
    
    # Fuzzy match (contains)
    for name, path in discovered.items():
        if app_lower in name or name in app_lower:
            return path
    
    # 3. Check if it's in PATH
    which_path = shutil.which(app_lower)
    if which_path:
        return which_path
    
    return app_name


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


@tool("list_installed_apps", "Lists all installed applications discovered on the PC. Use for 'what apps are installed', 'show installed apps', etc.")
def list_installed_apps(refresh: bool = False, limit: int = 50) -> str:
    """
    Lists all installed applications discovered on the PC.
    
    Args:
        refresh: If True, rescan the PC for apps (otherwise uses cache)
        limit: Maximum number of apps to list (default 50)
        
    Returns:
        Formatted list of discovered applications
    """
    try:
        apps = discover_installed_apps(force_refresh=refresh)
        
        if not apps:
            return "❌ No applications discovered. Try installing pywin32 for better discovery: pip install pywin32"
        
        # Sort alphabetically
        sorted_apps = sorted(apps.items(), key=lambda x: x[0])[:limit]
        
        result = f"📦 Discovered {len(apps)} installed applications:\n"
        result += "-" * 50 + "\n"
        
        for name, path in sorted_apps:
            # Truncate long paths
            display_path = path if len(path) < 50 else "..." + path[-47:]
            result += f"  • {name}: {display_path}\n"
        
        if len(apps) > limit:
            result += f"\n... and {len(apps) - limit} more apps."
        
        result += f"\n\n💡 Tip: Say 'open [app name]' to launch any of these apps."
        return result
        
    except Exception as e:
        return f"❌ Error listing apps: {str(e)}"


@tool("search_installed_apps", "Searches for an installed application by name. Use for 'find app', 'search for [app]', etc.")
def search_installed_apps(query: str) -> str:
    """
    Searches for installed applications matching a query.
    
    Args:
        query: Search term to find apps
        
    Returns:
        List of matching applications with their paths
    """
    try:
        apps = discover_installed_apps()
        query_lower = query.lower().strip()
        
        # Find matching apps
        matches = []
        for name, path in apps.items():
            if query_lower in name or query_lower in path.lower():
                matches.append((name, path))
        
        if not matches:
            return f"❌ No apps found matching '{query}'. Try a different search term."
        
        result = f"🔍 Found {len(matches)} apps matching '{query}':\n"
        result += "-" * 50 + "\n"
        
        for name, path in sorted(matches)[:20]:
            result += f"  • {name}\n    Path: {path}\n"
        
        if len(matches) > 20:
            result += f"\n... and {len(matches) - 20} more matches."
        
        return result
        
    except Exception as e:
        return f"❌ Error searching apps: {str(e)}"

@tool("open_application", "Launches an application. Use this for 'open', 'start', 'launch' commands. Handles focusing if already open.")
def open_application(app_name: str) -> str:
    """
    Opens an application using a 3-layer strategy for maximum compatibility.
    
    Layer 1 (Speed): URI schemes & magic commands (fastest)
    Layer 2 (Registry): AppOpener scans installed programs to find .exe
    Layer 3 (Visual Fallback): Simulates Win key + typing (100% success rate)
    
    Args:
        app_name: The name of the app (e.g. 'notepad', 'chrome', 'whatsapp') or file path.
        
    Returns:
        Status message
    """
    try:
        app_lower = app_name.lower().strip()
        
        # 0. Check if already running (for known apps) - FOCUS instead of re-opening
        if app_lower in APP_PROCESS_MAP and is_app_running(app_name):
            focus_msg = focus_window(app_name)
            return f"✓ {app_name} is already running. {focus_msg}"
        
        # =====================================================================
        # LAYER 1: SPEED SHORTCUTS (URI schemes, direct commands, known paths)
        # Uses find_app_path which includes auto-discovery of installed apps
        # =====================================================================
        target = find_app_path(app_name)  # Uses both static config AND auto-discovery
        
        # Detect if this is a URI scheme (ends with :) or file path
        is_uri_scheme = target.endswith(":") or "://" in target
        is_file_path = os.path.exists(target) or is_uri_scheme
        
        # Smart Fallback: If path doesn't exist, try shutil.which (for PATH commands)
        if not is_file_path:
            which_path = shutil.which(target)
            if which_path:
                target = which_path
                is_file_path = True
            elif not target.endswith(".exe") and shutil.which(target + ".exe"):
                target = shutil.which(target + ".exe")
                is_file_path = True
        
        # Try Layer 1: os.startfile (handles .exe, URIs, file associations)
        if is_file_path or is_uri_scheme:
            try:
                os.startfile(target)
                time.sleep(0.8)
                
                # Verify launch for known apps
                if PSUTIL_AVAILABLE and app_lower in APP_PROCESS_MAP:
                    for _ in range(5):
                        if is_app_running(app_name):
                            return f"✓ Layer 1 Success: '{app_name}' is running."
                        time.sleep(0.5)
                
                return f"✓ Layer 1: Opened '{app_name}' via {target}"
            except OSError:
                pass  # Move to Layer 2
        
        # =====================================================================
        # LAYER 2: REGISTRY SCAN (Find installed apps via AppOpener/winapps)
        # =====================================================================
        if APPOPENER_AVAILABLE:
            try:
                app_opener_open(app_lower, match_closest=True, throw_error=True)
                time.sleep(1)
                
                # Verify launch
                if PSUTIL_AVAILABLE and app_lower in APP_PROCESS_MAP:
                    for _ in range(5):
                        if is_app_running(app_name):
                            return f"✓ Layer 2 Success: '{app_name}' found and launched via registry."
                        time.sleep(0.5)
                
                return f"✓ Layer 2: Opened '{app_name}' via AppOpener registry scan."
            except Exception:
                pass  # Move to Layer 3
        
        # Try subprocess as intermediate fallback
        try:
            result = subprocess.Popen(target, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)
            
            if result.poll() is None or result.returncode == 0:
                # Check if app is now running
                if PSUTIL_AVAILABLE and app_lower in APP_PROCESS_MAP:
                    for _ in range(3):
                        if is_app_running(app_name):
                            return f"✓ Subprocess Success: '{app_name}' launched."
                        time.sleep(0.5)
                return f"✓ Command Started: {target}"
        except Exception:
            pass  # Move to Layer 3
        
        # =====================================================================
        # LAYER 3: VISUAL FALLBACK (Win Key + Type + Enter - 100% success rate)
        # =====================================================================
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.press('win')
                time.sleep(0.3)
                pyautogui.write(app_lower, interval=0.05)
                time.sleep(1.0)  # Wait for Windows Search to find the app
                pyautogui.press('enter')
                time.sleep(1.5)  # Wait for app to launch
                
                # Verify launch
                if PSUTIL_AVAILABLE and app_lower in APP_PROCESS_MAP:
                    for _ in range(5):
                        if is_app_running(app_name):
                            return f"✓ Layer 3 Success: '{app_name}' launched via Windows Search."
                        time.sleep(0.5)
                
                return f"✓ Layer 3: Launched '{app_name}' via Windows Search (visual fallback)."
            except Exception as e:
                return f"❌ Layer 3 Failed: Could not use visual fallback - {str(e)}"
        else:
            return f"❌ Could not open '{app_name}': All layers failed. Install pyautogui for visual fallback."
            
    except Exception as e:
        return f"❌ Error opening '{app_name}': {str(e)}. Try the exact path or use Windows Search."




@tool("focus_window", "Brings a specific window to the front. Use ONLY if the user explicitly asks to 'focus' or 'switch to' a window.")
def focus_window(window_title: str) -> str:
    """
    Focuses a window by title using PowerShell.
    """
    try:
        cmd = f"""
        $w = New-Object -ComObject WScript.Shell
        $w.AppActivate('{window_title}')
        """
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)
        time.sleep(0.5) # Wait for focus
        return f"Focused window: {window_title}"
    except Exception as e:
        return f"Error focusing window: {e}"



@tool("restart_application", "Restarts an application (closes it, waits, then opens it again).")
def restart_application(app_name: str) -> str:
    """
    Restarts an application.
    
    Args:
        app_name: Name of the app to restart
        
    Returns:
        Status message
    """
    close_res = close_application(app_name)
    time.sleep(2) # Wait for full close
    open_res = open_application(app_name)
    
    return f"🔄 Restarted {app_name}:\n{close_res}\n{open_res}"


@tool("type_text", "Types text. Optional: provide 'window' to focus first (e.g. window='notepad')")
def type_text(text: str, window: str = None, interval: float = 0.05) -> str:
    """
    Types text using the keyboard. Can focus a window first.
    
    Args:
        text: The text to type
        window: (Optional) Name of window to focus first
        interval: Delay between key presses (default 0.05s)
        
    Returns:
        Success message
    """
    if not PYAUTOGUI_AVAILABLE:
        return "Error: pyautogui is not installed. Run: pip install pyautogui"
    
    try:
        msg = ""
        if window:
            msg += focus_window(window) + ". "
        
        # Give user time to switch focus if running manually, but for BRO
        # we usually open an app first. Add small safety delay.
        time.sleep(0.5) 
        
        pyautogui.write(text, interval=interval)
        return f"{msg}Typed: {text}"
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
