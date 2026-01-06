"""
Screen Copilot: The "Eye" of Jarvis.
Passive monitoring & Active takeover capabilities.
"""
import time
import threading
import base64
import os
import sys
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Handle dependencies
try:
    import pyautogui
except ImportError:
    pyautogui = None
    
try:
    from PIL import Image
except ImportError:
    Image = None

# Import existing tools
from tools.pc_control import type_text, press_key, take_screenshot as capture_screen_file

# Try to import smart shopping, but don't fail if missing
try:
    from tools.smart_shopping import get_product_details, find_better_price
    SHOPPING_AVAILABLE = True
except ImportError:
    SHOPPING_AVAILABLE = False
    def get_product_details(*args): return "Shopping tool unavailable"
    def find_better_price(*args): return "Shopping tool unavailable"

from llm.cognitive_brain import CognitiveBrain

class ScreenCopilot:
    def __init__(self, brain: CognitiveBrain):
        self.brain = brain
        self.active_mode = False  # If True, Jarvis is clicking/typing
        self.monitoring = False   # If True, Jarvis is just watching
        self.last_context = "unknown"
        
    def start_monitoring(self):
        """Starts the passive background eye."""
        if not pyautogui:
            print("❌ Copilot requires pyautogui. Install it first.")
            return
            
        self.monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        print("👀 Copilot is watching your screen...")

    def stop_monitoring(self):
        self.monitoring = False

    def _capture_screen(self):
        """Captures screen in memory (fast)."""
        if not pyautogui:
            return None
            
        screenshot = pyautogui.screenshot()
        img_buffer = BytesIO()
        screenshot.save(img_buffer, format="JPEG", quality=50) # Low quality for speed
        return base64.b64encode(img_buffer.getvalue()).decode('utf-8')

    def _monitor_loop(self):
        """Passive Loop: Runs every 10s to check context."""
        while self.monitoring:
            if self.active_mode: 
                time.sleep(1) # Don't interfere if Active
                continue
                
            # 1. Take a quick look
            b64_img = self._capture_screen()
            if not b64_img:
                time.sleep(10)
                continue
            
            try:
                # 2. Fast Context Check (Is user shopping? Coding?)
                # We use a tiny prompt to save GPU
                context = self.brain.think_fast(
                    "Look at this screen. Are we: 'coding', 'shopping', 'gaming', or 'idle'? Return 1 word.",
                    image=b64_img
                )
                
                self.last_context = context.lower().strip()
                
                # 3. Proactive Help Logic
                # 3. Proactive Help Logic
                if "shopping" in self.last_context and SHOPPING_AVAILABLE:
                    # Extract product name from screen
                    product = self.brain.think_fast(
                        "What specific product is on screen? Return JUST the product name or 'none'.",
                        image=b64_img
                    )
                    
                    if product.lower() != "none" and len(product) > 3:
                        print(f"    🛍️ Shopping detected: {product}")
                        # findings = find_better_price(product)  # Save resources for now, just log
                        # print(f"    💡 Finding: {findings[:50]}...")
                        print(f"    💡 I could look for better prices for '{product}'...")

                elif "coding" in self.last_context:
                    # If we see red squiggly lines (errors), maybe log it
                    pass
            except Exception as e:
                print(f"    ⚠️ Copilot monitor error: {e}")
                
            time.sleep(10) # Wait 10s

    def take_over_task(self, task_description):
        """
        ACTIVE MODE: Jarvis takes control of mouse/keyboard.
        """
        if not pyautogui:
            return "❌ Copilot requires pyautogui."

        print(f"🤖 TAKING OVER: {task_description}")
        self.active_mode = True
        
        try:
            for i in range(10): # Safety limit: 10 steps max
                # 1. See
                b64_img = self._capture_screen()
                
                # 2. Think (Chain of Thought)
                prompt = f"""
                GOAL: {task_description}
                CURRENT SCREEN: (See image)
                
                What is the ONE next step?
                Return JSON in this format:
                {{
                    "thought": "I need to click the search bar",
                    "tool": "click" | "type" | "done",
                    "args": [x, y] or "text to type"
                }}
                Be precise with coordinates [x, y] or text.
                """
                
                # Ask Brain (Using Vision Model)
                response_str = self.brain.think_with_vision(prompt, b64_img)
                
                # 3. Parse and Execute
                try:
                    import json
                    # Clean up response to get valid JSON
                    json_str = response_str.strip()
                    if "```json" in json_str:
                        json_str = json_str.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_str:
                        json_str = json_str.split("```")[1].split("```")[0].strip()
                    
                    action = json.loads(json_str)
                    
                    thought = action.get("thought", "Executing step...")
                    tool_name = action.get("tool", "").lower()
                    args = action.get("args", [])
                    
                    print(f"    🤖 Step {i+1}: {thought}")
                    
                    if tool_name == "done":
                        print("    ✅ Task completed.")
                        break
                    
                    elif tool_name == "click":
                        if len(args) >= 2:
                            x, y = args[0], args[1]
                            print(f"      🖱️ Clicking at ({x}, {y})")
                            pyautogui.moveTo(x, y, duration=0.5)
                            pyautogui.click()
                        else:
                            print("      ❌ Invalid click coords")
                            
                    elif tool_name == "type":
                        text = args if isinstance(args, str) else str(args[0])
                        print(f"      ⌨️ Typing: '{text}'")
                        pyautogui.write(text, interval=0.05)
                        
                    elif tool_name == "press":
                        key = args if isinstance(args, str) else str(args[0])
                        print(f"      🎹 Pressing: {key}")
                        pyautogui.press(key)
                        
                    elif tool_name == "scroll":
                        amount = int(args if isinstance(args, (int, float)) else args[0])
                        print(f"      📜 Scrolling {amount}")
                        pyautogui.scroll(amount)
                        
                    else:
                        print(f"      ❓ Unknown tool: {tool_name}")
                        
                except Exception as e:
                    print(f"    ⚠️ Failed to parse/execute step: {e}")
                    # If parsing fails, simple heuristic fallback or retry
                    if "done" in response_str.lower(): break
                
                time.sleep(2) # Wait for UI to update
                
        except Exception as e:
            print(f"❌ Takeover failed: {e}")
        finally:
            self.active_mode = False
            print("🤖 Control returned to human.")


# Integration Helper
_global_copilot = None

def get_copilot(brain=None):
    global _global_copilot
    if not _global_copilot and brain:
        _global_copilot = ScreenCopilot(brain)
    return _global_copilot

# =============================================================================
# REGISTRY TOOLS
# =============================================================================
from .registry import tool

@tool("enable_screen_copilot", "Activate the autonomous screen copilot to monitor and help passively.")
def enable_screen_copilot() -> str:
    """
    Turns on the background screen monitoring loop.
    Jarvis will watch for context (shopping, coding) and offer help.
    """
    copilot = get_copilot()
    if not copilot:
        return "❌ System Error: Copilot not initialized with Brain instance."
    
    copilot.start_monitoring()
    return "👁️ Copilot activated. I am watching your screen for ways to help."

@tool("disable_screen_copilot", "Turn off screen monitoring.")
def disable_screen_copilot() -> str:
    """Stops the background monitoring loop."""
    copilot = get_copilot()
    if not copilot:
        return "Copilot not initialized."
        
    copilot.stop_monitoring()
    return "Copilot deactivated."

@tool("take_over_screen", "Grant full control to Jarvis to finish a task on screen.")
def take_over_screen(task: str) -> str:
    """
    Active takeover mode.
    
    Args:
        task: Description of what to do (e.g. "Finish this python function", "Buy this item")
    """
    copilot = get_copilot()
    if not copilot:
        return "❌ Copilot not initialized."
    
    # Run in thread to not block main API response
    threading.Thread(target=copilot.take_over_task, args=(task,)).start()
    return f"🤖 Taking over to: {task}. Please let go of the mouse."

