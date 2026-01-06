"""
BRO OCR - Text Reading from Images/Videos
Uses multiple backends: EasyOCR (offline), Tesseract, or LLaVA vision.
"""

import os
import sys
import json
import base64
import urllib.request
from typing import List, Dict, Optional, Tuple
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import OCR libraries
EASYOCR_AVAILABLE = False
TESSERACT_AVAILABLE = False
CV2_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    pass

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    pass

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# =============================================================================
# OCR READER
# =============================================================================

class OCRReader:
    """
    Multi-backend OCR reader.
    Priority: EasyOCR > Tesseract > LLaVA Vision
    """
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize OCR reader.
        
        Args:
            languages: List of language codes (e.g., ['en', 'hi'] for English and Hindi)
        """
        self.languages = languages or ['en']
        self._easyocr_reader = None
    
    def _get_easyocr(self):
        """Lazy load EasyOCR reader."""
        if self._easyocr_reader is None and EASYOCR_AVAILABLE:
            print("📥 Loading EasyOCR model (first time may take a moment)...")
            self._easyocr_reader = easyocr.Reader(self.languages, gpu=True)
        return self._easyocr_reader
    
    def read_easyocr(self, image_path: str) -> List[Dict]:
        """
        Read text using EasyOCR (best for most cases).
        Returns list of detected text with positions and confidence.
        """
        reader = self._get_easyocr()
        if not reader:
            return []
        
        results = reader.readtext(image_path)
        
        extracted = []
        for bbox, text, confidence in results:
            extracted.append({
                "text": text,
                "confidence": round(confidence, 2),
                "position": bbox
            })
        
        return extracted
    
    def read_tesseract(self, image_path: str) -> str:
        """Read text using Tesseract OCR."""
        if not TESSERACT_AVAILABLE:
            return ""
        
        if PIL_AVAILABLE:
            image = Image.open(image_path)
            return pytesseract.image_to_string(image)
        elif CV2_AVAILABLE:
            image = cv2.imread(image_path)
            return pytesseract.image_to_string(image)
        
        return ""
    
    def read_llava(self, image_path: str) -> str:
        """Use LLaVA vision model for OCR (fallback)."""
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            
            prompt = """OCR Task: Read and transcribe ALL visible text in this image.
            
Rules:
1. Extract EVERY piece of text you can see
2. Include numbers, prices, labels, buttons
3. Maintain the original formatting where possible
4. Separate different text areas with newlines

Output the extracted text directly, nothing else."""
            
            payload = json.dumps({
                "model": "llava:7b",
                "messages": [{"role": "user", "content": prompt, "images": [img_b64]}],
                "stream": False,
                "options": {"temperature": 0.1}
            }).encode()
            
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                return result["message"]["content"]
        
        except Exception as e:
            return f"Error: {e}"
    
    def read(self, image_path: str, method: str = "auto") -> str:
        """
        Read text from image using best available method.
        
        Args:
            image_path: Path to image
            method: "auto", "easyocr", "tesseract", or "llava"
        """
        if method == "auto":
            if EASYOCR_AVAILABLE:
                method = "easyocr"
            elif TESSERACT_AVAILABLE:
                method = "tesseract"
            else:
                method = "llava"
        
        if method == "easyocr":
            results = self.read_easyocr(image_path)
            return "\n".join([r["text"] for r in results])
        elif method == "tesseract":
            return self.read_tesseract(image_path)
        else:
            return self.read_llava(image_path)
    
    def read_detailed(self, image_path: str) -> Dict:
        """
        Read text with detailed information (position, confidence).
        Only works with EasyOCR.
        """
        if not EASYOCR_AVAILABLE:
            text = self.read(image_path, "auto")
            return {"text": text, "items": [], "method": "fallback"}
        
        results = self.read_easyocr(image_path)
        full_text = "\n".join([r["text"] for r in results])
        
        return {
            "text": full_text,
            "items": results,
            "method": "easyocr"
        }


# =============================================================================
# VIDEO OCR
# =============================================================================

def read_video_text(video_path: str, max_frames: int = 5) -> Dict:
    """
    Extract text from video frames.
    
    Args:
        video_path: Path to video file
        max_frames: Number of frames to process
    """
    if not CV2_AVAILABLE:
        return {"error": "OpenCV required. Run: pip install opencv-python"}
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": f"Cannot open video: {video_path}"}
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(1, total_frames // max_frames)
    
    reader = OCRReader()
    all_text = []
    frame_results = []
    
    frame_idx = 0
    processed = 0
    
    import tempfile
    
    while processed < max_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Save frame temporarily
        temp_path = os.path.join(tempfile.gettempdir(), f"ocr_frame_{processed}.jpg")
        cv2.imwrite(temp_path, frame)
        
        # Read text
        text = reader.read(temp_path)
        
        if text.strip():
            frame_results.append({
                "frame": frame_idx,
                "text": text
            })
            all_text.append(text)
        
        # Clean up
        try:
            os.remove(temp_path)
        except:
            pass
        
        frame_idx += interval
        processed += 1
    
    cap.release()
    
    # Combine and deduplicate text
    unique_text = list(set("\n".join(all_text).split("\n")))
    unique_text = [t.strip() for t in unique_text if t.strip()]
    
    return {
        "all_text": unique_text,
        "frames": frame_results,
        "frame_count": len(frame_results)
    }


# =============================================================================
# CONVENIENCE FUNCTIONS  
# =============================================================================

_reader = None

def get_reader(languages: List[str] = None) -> OCRReader:
    """Get or create OCR reader."""
    global _reader
    if _reader is None:
        _reader = OCRReader(languages or ['en'])
    return _reader


def read_text(image_path: str, languages: List[str] = None) -> str:
    """Read text from an image."""
    reader = get_reader(languages)
    return reader.read(image_path)


def read_text_detailed(image_path: str) -> Dict:
    """Read text with positions and confidence."""
    reader = get_reader()
    return reader.read_detailed(image_path)


def read_screen() -> str:
    """Read text from current screen."""
    from tools.video_recognition import capture_screen
    screen_path = capture_screen()
    return read_text(screen_path)


def read_price(image_path: str) -> str:
    """Extract prices from shopping app screenshot."""
    reader = get_reader()
    text = reader.read(image_path)
    
    # Look for price patterns
    import re
    patterns = [
        r'₹\s*[\d,]+\.?\d*',      # ₹123 or ₹1,234.56
        r'Rs\.?\s*[\d,]+\.?\d*',   # Rs.123 or Rs 1,234
        r'INR\s*[\d,]+\.?\d*',     # INR 123
        r'[\d,]+\.?\d*\s*/-',      # 123/-
    ]
    
    prices = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        prices.extend(matches)
    
    if prices:
        return f"Prices found: {', '.join(prices)}\n\nFull text:\n{text}"
    else:
        return f"No prices found.\n\nFull text:\n{text}"


def ocr_status() -> str:
    """Check OCR status."""
    status = """
📝 BRO OCR - TEXT READING
{'='*50}

Backends:
"""
    status += f"  • EasyOCR: {'✅ Available (recommended)' if EASYOCR_AVAILABLE else '❌ Install: pip install easyocr'}\n"
    status += f"  • Tesseract: {'✅ Available' if TESSERACT_AVAILABLE else '❌ Install: pip install pytesseract'}\n"
    status += f"  • LLaVA: ✅ Available (fallback)\n"
    status += f"  • OpenCV: {'✅ Available' if CV2_AVAILABLE else '❌ Install: pip install opencv-python'}\n"
    
    status += """
Commands:
  • read_text("image.png") - Extract text from image
  • read_text_detailed("image.png") - With positions & confidence
  • read_screen() - Read text from current screen
  • read_price("screenshot.png") - Extract prices
  • read_video_text("video.mp4") - OCR on video frames

For best results, install EasyOCR:
  pip install easyocr
"""
    return status


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO OCR")
    parser.add_argument("command", nargs="?", default="status",
                       choices=["status", "read", "screen", "price", "video"])
    parser.add_argument("path", nargs="?", default=None)
    
    args = parser.parse_args()
    
    if args.command == "status":
        print(ocr_status())
    elif args.command == "read" and args.path:
        print(read_text(args.path))
    elif args.command == "screen":
        print(read_screen())
    elif args.command == "price" and args.path:
        print(read_price(args.path))
    elif args.command == "video" and args.path:
        result = read_video_text(args.path)
        print("\n".join(result.get("all_text", [])))
    else:
        print(ocr_status())
