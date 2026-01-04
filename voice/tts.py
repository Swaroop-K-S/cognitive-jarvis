"""
Text-to-Speech Module
Handles voice output using pyttsx3 for offline synthesis.
"""

import sys
import os
import threading
import queue

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    pyttsx3 = None

from config import TTS_RATE, TTS_VOLUME


# Global TTS engine (singleton pattern for thread safety)
_tts_engine = None
_tts_lock = threading.Lock()
_speech_queue = queue.Queue()


def _get_engine():
    """Get or create the TTS engine."""
    global _tts_engine
    
    if not TTS_AVAILABLE:
        return None
    
    with _tts_lock:
        if _tts_engine is None:
            try:
                _tts_engine = pyttsx3.init()
                _tts_engine.setProperty('rate', TTS_RATE)
                _tts_engine.setProperty('volume', TTS_VOLUME)
                
                # Try to set a nice voice if available
                voices = _tts_engine.getProperty('voices')
                for voice in voices:
                    # Prefer a British or neutral English voice
                    if 'english' in voice.name.lower() or 'david' in voice.name.lower():
                        _tts_engine.setProperty('voice', voice.id)
                        break
            except Exception as e:
                print(f"❌ TTS initialization error: {e}")
                return None
    
    return _tts_engine


def speak(text: str, wait: bool = True) -> bool:
    """
    Speak the given text.
    
    Args:
        text: The text to speak
        wait: If True, wait for speech to complete before returning
        
    Returns:
        True if successful, False otherwise
    """
    if not TTS_AVAILABLE:
        print(f"🔊 [TTS Unavailable] {text}")
        return False
    
    engine = _get_engine()
    if engine is None:
        print(f"🔊 [TTS Error] {text}")
        return False
    
    try:
        with _tts_lock:
            engine.say(text)
            if wait:
                engine.runAndWait()
            else:
                # Non-blocking speech using a thread
                threading.Thread(target=engine.runAndWait, daemon=True).start()
        return True
    except Exception as e:
        print(f"❌ Speech error: {e}")
        print(f"🔊 [Fallback] {text}")
        return False


def say(text: str) -> bool:
    """
    Convenience function to speak text (non-blocking).
    Also prints the text to console.
    
    Args:
        text: The text to speak
        
    Returns:
        True if successful
    """
    print(f"🤖 BRO: {text}")
    return speak(text, wait=True)


def set_voice_rate(rate: int):
    """Set the speech rate (words per minute)."""
    engine = _get_engine()
    if engine:
        with _tts_lock:
            engine.setProperty('rate', rate)


def set_voice_volume(volume: float):
    """Set the speech volume (0.0 to 1.0)."""
    engine = _get_engine()
    if engine:
        with _tts_lock:
            engine.setProperty('volume', max(0.0, min(1.0, volume)))


def list_available_voices():
    """List all available TTS voices."""
    engine = _get_engine()
    if engine:
        voices = engine.getProperty('voices')
        print("Available voices:")
        for i, voice in enumerate(voices):
            print(f"  {i}: {voice.name} ({voice.id})")
        return voices
    return []


def stop_speaking():
    """Stop any current speech."""
    engine = _get_engine()
    if engine:
        with _tts_lock:
            engine.stop()
