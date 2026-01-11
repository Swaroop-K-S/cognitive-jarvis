"""
BRO Voice Input Module
Handles real microphone recording and speech-to-text using SpeechRecognition.
"""

import speech_recognition as sr
import os

def listen_and_transcribe():
    """
    Listen to the microphone and transcribe speech to text.
    Returns: (text, error_message)
    """
    recognizer = sr.Recognizer()
    
    # Adjust for ambient noise
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    
    # Use default microphone
    try:
        with sr.Microphone() as source:
            print("🎤 Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            print("🎤 Listening...")
            # Listen indefinitely until silence is detected (or max 5 seconds phrase)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🎤 Recognizing (Offline Mode)...")
            
            try:
                # 1. Try Whisper (Best Offline)
                # Requires: pip install openai-whisper
                text = recognizer.recognize_whisper(audio, language="english")
                print(f"✅ Whisper: {text}")
                return text, None
            except AttributeError:
                # Fallback if whisper not in this version of SR
                pass
            except Exception as e:
                print(f"⚠️ Whisper failed: {e}")

            try:
                # 2. Try Vosk (Fast Offline)
                # Requires: pip install vosk
                text = recognizer.recognize_vosk(audio)
                import json
                text = json.loads(text)["text"]
                print(f"✅ Vosk: {text}")
                return text, None
            except AttributeError:
                pass
            except Exception as e:
                 print(f"⚠️ Vosk failed: {e}")

            # 3. Fallback to Google (Online) with warning
            print("⚠️ Offline engines failed. Falling back to Google (Online).")
            text = recognizer.recognize_google(audio)
            print(f"✅ Google: {text}")
            return text, None
            
    except sr.WaitTimeoutError:
        return None, "No speech detected (timeout)"
    except sr.UnknownValueError:
        return None, "Could not understand audio"
    except sr.RequestError as e:
        return None, f"Network error: {e}"
    except Exception as e:
        return None, f"Error: {e}"

if __name__ == "__main__":
    text, err = listen_and_transcribe()
    if text:
        print(f"TRANSCRIPTION: {text}")
    else:
        print(f"ERROR: {err}")
