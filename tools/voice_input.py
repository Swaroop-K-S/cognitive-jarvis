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
    
    # Device ID 2 found to be working
    try:
        with sr.Microphone(device_index=2) as source:
            print("🎤 Adjusting for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            print("🎤 Listening...")
            # Listen indefinitely until silence is detected (or max 5 seconds phrase)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🎤 Recognizing...")
            # Use Google Speech Recognition (free, high quality, requires internet)
            text = recognizer.recognize_google(audio)
            print(f"✅ You said: {text}")
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
