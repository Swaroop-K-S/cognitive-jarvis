"""
BRO Wake Word Detection
Always-on "Hey BRO" listening using Vosk (100% offline).
"""

import json
import os
import sys
import threading
import queue
import time
from typing import Callable, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Vosk for offline recognition
VOSK_AVAILABLE = False
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)  # Suppress Vosk logs
    VOSK_AVAILABLE = True
except ImportError:
    pass

# Fallback to speech_recognition
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from config import WAKE_WORD, MIC_DEVICE_INDEX

# Wake word configuration
WAKE_PHRASES = ["BRO", "hey BRO", "okay BRO", "yo BRO"]
SAMPLE_RATE = 16000
CHUNK_SIZE = 4000


class WakeWordListener:
    """
    Background listener that waits for wake word then triggers callback.
    Uses Vosk for 100% offline recognition.
    """
    
    def __init__(
        self,
        on_wake: Callable[[], None],
        wake_phrases: List[str] = None,
        model_path: str = None
    ):
        """
        Initialize the wake word listener.
        
        Args:
            on_wake: Callback function when wake word detected
            wake_phrases: List of phrases to listen for (default: WAKE_PHRASES)
            model_path: Path to Vosk model (default: auto-download small model)
        """
        self.on_wake = on_wake
        self.wake_phrases = [p.lower() for p in (wake_phrases or WAKE_PHRASES)]
        self.model_path = model_path
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._audio = None
        self._stream = None
        self._model = None
        self._recognizer = None
        
        # Status
        self.last_heard = ""
        self.is_listening = False
        self.error_message = None
    
    def _ensure_model(self) -> bool:
        """Ensure Vosk model is available."""
        if not VOSK_AVAILABLE:
            self.error_message = "Vosk not installed. Run: pip install vosk"
            return False
        
        # Default model path
        if not self.model_path:
            # Look for model in common locations
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "vosk-model"),
                os.path.join(os.path.dirname(__file__), "..", "models", "vosk"),
                os.path.expanduser("~/.vosk/vosk-model-small-en-us-0.15"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.model_path = path
                    break
        
        # Try to load model
        if self.model_path and os.path.exists(self.model_path):
            try:
                self._model = Model(self.model_path)
                return True
            except Exception as e:
                self.error_message = f"Failed to load Vosk model: {e}"
                return False
        
        # Auto-download small model
        try:
            print("📥 Downloading Vosk model (first time only, ~50MB)...")
            # Vosk will auto-download if we pass model name
            self._model = Model(model_name="vosk-model-small-en-us-0.15")
            return True
        except Exception as e:
            self.error_message = f"Failed to download Vosk model: {e}. Download manually from https://alphacephei.com/vosk/models"
            return False
    
    def _init_audio(self) -> bool:
        """Initialize audio stream."""
        if not PYAUDIO_AVAILABLE:
            self.error_message = "PyAudio not installed. Run: pip install pyaudio"
            return False
        
        try:
            self._audio = pyaudio.PyAudio()
            
            # Get device index
            device_index = MIC_DEVICE_INDEX
            if device_index is None:
                device_index = self._audio.get_default_input_device_info()['index']
            
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK_SIZE
            )
            return True
        except Exception as e:
            self.error_message = f"Microphone error: {e}"
            return False
    
    def _cleanup_audio(self):
        """Clean up audio resources."""
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None
        
        if self._audio:
            try:
                self._audio.terminate()
            except:
                pass
            self._audio = None
    
    def _listen_loop(self):
        """Main listening loop (runs in background thread)."""
        if not self._ensure_model():
            print(f"❌ Wake word error: {self.error_message}")
            return
        
        if not self._init_audio():
            print(f"❌ Wake word error: {self.error_message}")
            return
        
        self._recognizer = KaldiRecognizer(self._model, SAMPLE_RATE)
        self.is_listening = True
        print(f"🎤 Wake word listening... Say '{WAKE_PHRASES[0]}' to activate")
        
        try:
            while self._running:
                try:
                    data = self._stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    
                    if self._recognizer.AcceptWaveform(data):
                        result = json.loads(self._recognizer.Result())
                        text = result.get("text", "").lower().strip()
                        
                        if text:
                            self.last_heard = text
                            
                            # Check for wake word
                            for phrase in self.wake_phrases:
                                if phrase in text:
                                    print(f"✨ Wake word detected: '{text}'")
                                    self.is_listening = False
                                    
                                    # Call the callback
                                    if self.on_wake:
                                        self.on_wake()
                                    
                                    self.is_listening = True
                                    break
                    
                except Exception as e:
                    if self._running:
                        print(f"⚠️ Listen error: {e}")
                        time.sleep(0.1)
        
        finally:
            self.is_listening = False
            self._cleanup_audio()
    
    def start(self):
        """Start listening for wake word in background."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop listening."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
    
    def is_active(self) -> bool:
        """Check if listener is active."""
        return self._running and self.is_listening


class SimpleSpeechRecognitionWakeWord:
    """
    Fallback wake word detector using speech_recognition library.
    Uses Google API (online) but works if Vosk isn't available.
    """
    
    def __init__(self, on_wake: Callable[[], None], wake_phrases: List[str] = None):
        self.on_wake = on_wake
        self.wake_phrases = [p.lower() for p in (wake_phrases or WAKE_PHRASES)]
        self._running = False
        self._thread = None
        self.is_listening = False
    
    def _listen_loop(self):
        if not SR_AVAILABLE:
            print("❌ speech_recognition not installed")
            return
        
        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        
        try:
            with sr.Microphone(device_index=MIC_DEVICE_INDEX) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(f"🎤 Wake word listening (online mode)... Say '{WAKE_PHRASES[0]}'")
                self.is_listening = True
                
                while self._running:
                    try:
                        audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)
                        text = recognizer.recognize_google(audio).lower()
                        
                        for phrase in self.wake_phrases:
                            if phrase in text:
                                print(f"✨ Wake word detected: '{text}'")
                                if self.on_wake:
                                    self.on_wake()
                                break
                    
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        print(f"⚠️ Speech API unavailable: {e}")
                        time.sleep(1)
                    except Exception as e:
                        print(f"⚠️ Wake word error: {e}")
                        time.sleep(0.5)
        
        finally:
            self.is_listening = False
    
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
    
    def is_active(self) -> bool:
        return self._running and self.is_listening


def create_wake_word_listener(on_wake: Callable[[], None]) -> object:
    """
    Factory function to create the best available wake word listener.
    
    Args:
        on_wake: Callback when wake word is detected
        
    Returns:
        A wake word listener instance (Vosk or fallback)
    """
    if VOSK_AVAILABLE and PYAUDIO_AVAILABLE:
        return WakeWordListener(on_wake)
    elif SR_AVAILABLE:
        print("⚠️ Vosk not available, using online wake word detection")
        return SimpleSpeechRecognitionWakeWord(on_wake)
    else:
        raise RuntimeError("No speech recognition available. Install vosk or speech_recognition")


# Quick test
if __name__ == "__main__":
    def on_wake_callback():
        print("🎉 BRO activated! (This is where we'd start listening for commands)")
    
    print("Testing wake word detection...")
    print(f"Vosk available: {VOSK_AVAILABLE}")
    print(f"PyAudio available: {PYAUDIO_AVAILABLE}")
    print(f"SpeechRecognition available: {SR_AVAILABLE}")
    
    try:
        listener = create_wake_word_listener(on_wake_callback)
        listener.start()
        
        print("\nListening... Say 'Hey BRO' to test. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        listener.stop()
