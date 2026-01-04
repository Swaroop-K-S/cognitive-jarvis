"""
Speech-to-Text Module
Handles microphone input and converts speech to text using Google's Web Speech API (default)
or other offline engines if configured.
"""

import speech_recognition as sr
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import WAKE_WORD, MIC_DEVICE_INDEX

def listen_one_shot(timeout=5, phrase_time_limit=10) -> str:
    """
    Listens for a single command from the microphone.
    
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
            print(f"🎤 Listening on {active_mic} for {timeout}s...")
            
            # Short calibration for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                print("⏳ Processing speech...")
                
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
