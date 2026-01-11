"""
Text-to-Speech Module (Edge TTS / "Bhai" Personality)
Handles voice output using Microsoft Edge's Neural TTS (Prabhat/Madhur).
"""
import asyncio
import os
import tempfile
import threading
import queue
import time
from typing import Optional

# Config imports
try:
    from jarvis.config import TTS_VOICE_EDGE, TTS_RATE, TTS_VOLUME
except ImportError:
    TTS_VOICE_EDGE = "en-IN-PrabhatNeural"
    TTS_RATE = 200
    TTS_VOLUME = 1.0

# 3rd Party Libs
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("⚠️ edge-tts not installed. Voice will be silent.")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame not installed. Cannot play audio.")

# Global Lock for Audio
_audio_lock = threading.Lock()

class EdgeTTS:
    def __init__(self):
        self.voice = TTS_VOICE_EDGE
        self.rate = "+15%"  # Default to Fast & Fluid
        self.volume = "-0%"
        self.pitch = "-2Hz" # Slightly deeper, more authoritative
        
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"❌ Pygame init failed: {e}")

    async def _generate_audio(self, text: str, output_file: str):
        """Generate audio with SSML for "Bhai" Prosody."""
        
        # SSML Tuning for "The Cool Genius"
        # - Rate: Fast (+15%)
        # - Pitch: Slightly Low (-2Hz)
        # - Contour: Smooth arcs (removes robotic transients)
        ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{self.voice}'>
            <prosody rate='{self.rate}' pitch='{self.pitch}' volume='{self.volume}'>
                {text}
            </prosody>
        </voice>
        </speak>"""

        communicate = edge_tts.Communicate(ssml, self.voice)
        await communicate.save(output_file)

    def speak(self, text: str, wait: bool = True):
        """Synthesize and play text."""
        if not EDGE_TTS_AVAILABLE or not PYGAME_AVAILABLE:
            # Silent fallback
            print(f"🔇 [Silent] {text}")
            return

        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_filename = fp.name
            
            # Generate (run async in sync context)
            asyncio.run(self._generate_audio(text, temp_filename))
            
            # Play
            with _audio_lock:
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                
                if wait:
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    
                    # Cleanup
                    pygame.mixer.music.unload()
                    try:
                        os.remove(temp_filename)
                    except:
                        pass
        except Exception as e:
            print(f"❌ Voice Error: {e}")

    def stop(self):
        if PYGAME_AVAILABLE:
            pygame.mixer.music.stop()

# Helper Functions (API)

_engine = None

def _get_engine():
    global _engine
    if not _engine:
        _engine = EdgeTTS()
    return _engine

def speak(text: str, wait: bool = True) -> bool:
    """Public API: Speak text."""
    try:
        engine = _get_engine()
        engine.speak(text, wait)
        return True
    except Exception as e:
        print(f"Speak failed: {e}")
        return False

def say(text: str) -> bool:
    """Convenience API: Print and Speak."""
    print(f"🤖 BRO: {text}")
    return speak(text, wait=True)

def stop_speaking():
    """Stop current audio."""
    ensure_stop = _get_engine()
    if ensure_stop:
        ensure_stop.stop()

# Legacy/Dummy functions to maintain API compatibility
def list_available_voices():
    return ["Edge Neural (Prabhat)"]
    
def set_voice_rate(rate): pass
def set_voice_volume(vol): pass

# Export availability flag
TTS_AVAILABLE = True
