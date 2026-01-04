"""
BRO Enhanced Local TTS
Improved text-to-speech with multiple backends and voice customization.
Priority: Piper > pyttsx3 (both work 100% offline)
"""

import os
import sys
import threading
import queue
import hashlib
import subprocess
from typing import Optional, List, Dict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TTS_RATE, TTS_VOLUME

# ============================================================================
# TTS BACKEND DETECTION
# ============================================================================

# pyttsx3 (always available if installed)
PYTTSX3_AVAILABLE = False
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    pass

# Piper TTS (high quality local TTS)
PIPER_AVAILABLE = False
try:
    import piper
    PIPER_AVAILABLE = True
except ImportError:
    pass

# Edge TTS (uses Microsoft Edge, free, no API key)
EDGE_TTS_AVAILABLE = False
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    pass


# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

CACHE_DIR = Path(__file__).parent.parent / "tts_cache"
CACHE_ENABLED = True
MAX_CACHE_SIZE_MB = 100


def _get_cache_path(text: str, voice: str) -> Path:
    """Generate cache file path for text + voice combo."""
    hash_input = f"{text}_{voice}".encode()
    hash_val = hashlib.md5(hash_input).hexdigest()[:12]
    return CACHE_DIR / f"tts_{hash_val}.wav"


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    if CACHE_ENABLED:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# PYTTSX3 BACKEND (Default - Always Works)
# ============================================================================

_pyttsx3_engine = None
_pyttsx3_lock = threading.Lock()


def _get_pyttsx3_engine():
    """Get or create pyttsx3 engine."""
    global _pyttsx3_engine
    
    if not PYTTSX3_AVAILABLE:
        return None
    
    with _pyttsx3_lock:
        if _pyttsx3_engine is None:
            try:
                _pyttsx3_engine = pyttsx3.init()
                _pyttsx3_engine.setProperty('rate', TTS_RATE)
                _pyttsx3_engine.setProperty('volume', TTS_VOLUME)
            except Exception as e:
                print(f"❌ pyttsx3 init error: {e}")
                return None
    
    return _pyttsx3_engine


def pyttsx3_speak(text: str, voice_name: str = None, rate: int = None) -> bool:
    """
    Speak using pyttsx3.
    
    Args:
        text: Text to speak
        voice_name: Optional voice name (e.g., 'david', 'zira')
        rate: Words per minute
        
    Returns:
        True if successful
    """
    engine = _get_pyttsx3_engine()
    if not engine:
        return False
    
    try:
        with _pyttsx3_lock:
            # Set voice if specified
            if voice_name:
                voices = engine.getProperty('voices')
                for voice in voices:
                    if voice_name.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            
            # Set rate if specified
            if rate:
                engine.setProperty('rate', rate)
            
            engine.say(text)
            engine.runAndWait()
        
        return True
    
    except Exception as e:
        print(f"❌ pyttsx3 speak error: {e}")
        return False


def pyttsx3_list_voices() -> List[Dict[str, str]]:
    """List available pyttsx3 voices."""
    engine = _get_pyttsx3_engine()
    if not engine:
        return []
    
    voices = []
    for voice in engine.getProperty('voices'):
        voices.append({
            'id': voice.id,
            'name': voice.name,
            'languages': getattr(voice, 'languages', []),
        })
    return voices


# ============================================================================
# EDGE TTS BACKEND (High Quality, Uses Microsoft Edge - Free)
# ============================================================================

def edge_tts_speak(text: str, voice: str = "en-US-GuyNeural") -> bool:
    """
    Speak using Edge TTS (requires internet on first use, then cached).
    
    Args:
        text: Text to speak
        voice: Voice name (e.g., 'en-US-GuyNeural', 'en-GB-RyanNeural')
        
    Returns:
        True if successful
    """
    if not EDGE_TTS_AVAILABLE:
        return False
    
    import asyncio
    
    async def _speak():
        try:
            _ensure_cache_dir()
            cache_path = _get_cache_path(text, voice)
            
            # Check cache
            if CACHE_ENABLED and cache_path.exists():
                _play_audio(str(cache_path))
                return True
            
            # Generate audio
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(cache_path))
            
            # Play
            _play_audio(str(cache_path))
            return True
        
        except Exception as e:
            print(f"❌ Edge TTS error: {e}")
            return False
    
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_speak())
        loop.close()
        return result
    except:
        return False


def edge_tts_list_voices() -> List[str]:
    """List available Edge TTS voices."""
    # Common high-quality voices
    return [
        "en-US-GuyNeural",      # Male, American
        "en-US-JennyNeural",    # Female, American  
        "en-GB-RyanNeural",     # Male, British (BRO-like!)
        "en-GB-SoniaNeural",    # Female, British
        "en-AU-WilliamNeural",  # Male, Australian
        "en-IN-PrabhatNeural",  # Male, Indian
    ]


# ============================================================================
# PIPER TTS BACKEND (Fully Offline, High Quality)
# ============================================================================

_piper_voice = None


def piper_speak(text: str, model_path: str = None) -> bool:
    """
    Speak using Piper TTS (fully offline, high quality).
    
    Args:
        text: Text to speak
        model_path: Path to Piper voice model
        
    Returns:
        True if successful
    """
    if not PIPER_AVAILABLE:
        return False
    
    try:
        if model_path and os.path.exists(model_path):
            voice = piper.PiperVoice.load(model_path)
        else:
            # Try to use default model
            global _piper_voice
            if _piper_voice is None:
                # Look for models in common locations
                model_dirs = [
                    Path(__file__).parent.parent / "models" / "piper",
                    Path.home() / ".piper" / "voices",
                ]
                
                for model_dir in model_dirs:
                    if model_dir.exists():
                        models = list(model_dir.glob("*.onnx"))
                        if models:
                            _piper_voice = piper.PiperVoice.load(str(models[0]))
                            break
                
                if _piper_voice is None:
                    print("⚠️ No Piper voice model found. Download from: https://github.com/rhasspy/piper")
                    return False
            
            voice = _piper_voice
        
        _ensure_cache_dir()
        cache_path = _get_cache_path(text, "piper")
        
        # Generate audio
        with open(cache_path, 'wb') as f:
            for audio_bytes in voice.synthesize_stream_raw(text):
                f.write(audio_bytes)
        
        _play_audio(str(cache_path))
        return True
    
    except Exception as e:
        print(f"❌ Piper TTS error: {e}")
        return False


# ============================================================================
# AUDIO PLAYBACK
# ============================================================================

def _play_audio(file_path: str) -> bool:
    """Play an audio file using best available method."""
    try:
        if sys.platform == 'win32':
            # Windows: use built-in player
            import winsound
            winsound.PlaySound(file_path, winsound.SND_FILENAME)
            return True
        else:
            # Linux/Mac: try aplay or afplay
            if sys.platform == 'darwin':
                subprocess.run(['afplay', file_path], check=True)
            else:
                subprocess.run(['aplay', file_path], check=True)
            return True
    
    except Exception as e:
        # Fallback: try pygame or playsound
        try:
            from playsound import playsound
            playsound(file_path)
            return True
        except:
            pass
        
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            return True
        except:
            pass
    
    return False


# ============================================================================
# UNIFIED SPEAK FUNCTION
# ============================================================================

class TTSEngine:
    """Unified TTS engine with automatic backend selection."""
    
    def __init__(self, preferred_backend: str = "auto"):
        """
        Initialize TTS engine.
        
        Args:
            preferred_backend: 'auto', 'pyttsx3', 'edge', or 'piper'
        """
        self.preferred_backend = preferred_backend
        self.current_backend = None
        self.voice = None
        self.rate = TTS_RATE
        self.volume = TTS_VOLUME
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Speak text using best available backend.
        
        Args:
            text: Text to speak
            wait: Wait for speech to complete (always True currently)
            
        Returns:
            True if successful
        """
        # Print what's being said
        print(f"🤖 BRO: {text}")
        
        backend = self.preferred_backend
        
        if backend == "auto":
            # Priority: Edge (best quality) > Piper > pyttsx3 (most compatible)
            if EDGE_TTS_AVAILABLE:
                backend = "edge"
            elif PIPER_AVAILABLE:
                backend = "piper"
            elif PYTTSX3_AVAILABLE:
                backend = "pyttsx3"
            else:
                print(f"🔊 [No TTS] {text}")
                return False
        
        self.current_backend = backend
        
        if backend == "edge":
            voice = self.voice or "en-GB-RyanNeural"  # British male - BRO-like!
            return edge_tts_speak(text, voice)
        
        elif backend == "piper":
            return piper_speak(text)
        
        elif backend == "pyttsx3":
            return pyttsx3_speak(text, self.voice, self.rate)
        
        return False
    
    def set_voice(self, voice: str):
        """Set the voice to use."""
        self.voice = voice
    
    def set_rate(self, rate: int):
        """Set speech rate (words per minute)."""
        self.rate = rate
        if PYTTSX3_AVAILABLE:
            engine = _get_pyttsx3_engine()
            if engine:
                engine.setProperty('rate', rate)
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if PYTTSX3_AVAILABLE:
            engine = _get_pyttsx3_engine()
            if engine:
                engine.setProperty('volume', self.volume)
    
    def list_voices(self) -> Dict[str, List]:
        """List available voices for all backends."""
        voices = {}
        
        if PYTTSX3_AVAILABLE:
            voices['pyttsx3'] = pyttsx3_list_voices()
        
        if EDGE_TTS_AVAILABLE:
            voices['edge'] = edge_tts_list_voices()
        
        if PIPER_AVAILABLE:
            voices['piper'] = ["Install models from https://github.com/rhasspy/piper"]
        
        return voices
    
    def get_status(self) -> Dict:
        """Get TTS system status."""
        return {
            "pyttsx3": PYTTSX3_AVAILABLE,
            "edge_tts": EDGE_TTS_AVAILABLE,
            "piper": PIPER_AVAILABLE,
            "current_backend": self.current_backend,
            "preferred_backend": self.preferred_backend,
            "cache_enabled": CACHE_ENABLED,
        }


# ============================================================================
# GLOBAL TTS INSTANCE
# ============================================================================

_tts_engine: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    """Get the global TTS engine instance."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine


def speak(text: str, wait: bool = True) -> bool:
    """
    Global speak function - uses best available TTS.
    
    Args:
        text: Text to speak
        wait: Wait for completion
        
    Returns:
        True if successful
    """
    return get_tts_engine().speak(text, wait)


def say(text: str) -> bool:
    """Alias for speak() - for backward compatibility."""
    return speak(text, wait=True)


# ============================================================================
# CLI TEST
# ============================================================================

if __name__ == "__main__":
    print("BRO Enhanced TTS Test")
    print("=" * 40)
    
    engine = get_tts_engine()
    status = engine.get_status()
    
    print(f"Available backends:")
    print(f"  - pyttsx3: {'✓' if status['pyttsx3'] else '✗'}")
    print(f"  - edge_tts: {'✓' if status['edge_tts'] else '✗'}")
    print(f"  - piper: {'✓' if status['piper'] else '✗'}")
    print()
    
    test_message = "Hello, I am BRO, your personal AI assistant. How may I help you today?"
    print(f"Testing with: \"{test_message}\"")
    print()
    
    result = speak(test_message)
    print(f"\nResult: {'Success' if result else 'Failed'}")
