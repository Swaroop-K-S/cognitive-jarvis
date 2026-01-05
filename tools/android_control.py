"""
BRO Android Controller
Control your physical Android phone via ADB - 100% Local!

Features:
- Screen capture and mirroring
- Tap, swipe, type on phone
- App launching via intents (instant)
- Vision-based interaction (find and click elements)
- OCR text reading from screen

Requirements:
- USB Debugging enabled on phone
- ADB installed (comes with Android Platform Tools or Scrcpy)
- Phone connected via USB or WiFi ADB
"""

import os
import sys
import time
import json
import subprocess
from typing import Optional, Tuple, List
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================

# Pure Python ADB
PPADB_AVAILABLE = False
try:
    from ppadb.client import Client as AdbClient
    PPADB_AVAILABLE = True
except ImportError:
    pass

# OpenCV for image processing
CV2_AVAILABLE = False
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    pass

# PIL for image handling
PIL_AVAILABLE = False
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    pass

# =============================================================================
# CONFIGURATION
# =============================================================================

ADB_HOST = "127.0.0.1"
ADB_PORT = 5037

# Common app package names
APP_PACKAGES = {
    "whatsapp": "com.whatsapp",
    "whatsapp business": "com.whatsapp.w4b",
    "youtube": "com.google.android.youtube",
    "chrome": "com.android.chrome",
    "settings": "com.android.settings",
    "camera": "com.android.camera",
    "gallery": "com.google.android.apps.photos",
    "phone": "com.android.dialer",
    "messages": "com.google.android.apps.messaging",
    "gmail": "com.google.android.gm",
    "maps": "com.google.android.apps.maps",
    "spotify": "com.spotify.music",
    "instagram": "com.instagram.android",
    "twitter": "com.twitter.android",
    "telegram": "org.telegram.messenger",
    "facebook": "com.facebook.katana",
}

# =============================================================================
# ANDROID CONTROLLER
# =============================================================================

class AndroidController:
    """
    Controls a physical Android phone via ADB.
    Supports USB and WIRELESS (WiFi) connection.
    All operations are local - no cloud services.
    """
    
    def __init__(self, host: str = ADB_HOST, port: int = ADB_PORT):
        self.host = host
        self.port = port
        self.client = None
        self.device = None
        self.screen_size = (1080, 1920)  # Default, updated on connect
        self.wireless_ip = None
        
    def connect(self, device_ip: str = None) -> bool:
        """
        Connect to Android device.
        
        Args:
            device_ip: Optional IP for wireless connection (e.g., "192.168.1.100")
                      If None, connects to USB device
        """
        if not PPADB_AVAILABLE:
            print("[!] ppadb not installed. Run: pip install pure-python-adb")
            return False
        
        # Start ADB server
        self._start_adb_server()
        
        # If IP provided, connect wirelessly first
        if device_ip:
            return self.connect_wifi(device_ip)
        
        try:
            self.client = AdbClient(host=self.host, port=self.port)
            devices = self.client.devices()
            
            if not devices:
                print("[!] No Android device found!")
                print("    For USB: Connect phone and enable USB Debugging")
                print("    For WiFi: Use connect_wifi('PHONE_IP')")
                return False
            
            self.device = devices[0]
            print(f"[+] Connected to: {self.device.serial}")
            
            # Get screen size
            self._update_screen_size()
            return True
            
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False
    
    def connect_wifi(self, phone_ip: str, port: int = 5555) -> bool:
        """
        Connect to phone via WiFi ADB.
        
        Setup steps:
        1. Connect phone via USB once
        2. Run: adb tcpip 5555 (or use enable_wifi_mode())
        3. Disconnect USB
        4. Use this method with phone's IP
        
        Args:
            phone_ip: Phone's IP address (find in Settings > About Phone > IP)
            port: ADB port (default 5555)
        """
        print(f"[*] Connecting to {phone_ip}:{port} via WiFi...")
        
        try:
            # Use ADB command to connect
            result = subprocess.run(
                ["adb", "connect", f"{phone_ip}:{port}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "connected" in result.stdout.lower():
                print(f"[+] WiFi connected to {phone_ip}:{port}")
                self.wireless_ip = phone_ip
                
                # Now connect via ppadb
                self.client = AdbClient(host=self.host, port=self.port)
                devices = self.client.devices()
                
                if devices:
                    # Find the wireless device
                    for dev in devices:
                        if phone_ip in dev.serial:
                            self.device = dev
                            break
                    else:
                        self.device = devices[0]
                    
                    print(f"[+] Device ready: {self.device.serial}")
                    self._update_screen_size()
                    return True
            else:
                print(f"[!] WiFi connection failed: {result.stdout} {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("[!] ADB not found! Install Android Platform Tools")
            print("    Download: https://developer.android.com/studio/releases/platform-tools")
            return False
        except Exception as e:
            print(f"[!] WiFi connection error: {e}")
            return False
    
    def enable_wifi_mode(self, port: int = 5555) -> bool:
        """
        Enable WiFi debugging mode (requires USB connection first).
        After running this, you can disconnect USB and use connect_wifi().
        
        Returns the phone's IP address if successful.
        """
        try:
            # Enable tcpip mode
            result = subprocess.run(
                ["adb", "tcpip", str(port)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "restarting" in result.stdout.lower() or result.returncode == 0:
                print(f"[+] WiFi mode enabled on port {port}")
                
                # Try to get phone IP
                ip_result = subprocess.run(
                    ["adb", "shell", "ip route | grep wlan | awk '{print $9}'"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                phone_ip = ip_result.stdout.strip()
                if phone_ip:
                    print(f"[+] Phone IP: {phone_ip}")
                    print(f"    Now you can disconnect USB and run:")
                    print(f"    python android_control.py wifi {phone_ip}")
                    return True
                else:
                    print("[*] Phone IP not detected. Find it in:")
                    print("    Settings > About Phone > Status > IP Address")
                    return True
            else:
                print(f"[!] Failed to enable WiFi mode: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[!] Error enabling WiFi mode: {e}")
            return False
    
    def disconnect_wifi(self) -> bool:
        """Disconnect from WiFi ADB."""
        if self.wireless_ip:
            try:
                subprocess.run(
                    ["adb", "disconnect", f"{self.wireless_ip}:5555"],
                    capture_output=True,
                    timeout=5
                )
                print(f"[+] Disconnected from {self.wireless_ip}")
                self.wireless_ip = None
                self.device = None
                return True
            except:
                pass
        return False
    
    def _start_adb_server(self):
        """Start ADB server if not running."""
        try:
            subprocess.run(["adb", "start-server"], capture_output=True, timeout=5)
        except:
            pass
    
    def _update_screen_size(self):
        """Get the phone's screen resolution."""
        try:
            result = self.device.shell("wm size")
            # Output: "Physical size: 1080x1920"
            if "x" in result:
                size_str = result.split(":")[-1].strip()
                width, height = map(int, size_str.split("x"))
                self.screen_size = (width, height)
        except:
            pass
    
    # =========================================================================
    # SCREEN CAPTURE
    # =========================================================================
    
    def capture_screen(self, save_path: str = None) -> Optional[bytes]:
        """
        Capture the phone screen.
        
        Args:
            save_path: Optional path to save the screenshot
            
        Returns:
            PNG image bytes
        """
        if not self.device:
            return None
        
        try:
            image_bytes = self.device.screencap()
            
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(image_bytes)
            
            return image_bytes
        except Exception as e:
            print(f"[!] Screenshot failed: {e}")
            return None
    
    def get_screen_image(self):
        """Get screen as PIL Image (resized for AI efficiency)."""
        if not PIL_AVAILABLE:
            return None
        
        img_bytes = self.capture_screen()
        if not img_bytes:
            return None
        
        image = Image.open(BytesIO(img_bytes))
        
        # Resize for AI (512x512 is ideal for vision models)
        image.thumbnail((512, 512), Image.Resampling.LANCZOS)
        return image
    
    # =========================================================================
    # INPUT ACTIONS
    # =========================================================================
    
    def tap(self, x: int, y: int) -> bool:
        """
        Tap at screen coordinates.
        
        Args:
            x: X coordinate (0 to screen_width)
            y: Y coordinate (0 to screen_height)
        """
        if not self.device:
            return False
        
        try:
            self.device.shell(f"input tap {x} {y}")
            return True
        except Exception as e:
            print(f"[!] Tap failed: {e}")
            return False
    
    def tap_percent(self, x_pct: float, y_pct: float) -> bool:
        """
        Tap at percentage of screen (0.0 to 1.0).
        Useful for AI models that output normalized coordinates.
        """
        x = int(x_pct * self.screen_size[0])
        y = int(y_pct * self.screen_size[1])
        return self.tap(x, y)
    
    def long_press(self, x: int, y: int, duration_ms: int = 1000) -> bool:
        """Long press at coordinates."""
        if not self.device:
            return False
        
        try:
            self.device.shell(f"input swipe {x} {y} {x} {y} {duration_ms}")
            return True
        except:
            return False
    
    def swipe(self, direction: str = "up", duration_ms: int = 300) -> bool:
        """
        Swipe/scroll the screen.
        
        Args:
            direction: "up", "down", "left", "right"
            duration_ms: Swipe duration in milliseconds
        """
        if not self.device:
            return False
        
        w, h = self.screen_size
        cx, cy = w // 2, h // 2
        
        coords = {
            "up": (cx, int(h * 0.7), cx, int(h * 0.3)),
            "down": (cx, int(h * 0.3), cx, int(h * 0.7)),
            "left": (int(w * 0.8), cy, int(w * 0.2), cy),
            "right": (int(w * 0.2), cy, int(w * 0.8), cy),
        }
        
        if direction not in coords:
            return False
        
        x1, y1, x2, y2 = coords[direction]
        
        try:
            self.device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
            return True
        except:
            return False
    
    def type_text(self, text: str) -> bool:
        """
        Type text on the phone.
        Note: Special characters may not work well.
        """
        if not self.device:
            return False
        
        # Escape special characters for ADB
        # Replace spaces with %s, special chars need escaping
        safe_text = text.replace(" ", "%s")
        safe_text = safe_text.replace("'", "\\'")
        safe_text = safe_text.replace('"', '\\"')
        safe_text = safe_text.replace("&", "\\&")
        safe_text = safe_text.replace("<", "\\<")
        safe_text = safe_text.replace(">", "\\>")
        safe_text = safe_text.replace(";", "\\;")
        safe_text = safe_text.replace("|", "\\|")
        
        try:
            self.device.shell(f"input text '{safe_text}'")
            return True
        except Exception as e:
            print(f"[!] Type failed: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """
        Press a key/button.
        
        Keys: home, back, menu, enter, delete, tab, space, 
              volume_up, volume_down, power, camera
        """
        key_codes = {
            "home": 3,
            "back": 4,
            "menu": 82,
            "enter": 66,
            "delete": 67,
            "backspace": 67,
            "tab": 61,
            "space": 62,
            "volume_up": 24,
            "volume_down": 25,
            "power": 26,
            "camera": 27,
            "search": 84,
            "play_pause": 85,
            "mute": 91,
        }
        
        key_lower = key.lower()
        if key_lower not in key_codes:
            print(f"[!] Unknown key: {key}")
            return False
        
        if not self.device:
            return False
        
        try:
            self.device.shell(f"input keyevent {key_codes[key_lower]}")
            return True
        except:
            return False
    
    # =========================================================================
    # APP CONTROL
    # =========================================================================
    
    def open_app(self, app_name: str) -> bool:
        """
        Open an app by name.
        Uses package intents for instant launch (no vision needed).
        """
        if not self.device:
            return False
        
        app_lower = app_name.lower()
        
        # Check if we know the package
        package = APP_PACKAGES.get(app_lower)
        
        if not package:
            # Try partial match
            for name, pkg in APP_PACKAGES.items():
                if app_lower in name or name in app_lower:
                    package = pkg
                    break
        
        if package:
            try:
                # Use monkey to launch (works reliably)
                self.device.shell(f"monkey -p {package} -c android.intent.category.LAUNCHER 1")
                print(f"[+] Launched: {package}")
                return True
            except Exception as e:
                print(f"[!] Launch failed: {e}")
                return False
        else:
            print(f"[!] Unknown app: {app_name}")
            print(f"    Known apps: {', '.join(APP_PACKAGES.keys())}")
            return False
    
    def close_app(self, app_name: str) -> bool:
        """Force stop an app."""
        if not self.device:
            return False
        
        package = APP_PACKAGES.get(app_name.lower())
        if not package:
            return False
        
        try:
            self.device.shell(f"am force-stop {package}")
            return True
        except:
            return False
    
    def go_home(self) -> bool:
        """Press the home button."""
        return self.press_key("home")
    
    def go_back(self) -> bool:
        """Press the back button."""
        return self.press_key("back")
    
    # =========================================================================
    # ADVANCED: SMART ELEMENT INTERACTION (XML-first, Vision fallback)
    # =========================================================================
    
    def _get_ui_hierarchy(self) -> str:
        """
        Get the UI hierarchy XML using UIAutomator dump.
        This is MUCH faster than vision (~0.3s vs ~3-5s).
        """
        if not self.device:
            return ""
        
        try:
            # Dump UI hierarchy to stdout (faster than file)
            result = self.device.shell("uiautomator dump /dev/tty")
            # Extract XML content
            if "<?xml" in result:
                start = result.find("<?xml")
                return result[start:].strip()
            return result
        except Exception as e:
            print(f"[!] UIAutomator dump failed: {e}")
            return ""
    
    def _find_bounds_in_xml(self, xml_content: str, target_text: str) -> Optional[Tuple[int, int]]:
        """
        Find element bounds in UI hierarchy XML.
        
        Args:
            xml_content: UIAutomator XML dump
            target_text: Text to find (case-insensitive partial match)
            
        Returns:
            (x, y) center coordinates or None if not found
        """
        import re
        
        target_lower = target_text.lower()
        
        # Pattern to find elements with text/content-desc and their bounds
        # Example: text="Settings" bounds="[0,100][200,200]"
        pattern = r'(?:text|content-desc)="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        
        for match in re.finditer(pattern, xml_content, re.IGNORECASE):
            element_text = match.group(1).lower()
            if target_lower in element_text or element_text in target_lower:
                x1, y1 = int(match.group(2)), int(match.group(3))
                x2, y2 = int(match.group(4)), int(match.group(5))
                # Return center of element
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                return (center_x, center_y)
        
        # Also try resource-id matching
        pattern_id = r'resource-id="[^"]*([^"/]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        for match in re.finditer(pattern_id, xml_content, re.IGNORECASE):
            element_id = match.group(1).lower()
            if target_lower in element_id:
                x1, y1 = int(match.group(2)), int(match.group(3))
                x2, y2 = int(match.group(4)), int(match.group(5))
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                return (center_x, center_y)
        
        return None
    
    def smart_tap(self, target: str) -> bool:
        """
        Smart element tap - uses XML first (fast), vision fallback (slow).
        
        This is ~6x faster than pure vision for most cases.
        
        Args:
            target: Text/description of element to tap
            
        Returns:
            True if tap succeeded
        """
        # =====================================================================
        # LAYER 1: XML DUMP (Fast - ~0.3s)
        # =====================================================================
        print(f"[*] Looking for: '{target}'")
        xml = self._get_ui_hierarchy()
        
        if xml:
            coords = self._find_bounds_in_xml(xml, target)
            if coords:
                x, y = coords
                print(f"[+] Found via XML at ({x}, {y})")
                return self.tap(x, y)
            print(f"[*] Not in XML, trying vision...")
        
        # =====================================================================
        # LAYER 2: VISION MODEL (Slow - ~3-5s, but finds anything)
        # =====================================================================
        return self._find_and_tap_vision(target)
    
    def find_and_tap(self, description: str) -> bool:
        """
        Find an element and tap it. Uses smart detection (XML + Vision).
        
        Args:
            description: What to look for (e.g., "send button", "search box")
        """
        return self.smart_tap(description)
    
    def _find_and_tap_vision(self, description: str) -> bool:
        """
        Use AI vision model to find an element and tap it.
        This is slower but can find any visual element.
        
        Args:
            description: What to look for
        """
        import urllib.request
        import base64
        
        # Capture screen
        img_bytes = self.capture_screen()
        if not img_bytes:
            return False
        
        # Convert to base64
        img_b64 = base64.b64encode(img_bytes).decode()
        
        # Ask vision model
        prompt = f"""Look at this Android phone screenshot. 
Find the element matching: "{description}"
Reply with ONLY the tap coordinates as: TAP X Y
Where X and Y are pixel coordinates.
If not found, reply: NOT_FOUND"""
        
        try:
            payload = json.dumps({
                "model": "moondream",  # Lightweight vision model
                "messages": [{
                    "role": "user",
                    "content": prompt,
                    "images": [img_b64]
                }],
                "stream": False
            }).encode()
            
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                response = result["message"]["content"]
                
                if "TAP" in response:
                    parts = response.split()
                    x_idx = parts.index("TAP") + 1
                    x, y = int(parts[x_idx]), int(parts[x_idx + 1])
                    print(f"[+] Found via Vision at ({x}, {y})")
                    return self.tap(x, y)
                else:
                    print(f"[!] Element not found: {description}")
                    return False
                    
        except Exception as e:
            print(f"[!] Vision error: {e}")
            return False
    
    def get_screen_elements(self) -> List[dict]:
        """
        Get all visible elements on screen from XML hierarchy.
        Useful for debugging or listing what's tappable.
        
        Returns:
            List of elements with text and bounds
        """
        import re
        xml = self._get_ui_hierarchy()
        if not xml:
            return []
        
        elements = []
        pattern = r'(?:text|content-desc)="([^"]+)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
        
        for match in re.finditer(pattern, xml, re.IGNORECASE):
            text = match.group(1)
            if text.strip():
                x1, y1 = int(match.group(2)), int(match.group(3))
                x2, y2 = int(match.group(4)), int(match.group(5))
                elements.append({
                    "text": text,
                    "bounds": (x1, y1, x2, y2),
                    "center": ((x1+x2)//2, (y1+y2)//2)
                })
        
        return elements
    
    def read_screen_text(self) -> str:
        """Read text from the current screen using AI."""
        import urllib.request
        import base64
        
        img_bytes = self.capture_screen()
        if not img_bytes:
            return ""
        
        img_b64 = base64.b64encode(img_bytes).decode()
        
        try:
            payload = json.dumps({
                "model": "moondream",
                "messages": [{
                    "role": "user",
                    "content": "Read all visible text on this phone screen. List the main content.",
                    "images": [img_b64]
                }],
                "stream": False
            }).encode()
            
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result["message"]["content"]
        except:
            return ""
    
    # =========================================================================
    # STATUS
    # =========================================================================
    
    def get_status(self) -> dict:
        """Get connection status."""
        return {
            "connected": self.device is not None,
            "device": self.device.serial if self.device else None,
            "screen_size": self.screen_size,
        }


# =============================================================================
# BRO TOOLS
# =============================================================================

# Global controller instance
_controller = None

def get_controller() -> AndroidController:
    """Get or create the Android controller."""
    global _controller
    if _controller is None or _controller.device is None:
        _controller = AndroidController()
        _controller.connect()
    return _controller


def android_status() -> dict:
    """Get Android controller status."""
    return {
        "ppadb_available": PPADB_AVAILABLE,
        "cv2_available": CV2_AVAILABLE,
        "pil_available": PIL_AVAILABLE,
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Android Controller - USB or WIRELESS")
    parser.add_argument("command", nargs="?", default="status",
                       help="Command: status, wifi, enable-wifi, connect, tap, swipe, open, type")
    parser.add_argument("args", nargs="*", help="Command arguments")
    
    args = parser.parse_args()
    
    ctrl = AndroidController()
    
    if args.command == "status":
        print("\n=== Android Controller Status ===")
        print(f"ppadb: {'OK' if PPADB_AVAILABLE else 'Missing'}")
        print(f"opencv: {'OK' if CV2_AVAILABLE else 'Missing'}")
        print(f"PIL: {'OK' if PIL_AVAILABLE else 'Missing'}")
        
        if ctrl.connect():
            print(f"\nDevice: {ctrl.device.serial}")
            print(f"Screen: {ctrl.screen_size[0]}x{ctrl.screen_size[1]}")
            print(f"Mode: {'WiFi' if ':' in ctrl.device.serial else 'USB'}")
    
    elif args.command == "wifi":
        # Connect via WiFi
        if args.args:
            phone_ip = args.args[0]
            port = int(args.args[1]) if len(args.args) > 1 else 5555
            ctrl.connect_wifi(phone_ip, port)
        else:
            print("Usage: python android_control.py wifi <PHONE_IP> [PORT]")
            print("\nTo find your phone's IP:")
            print("  Settings > About Phone > Status > IP Address")
            print("\nFirst-time setup (requires USB once):")
            print("  python android_control.py enable-wifi")
    
    elif args.command in ["enable-wifi", "enablewifi", "wifi-setup"]:
        # Enable WiFi debugging mode (requires USB)
        print("=== Enable WiFi Debugging ===")
        print("This requires your phone to be connected via USB first.\n")
        ctrl.enable_wifi_mode()
    
    elif args.command == "disconnect":
        ctrl.disconnect_wifi()
    
    elif args.command == "connect":
        if args.args:
            # IP provided = wireless
            ctrl.connect_wifi(args.args[0])
        else:
            ctrl.connect()
    
    elif args.command == "screen":
        if ctrl.connect():
            ctrl.capture_screen("phone_screen.png")
            print("Screenshot saved: phone_screen.png")
    
    elif args.command == "open":
        if args.args and ctrl.connect():
            ctrl.open_app(" ".join(args.args))
    
    elif args.command == "tap":
        if len(args.args) >= 2 and ctrl.connect():
            x, y = int(args.args[0]), int(args.args[1])
            ctrl.tap(x, y)
            print(f"Tapped: {x}, {y}")
    
    elif args.command == "swipe":
        direction = args.args[0] if args.args else "up"
        if ctrl.connect():
            ctrl.swipe(direction)
            print(f"Swiped: {direction}")
    
    elif args.command == "type":
        if args.args and ctrl.connect():
            ctrl.type_text(" ".join(args.args))
    
    elif args.command == "home":
        if ctrl.connect():
            ctrl.go_home()
    
    elif args.command == "back":
        if ctrl.connect():
            ctrl.go_back()
    
    else:
        print("""
=== BRO Android Controller ===

USB Commands:
  status              - Check connection and device info
  connect             - Connect to USB device
  screen              - Take screenshot

WiFi Commands (NO USB NEEDED after setup):
  enable-wifi         - Enable WiFi mode (requires USB once)
  wifi <IP> [PORT]    - Connect wirelessly to phone
  disconnect          - Disconnect WiFi

Control Commands (work with USB or WiFi):
  open <app>          - Open app (youtube, whatsapp, chrome, etc.)
  tap <X> <Y>         - Tap at coordinates
  swipe <direction>   - Swipe up/down/left/right
  type <text>         - Type text
  home                - Press home button
  back                - Press back button

Examples:
  python android_control.py enable-wifi      # First time: enable WiFi mode
  python android_control.py wifi 192.168.1.5 # Connect wirelessly
  python android_control.py open youtube     # Open YouTube
  python android_control.py swipe up         # Scroll down
""")


if __name__ == "__main__":
    main()
