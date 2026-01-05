"""
Speech-to-Text Module
Hybrid STT: Uses local Whisper (fast, private) with Google cloud fallback.

Priority:
1. Faster-Whisper (local, ~0.5s latency)
2. Google Web Speech API (cloud, ~2-3s latency, requires internet)
"""

import speech_recognition as sr
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WAKE_WORD, MIC_DEVICE_INDEX

# Import local Whisper STT
try:
    from .stt_fast import get_whisper_stt, listen_whisper, whisper_status, WHISPER_AVAILABLE
except ImportError:
    WHISPER_AVAILABLE = False
    listen_whisper = None


# Configuration
USE_LOCAL_WHISPER = True  # Set to False to force Google STT


def listen_one_shot(timeout=5, phrase_time_limit=10, force_google=False) -> str:
    """
    Listens for a single command from the microphone.
    Uses local Whisper by default, falls back to Google if unavailable.
    
    Args:
        timeout: Maximum seconds to wait for speech to start
        phrase_time_limit: Maximum seconds to let the user speak
        force_google: If True, skip Whisper and use Google directly
        
    Returns:
        The recognized text, or None if failed/timed out
    """
    
    # =========================================================================
    # METHOD 1: LOCAL WHISPER (Fast, Private)
    # =========================================================================
    if USE_LOCAL_WHISPER and not force_google and WHISPER_AVAILABLE:
        try:
            stt = get_whisper_stt()
            if stt.is_available():
                result = stt.listen(
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                if result:
                    return result
                # If no result, fall through to Google
                print("    ⚠️ Whisper returned empty, trying Google...")
        except Exception as e:
            print(f"    ⚠️ Whisper failed: {e}, trying Google...")
    
    # =========================================================================
    # METHOD 2: GOOGLE CLOUD STT (Fallback)
    # =========================================================================
    return _listen_google(timeout, phrase_time_limit)


def _listen_google(timeout=5, phrase_time_limit=10) -> str:
    """
    Listen using Google's Web Speech API (cloud-based).
    
    Note: Sends audio to Google servers. Requires internet.
    
    Args:
        timeout: Maximum seconds to wait for speech to start
        phrase_time_limit: Maximum seconds to let the user speak
        
    Returns:
        The recognized text, or None if failed/timed out
    """
    recognizer = sr.Recognizer()
    
    # Adjust energy threshold for better pause detection
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300  # Default starting value
    
    try:
        # Use configured device index or default
        with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
            active_mic = f"Index {MIC_DEVICE_INDEX}" if MIC_DEVICE_INDEX is not None else "Default"
            print(f"🎤 Listening on {active_mic} for {timeout}s (Google)...")
            
            # Short calibration for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                print("⏳ Processing speech (Google)...")
                
                # specific_language="en-US" can be added if needed
                text = recognizer.recognize_google(audio)
                return text
                
            except sr.WaitTimeoutError:
                print("❌ No speech detected (Timeout)")
                return None
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"❌ Could not request results; {e}")
                return None
                
    except OSError as e:
        print(f"❌ Microphone error: {e}")
        print("Tip: Check if 'pyaudio' is installed correctly.")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in STT: {e}")
        return None


def list_microphones():
    """List available microphone devices."""
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"Mic {index}: {name}")


def get_stt_status() -> dict:
    """Get STT engine status."""
    status = {
        "local_whisper_enabled": USE_LOCAL_WHISPER,
        "google_available": True,  # Always available with internet
    }
    
    if WHISPER_AVAILABLE:
        whisper_st = whisper_status()
        status.update(whisper_st)
    else:
        status["whisper_available"] = False
    
    return status
