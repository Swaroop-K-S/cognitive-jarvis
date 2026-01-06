"""
Speech-to-Text Module
Hybrid STT: Uses local Whisper (fast, private) with Google cloud fallback.
"""

import speech_recognition as sr
from jarvis.config import WAKE_WORD, MIC_DEVICE_INDEX

# Import local Whisper STT
WHISPER_AVAILABLE = False
try:
    from jarvis.voice.stt_fast import get_stt
    WHISPER_AVAILABLE = True
except ImportError:
    pass

# Configuration
USE_LOCAL_WHISPER = True

def listen_one_shot(timeout=5, phrase_time_limit=10, force_google=False) -> str:
    """
    Listens for a single command.
    Records using SpeechRecognition, then transcribes with Whisper (Local) or Google (Cloud).
    """
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 300
    
    try:
        with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
            print(f"🎤 Listening... ({'Whisper' if (USE_LOCAL_WHISPER and not force_google) else 'Google'})")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                # 1. Record Audio
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                # 2. Transcribe
                if USE_LOCAL_WHISPER and not force_google and WHISPER_AVAILABLE:
                    try:
                        print("    ⏳ Transcribing (Whisper)...")
                        wav_data = io.BytesIO(audio.get_wav_data())
                        stt = get_stt()
                        text = stt.transcribe(wav_data)
                        print(f"    🗣️ You said: {text}")
                        return text
                    except Exception as e:
                        print(f"    ⚠️ Whisper Error: {e}")
                        # Fallback to Google
                
                # Fallback / Default to Google
                print("    ⏳ Sending to Google...")
                text = recognizer.recognize_google(audio)
                print(f"    🗣️ Google heard: {text}")
                return text

            except sr.WaitTimeoutError:
                print("❌ Timeout - No speech")
                return None
            except sr.UnknownValueError:
                print("❌ Unintelligible")
                return None
                
    except Exception as e:
        print(f"❌ Microphone Error: {e}")
        return None
