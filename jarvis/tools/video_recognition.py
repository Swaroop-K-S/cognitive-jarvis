"""
Video Recognition Module
Pipelines: Video -> Frames -> Vision AI -> Summary/Search.
Supports local files and YouTube URLs.
"""
import cv2
import os
import time
import base64
from typing import List, Dict, Optional
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OLLAMA_HOST

# Try to import ollama client
OLLAMA_CLIENT_AVAILABLE = False
try:
    import ollama
    OLLAMA_CLIENT_AVAILABLE = True
except ImportError:
    ollama = None

# Try to import yt-dlp
YTDLP_AVAILABLE = False
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    yt_dlp = None


# Vision model to use for frame analysis
VISION_MODEL = "llava:7b"  # or "moondream" for lighter weight


class VideoRecognizer:
    """
    Video analysis using frame-sampling pipeline.
    Extracts keyframes and uses Vision AI to understand content.
    """
    
    def __init__(self):
        self.temp_dir = "temp_video_frames"
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def _download_youtube(self, url: str) -> Optional[str]:
        """Downloads YouTube video to a temp file (lowest quality for speed)."""
        if not YTDLP_AVAILABLE:
            print("    ❌ yt-dlp not installed. Run: pip install yt-dlp")
            return None
        
        print(f"    🎥 Downloading YouTube video...")
        ydl_opts = {
            'format': 'worst',  # We only need low-res for vision
            'outtmpl': os.path.join(self.temp_dir, 'temp_video.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"    ❌ YouTube download failed: {e}")
            return None

    def _extract_frames(self, video_path: str, interval: int = 5) -> List[str]:
        """Extracts one frame every 'interval' seconds."""
        print(f"    🎞️ Extracting frames from {os.path.basename(video_path)}...")
        vidcap = cv2.VideoCapture(video_path)
        
        if not vidcap.isOpened():
            print(f"    ❌ Could not open video: {video_path}")
            return []
        
        fps = vidcap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30  # Default fallback
        
        frame_interval = int(fps * interval)
        if frame_interval == 0:
            frame_interval = 1
        
        frames_base64 = []
        count = 0
        success = True
        
        while success:
            success, image = vidcap.read()
            if count % frame_interval == 0 and success:
                # Resize to speed up Vision AI (512px max)
                height, width = image.shape[:2]
                if width > 512:
                    scale = 512 / width
                    image = cv2.resize(image, (512, int(height * scale)))
                
                # Convert to base64
                _, buffer = cv2.imencode('.jpg', image)
                frame_str = base64.b64encode(buffer).decode('utf-8')
                frames_base64.append(frame_str)
                timestamp = count / fps
                print(f"      -> Captured frame at {timestamp:.1f}s")
            count += 1
            
        vidcap.release()
        print(f"    ✓ Extracted {len(frames_base64)} keyframes")
        return frames_base64

    def analyze_video(self, source: str, query: str = "Describe what happens in this video") -> str:
        """
        Main pipeline: Source -> Frames -> Captions -> Summary
        
        Args:
            source: Path to video file or YouTube URL
            query: Question about the video
            
        Returns:
            Summary or answer based on video content
        """
        if not OLLAMA_CLIENT_AVAILABLE:
            return "Error: ollama client not installed. Run: pip install ollama"
        
        video_path = source
        is_youtube = "youtube.com" in source or "youtu.be" in source
        
        try:
            # 1. Acquire Video
            if is_youtube:
                video_path = self._download_youtube(source)
                if not video_path:
                    return "Failed to download YouTube video."
            
            if not os.path.exists(video_path):
                return f"Video file not found: {video_path}"
            
            # 2. Extract Keyframes (1 frame every 5 seconds)
            frames = self._extract_frames(video_path, interval=5)
            if not frames:
                return "Could not extract any frames from the video."
            
            # Limit frames to avoid overwhelming the LLM
            max_frames = 20
            if len(frames) > max_frames:
                # Sample evenly across the video
                step = len(frames) // max_frames
                frames = frames[::step][:max_frames]
                print(f"    📋 Sampled down to {len(frames)} frames")
            
            # 3. Vision Loop (The "Eyes")
            print(f"    🧠 Analyzing {len(frames)} frames with {VISION_MODEL}...")
            frame_descriptions = []
            
            for i, frame in enumerate(frames):
                try:
                    # Ask Vision model to describe the frame briefly
                    res = ollama.chat(model=VISION_MODEL, messages=[{
                        'role': 'user',
                        'content': "Describe this image in one brief sentence.",
                        'images': [frame]
                    }])
                    desc = res['message']['content'].strip()
                    timestamp = i * 5
                    frame_descriptions.append(f"[{timestamp}s]: {desc}")
                    print(f"      -> Frame {i+1}/{len(frames)}: {desc[:60]}...")
                except Exception as e:
                    print(f"      ⚠️ Frame {i} failed: {e}")
                    continue
            
            if not frame_descriptions:
                return "Failed to analyze any frames. Check if vision model is available."
            
            # 4. Synthesis Loop (The "Brain")
            print(f"    🧠 Synthesizing {len(frame_descriptions)} descriptions...")
            full_context = "\n".join(frame_descriptions)
            
            summary_prompt = f"""Here is a timeline of events from a video:

{full_context}

User Question: {query}

Based on the timeline above, answer the user's question concisely."""
            
            final_res = ollama.chat(model="gemma3", messages=[{
                'role': 'user',
                'content': summary_prompt
            }])
            
            return final_res['message']['content']

        except Exception as e:
            return f"Video Error: {str(e)}"
        finally:
            # Cleanup YouTube downloads
            if is_youtube and video_path and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                except:
                    pass


# =============================================================================
# REGISTRY-COMPATIBLE WRAPPER FUNCTIONS
# =============================================================================

from .registry import tool

_recognizer = None

def _get_recognizer() -> VideoRecognizer:
    global _recognizer
    if _recognizer is None:
        _recognizer = VideoRecognizer()
    return _recognizer


@tool("summarize_video", "Summarize the main events and content of a video file or YouTube URL.")
def summarize_video(video_source: str) -> str:
    """
    Summarize a video file or YouTube URL.
    
    Args:
        video_source: Path to local video file or YouTube URL
        
    Returns:
        Summary of the video content
    """
    recognizer = _get_recognizer()
    return recognizer.analyze_video(
        video_source, 
        "Summarize the main events and content of this video."
    )


@tool("find_in_video", "Find specific events or objects in a video file or YouTube URL.")
def find_in_video(video_source: str, search_query: str) -> str:
    """
    Find specific events or objects in a video.
    
    Args:
        video_source: Path to local video file or YouTube URL
        search_query: What to search for in the video
        
    Returns:
        Timestamps and descriptions of matching content
    """
    recognizer = _get_recognizer()
    return recognizer.analyze_video(
        video_source, 
        f"Find where this happens in the video: {search_query}. "
        f"Return the approximate timestamp(s) and describe what you see."
    )


def video_status() -> dict:
    """Get video recognition capabilities status."""
    return {
        "opencv_available": True,  # cv2 is always available if we got here
        "ytdlp_available": YTDLP_AVAILABLE,
        "ollama_client_available": OLLAMA_CLIENT_AVAILABLE,
        "vision_model": VISION_MODEL,
    }
