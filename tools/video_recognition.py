"""
BRO Video Recognition
Analyze videos and live feeds using AI vision (LLaVA).
"""

import os
import sys
import json
import base64
import urllib.request
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import CV2
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Try to import PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

VISION_MODEL = "llava:7b"
OLLAMA_URL = "http://localhost:11434/api/chat"
FRAME_INTERVAL = 30  # Analyze every 30 frames (about 1 per second at 30fps)


# =============================================================================
# VIDEO FRAME EXTRACTION
# =============================================================================

def extract_frames(video_path: str, interval: int = FRAME_INTERVAL, max_frames: int = 10) -> List[str]:
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to video file
        interval: Extract every N frames
        max_frames: Maximum number of frames to extract
    
    Returns:
        List of paths to extracted frame images
    """
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV required. Run: pip install opencv-python")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    frames = []
    frame_count = 0
    extracted = 0
    
    temp_dir = tempfile.mkdtemp(prefix="bro_video_")
    
    while extracted < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % interval == 0:
            frame_path = os.path.join(temp_dir, f"frame_{extracted:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            frames.append(frame_path)
            extracted += 1
        
        frame_count += 1
    
    cap.release()
    return frames


def capture_screen() -> str:
    """Capture current screen."""
    if not CV2_AVAILABLE:
        # Use Windows screenshot
        import subprocess
        temp_path = os.path.join(tempfile.gettempdir(), "bro_screen.png")
        subprocess.run([
            "powershell", "-Command",
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"[System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {{ "
            f"$bitmap = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height); "
            f"$graphics = [System.Drawing.Graphics]::FromImage($bitmap); "
            f"$graphics.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size); "
            f"$bitmap.Save('{temp_path}'); }}"
        ], capture_output=True)
        return temp_path
    else:
        import numpy as np
        from PIL import ImageGrab
        
        screen = ImageGrab.grab()
        temp_path = os.path.join(tempfile.gettempdir(), "bro_screen.png")
        screen.save(temp_path)
        return temp_path


def capture_webcam() -> str:
    """Capture frame from webcam."""
    if not CV2_AVAILABLE:
        raise ImportError("OpenCV required for webcam. Run: pip install opencv-python")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise ValueError("Cannot open webcam")
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError("Failed to capture from webcam")
    
    temp_path = os.path.join(tempfile.gettempdir(), "bro_webcam.jpg")
    cv2.imwrite(temp_path, frame)
    return temp_path


# =============================================================================
# AI VISION ANALYSIS
# =============================================================================

def analyze_image(image_path: str, prompt: str = "Describe what you see in this image.") -> str:
    """Analyze a single image using LLaVA."""
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        
        payload = json.dumps({
            "model": VISION_MODEL,
            "messages": [{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }],
            "stream": False,
            "options": {"temperature": 0.3}
        }).encode()
        
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            return result["message"]["content"]
    
    except Exception as e:
        return f"Error: {e}"


def analyze_video(video_path: str, prompt: str = None, max_frames: int = 5) -> str:
    """
    Analyze a video by extracting key frames and describing each.
    
    Args:
        video_path: Path to video file
        prompt: Custom prompt for analysis
        max_frames: Number of frames to analyze
    """
    if prompt is None:
        prompt = "Describe what's happening in this video frame. Be specific about actions, people, and objects."
    
    print(f"🎬 Analyzing video: {video_path}")
    print(f"   Extracting {max_frames} frames...")
    
    frames = extract_frames(video_path, max_frames=max_frames)
    
    if not frames:
        return "❌ Could not extract frames from video"
    
    print(f"   Analyzing {len(frames)} frames with AI vision...")
    
    output = f"""
🎬 VIDEO ANALYSIS
{'='*50}
File: {os.path.basename(video_path)}
Frames analyzed: {len(frames)}
{'='*50}
"""
    
    for i, frame_path in enumerate(frames):
        print(f"   Processing frame {i+1}/{len(frames)}...")
        description = analyze_image(frame_path, prompt)
        output += f"\n📷 Frame {i+1}:\n{description}\n"
        
        # Clean up frame
        try:
            os.remove(frame_path)
        except:
            pass
    
    # Generate summary
    summary_prompt = f"""Based on these frame descriptions, provide a brief summary of what happens in this video:

{output}

Summarize in 2-3 sentences."""
    
    # Use text model for summary
    try:
        payload = json.dumps({
            "model": "gemma3",
            "messages": [{"role": "user", "content": summary_prompt}],
            "stream": False
        }).encode()
        
        req = urllib.request.Request(
            OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            summary = result["message"]["content"]
            output += f"\n{'='*50}\n📝 SUMMARY:\n{summary}\n"
    except:
        pass
    
    return output


# =============================================================================
# REAL-TIME ANALYSIS
# =============================================================================

def watch_screen(interval: int = 5, duration: int = 30, 
                 prompt: str = "What's happening on screen?",
                 callback: Callable[[str], None] = None) -> List[Dict]:
    """
    Watch screen and analyze periodically.
    
    Args:
        interval: Seconds between captures
        duration: Total seconds to watch
        prompt: Question to ask about each frame
        callback: Optional callback for each analysis
    """
    results = []
    start = time.time()
    
    print(f"👁️ Watching screen for {duration}s (every {interval}s)...")
    
    while time.time() - start < duration:
        try:
            screen_path = capture_screen()
            analysis = analyze_image(screen_path, prompt)
            
            result = {
                "timestamp": time.time() - start,
                "analysis": analysis
            }
            results.append(result)
            
            print(f"\n⏱️ {result['timestamp']:.1f}s: {analysis[:100]}...")
            
            if callback:
                callback(analysis)
            
            time.sleep(interval)
        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(interval)
    
    return results


def watch_webcam(interval: int = 3, duration: int = 30,
                 prompt: str = "What do you see?") -> List[Dict]:
    """
    Watch webcam and analyze periodically.
    """
    if not CV2_AVAILABLE:
        return [{"error": "OpenCV required for webcam"}]
    
    results = []
    start = time.time()
    
    print(f"📹 Watching webcam for {duration}s...")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return [{"error": "Cannot open webcam"}]
    
    try:
        while time.time() - start < duration:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Save frame
            temp_path = os.path.join(tempfile.gettempdir(), "bro_webcam_temp.jpg")
            cv2.imwrite(temp_path, frame)
            
            # Analyze
            analysis = analyze_image(temp_path, prompt)
            
            result = {
                "timestamp": time.time() - start,
                "analysis": analysis
            }
            results.append(result)
            
            print(f"\n📹 {result['timestamp']:.1f}s: {analysis[:100]}...")
            
            time.sleep(interval)
    finally:
        cap.release()
    
    return results


# =============================================================================
# SPECIALIZED ANALYSIS
# =============================================================================

def detect_objects(image_or_video: str) -> str:
    """Detect and list objects in image or video."""
    prompt = """List ALL objects you can see in this image.
Format as a bullet list with confidence level (high/medium/low):
• [object] - [confidence]

Be thorough and specific."""
    
    if image_or_video.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        frames = extract_frames(image_or_video, max_frames=3)
        if frames:
            return analyze_image(frames[0], prompt)
    
    return analyze_image(image_or_video, prompt)


def read_text(image_path: str) -> str:
    """Extract text from image (OCR-like)."""
    prompt = """Read and transcribe ALL text visible in this image.
Include signs, labels, screens, documents, etc.
Format the text exactly as it appears."""
    
    return analyze_image(image_path, prompt)


def describe_person(image_path: str) -> str:
    """Describe people in image."""
    prompt = """Describe the people visible in this image:
- How many people
- What they're wearing
- What they're doing
- Estimated age range
- Any notable features

Be respectful and objective."""
    
    return analyze_image(image_path, prompt)


def analyze_activity(video_path: str) -> str:
    """Analyze activity/actions in a video."""
    prompt = "Describe the main activity or action happening in this frame. What are people doing?"
    return analyze_video(video_path, prompt, max_frames=5)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def see(source: str = "screen", prompt: str = None) -> str:
    """
    Quick vision command.
    
    Args:
        source: "screen", "webcam", or path to image/video
        prompt: What to ask about the image
    """
    if source == "screen":
        screen_path = capture_screen()
        prompt = prompt or "What's on my screen? Be brief."
        result = analyze_image(screen_path, prompt)
        return f"👁️ Screen: {result}"
    
    elif source == "webcam":
        webcam_path = capture_webcam()
        prompt = prompt or "What do you see? Be brief."
        result = analyze_image(webcam_path, prompt)
        return f"📹 Webcam: {result}"
    
    elif os.path.isfile(source):
        if source.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            return analyze_video(source, prompt or None)
        else:
            return analyze_image(source, prompt or "Describe this image.")
    
    else:
        return f"❌ Unknown source: {source}"


def what_is_this(image_path: str) -> str:
    """Identify the main subject of an image."""
    prompt = "What is the main subject of this image? Identify it in one sentence."
    return analyze_image(image_path, prompt)


# =============================================================================
# STATUS
# =============================================================================

def video_status() -> str:
    """Check video recognition status."""
    return f"""
🎬 BRO VIDEO RECOGNITION
{'='*50}

Dependencies:
  • OpenCV: {'✅ Available' if CV2_AVAILABLE else '❌ Install: pip install opencv-python'}
  • PIL: {'✅ Available' if PIL_AVAILABLE else '❌ Install: pip install Pillow'}
  • Vision Model: {VISION_MODEL}

Commands:
  • see("screen") - Analyze current screen
  • see("webcam") - Analyze webcam
  • see("path/to/video.mp4") - Analyze video
  • see("path/to/image.jpg") - Analyze image
  
  • analyze_video(path) - Detailed video analysis
  • detect_objects(path) - List objects
  • read_text(path) - OCR/text extraction
  • describe_person(path) - Describe people
  
  • watch_screen(interval=5, duration=30) - Monitor screen
  • watch_webcam(interval=3, duration=30) - Monitor webcam
"""


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Video Recognition")
    parser.add_argument("command", nargs="?", default="status",
                       choices=["status", "screen", "webcam", "analyze", "objects", "text"])
    parser.add_argument("path", nargs="?", default=None)
    parser.add_argument("--prompt", "-p", default=None)
    
    args = parser.parse_args()
    
    if args.command == "status":
        print(video_status())
    elif args.command == "screen":
        print(see("screen", args.prompt))
    elif args.command == "webcam":
        print(see("webcam", args.prompt))
    elif args.command == "analyze" and args.path:
        print(see(args.path, args.prompt))
    elif args.command == "objects" and args.path:
        print(detect_objects(args.path))
    elif args.command == "text" and args.path:
        print(read_text(args.path))
    else:
        print(video_status())
