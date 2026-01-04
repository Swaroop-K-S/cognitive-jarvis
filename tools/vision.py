"""
BRO Vision System
Enables BRO to "see" the screen using Ollama + LLaVA (local multimodal model).
Also includes Tesseract OCR fallback for text-heavy content.
"""

import base64
import json
import os
import sys
import urllib.request
from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Handle imports gracefully
VISION_DEPS_AVAILABLE = False
Image = None
try:
    import pyautogui
    from PIL import Image as PILImage
    Image = PILImage
    VISION_DEPS_AVAILABLE = True
except ImportError:
    pass

OCR_AVAILABLE = False
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    pass

from config import OLLAMA_HOST
from .registry import tool

# Vision model configuration - supports llava, moondream, bakllava
VISION_MODEL = os.getenv("VISION_MODEL", "moondream")  # moondream is lightweight


def _capture_screen(region: Optional[Tuple[int, int, int, int]] = None):
    """Capture the screen or a region of it."""
    if not VISION_DEPS_AVAILABLE:
        return None
    try:
        screenshot = pyautogui.screenshot(region=region)
        return screenshot
    except Exception as e:
        print(f"❌ Screenshot error: {e}")
        return None


def _image_to_base64(image, max_size: int = 1024) -> str:
    """Convert PIL Image to base64 string, resizing if needed for efficiency."""
    # Resize large images to reduce payload size
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
    
    # Convert to JPEG for smaller size
    buffer = BytesIO()
    if image.mode == 'RGBA':
        image = image.convert('RGB')
    image.save(buffer, format='JPEG', quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def _call_llava(prompt: str, image_base64: str) -> str:
    """Call Ollama's LLaVA model with an image."""
    try:
        payload = {
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 300
            }
        }
        
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response", "I couldn't analyze the image.")
    
    except urllib.error.URLError:
        return "❌ Vision unavailable: Ollama not running or LLaVA not installed. Run: ollama pull llava"
    except Exception as e:
        return f"❌ Vision error: {str(e)}"


def _check_llava_available() -> bool:
    """Check if LLaVA model is available in Ollama."""
    try:
        req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            return VISION_MODEL.split(":")[0] in models
    except:
        return False


@tool("analyze_screen", "Analyzes what's currently visible on the screen. Use for 'what's on my screen', 'describe what you see', etc.")
def analyze_screen(question: str = "Describe what you see on this screen in detail.") -> str:
    """
    Captures the screen and uses LLaVA to describe what's visible.
    
    Args:
        question: What to analyze about the screen (default: general description)
        
    Returns:
        Natural language description of the screen contents
    """
    if not VISION_DEPS_AVAILABLE:
        return "❌ Vision not available: Install pyautogui and Pillow"
    
    if not _check_llava_available():
        return "❌ LLaVA model not found. Install with: ollama pull llava"
    
    # Capture screen
    screenshot = _capture_screen()
    if screenshot is None:
        return "❌ Could not capture screen"
    
    # Convert to base64
    image_b64 = _image_to_base64(screenshot)
    
    # Analyze with LLaVA
    prompt = f"""You are BRO, an AI assistant analyzing a computer screen.
{question}

Be concise but helpful. Focus on:
- What application/window is open
- Key content visible (text, images, UI elements)
- Anything that seems relevant to what the user might want to do

Keep your response under 100 words."""

    return _call_llava(prompt, image_b64)


@tool("find_on_screen", "Finds a specific element or text on the screen. Use for 'find the save button', 'where is the search box', etc.")
def find_on_screen(description: str) -> str:
    """
    Uses vision to locate a specific UI element or text on screen.
    
    Args:
        description: What to find (e.g., "the save button", "search box", "close icon")
        
    Returns:
        Description of where the element is located, or if it's not found
    """
    if not VISION_DEPS_AVAILABLE:
        return "❌ Vision not available: Install pyautogui and Pillow"
    
    if not _check_llava_available():
        return "❌ LLaVA model not found. Install with: ollama pull llava"
    
    screenshot = _capture_screen()
    if screenshot is None:
        return "❌ Could not capture screen"
    
    image_b64 = _image_to_base64(screenshot, max_size=1280)
    
    prompt = f"""You are BRO helping locate something on a computer screen.
Find: "{description}"

If you can see it:
1. Describe its exact location (top-left, center, bottom-right, etc.)
2. Describe what's near it for reference
3. Describe what it looks like

If you cannot find it:
1. Say it's not visible
2. Suggest what the user might need to do (scroll, open a menu, etc.)

Be brief and precise."""

    return _call_llava(prompt, image_b64)


@tool("read_screen_text", "Reads and extracts all visible text from the screen using OCR.")
def read_screen_text(region: str = None) -> str:
    """
    Uses OCR to extract text from the screen.
    Faster than LLaVA for pure text extraction.
    
    Args:
        region: Optional region description (not implemented yet - captures full screen)
        
    Returns:
        Extracted text from the screen
    """
    if not VISION_DEPS_AVAILABLE:
        return "❌ Vision not available: Install pyautogui and Pillow"
    
    screenshot = _capture_screen()
    if screenshot is None:
        return "❌ Could not capture screen"
    
    # Try OCR first (faster for text)
    if OCR_AVAILABLE:
        try:
            text = pytesseract.image_to_string(screenshot)
            if text.strip():
                return f"📝 Screen text:\n{text.strip()}"
        except Exception as e:
            pass  # Fall through to LLaVA
    
    # Fallback to LLaVA
    if _check_llava_available():
        image_b64 = _image_to_base64(screenshot)
        prompt = "Read and transcribe ALL text visible on this screen. Just output the text, nothing else."
        return _call_llava(prompt, image_b64)
    
    return "❌ OCR not available (install pytesseract) and LLaVA not running"


@tool("describe_image", "Analyzes and describes an image file.")
def describe_image(image_path: str, question: str = "Describe this image in detail.") -> str:
    """
    Analyzes an image file using LLaVA.
    
    Args:
        image_path: Path to the image file
        question: What to analyze about the image
        
    Returns:
        Description of the image
    """
    if not VISION_DEPS_AVAILABLE:
        return "❌ Vision not available: Install Pillow"
    
    if not os.path.exists(image_path):
        return f"❌ Image not found: {image_path}"
    
    if not _check_llava_available():
        return "❌ LLaVA model not found. Install with: ollama pull llava"
    
    try:
        image = Image.open(image_path)
        image_b64 = _image_to_base64(image)
        return _call_llava(question, image_b64)
    except Exception as e:
        return f"❌ Error loading image: {str(e)}"


@tool("save_screenshot", "Takes a screenshot and saves it to a file.")
def save_screenshot(filename: str = None, region: str = None) -> str:
    """
    Takes a screenshot and saves it.
    
    Args:
        filename: Optional filename (default: screenshot_TIMESTAMP.png)
        region: Optional region (not implemented - full screen)
        
    Returns:
        Path where screenshot was saved
    """
    if not VISION_DEPS_AVAILABLE:
        return "❌ Screenshot not available: Install pyautogui"
    
    screenshot = _capture_screen()
    if screenshot is None:
        return "❌ Could not capture screen"
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pictures_folder = os.path.expanduser("~\\Pictures")
        filename = os.path.join(pictures_folder, f"screenshot_{timestamp}.png")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    try:
        screenshot.save(filename)
        return f"✓ Screenshot saved: {filename}"
    except Exception as e:
        return f"❌ Error saving screenshot: {str(e)}"


# Quick status check
def vision_status() -> dict:
    """Get the status of vision capabilities."""
    return {
        "vision_deps": VISION_DEPS_AVAILABLE,
        "ocr_available": OCR_AVAILABLE,
        "llava_available": _check_llava_available(),
        "vision_model": VISION_MODEL
    }
