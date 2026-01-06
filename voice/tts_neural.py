"""
Neural TTS Module (Edge TTS)
Provides high-quality neural voice synthesis using Microsoft Edge's online TTS.
"""
import asyncio
import os
import asyncio
import os
import tempfile
import threading
from config import TTS_VOICE_EDGE

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Check if edge-tts is installed
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False


class NeuralTTS:
    def __init__(self):
        self.voice = TTS_VOICE_EDGE
        self.rate = "+10%"  # Super fluent/fast
        self.volume = "+0%"
        self.pitch = "+0Hz" # Natural pitch
        
        # Initialize pygame mixer for playback
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.audio_available = True
            except Exception as e:
                print(f"⚠️ Audio output unavailable: {e}")
                self.audio_available = False
        else:
            print("⚠️ Pygame not installed. Audio output unavailable.")
            self.audio_available = False

    async def _generate_audio(self, text: str, output_file: str):
        """Generate audio file from text (Unified Voice - No Switching)."""
        
        # UNIFIED MODEL: Always use default voice (Prabhat)
        # We rely on Romanized text input for consistent persona.
        voice = self.voice
        

        
        # FINAL TUNING: "Fast & Smooth" (User Request: Increase Speed)
        # Speed: +15% (Fast) | Pitch: -1Hz (Neutral/Soft) | Volume: -10% (Gentle)
        # Contour: Gentle arc to remove sharp/crispy transients.
        ssml_text = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice}'>
            <prosody rate='+15%' pitch='-1Hz' volume='-10%' contour='(0%,+0%) (50%,+2%) (100%,-5%)'>
                {text}
            </prosody>
        </voice>
        </speak>"""

        communicate = edge_tts.Communicate(ssml_text, voice)
        await communicate.save(output_file)

    def speak(self, text: str, wait: bool = True):
        """
        Synthesize and play text.
        """
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("Edge TTS not installed")
            
        if not self.audio_available:
            raise RuntimeError("Audio output unavailable (Pygame missing)")

        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_filename = fp.name
            
            # Generate audio (synchronously run async code)
            asyncio.run(self._generate_audio(text, temp_filename))
            
            # Play audio
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
            else:
                # Non-blocking cleanup is harder with pygame in this simple setup
                # We'll just leave the temp file for os cleanup or handle later
                pass
                
        except Exception as e:
            print(f"❌ Neural TTS Error: {e}")

    def stop(self):
        if self.audio_available:
            pygame.mixer.music.stop()

# Singleton
_neural_engine = None

def speak_neural(text: str, wait: bool = True):
    global _neural_engine
    if not _neural_engine:
        _neural_engine = NeuralTTS()
    _neural_engine.speak(text, wait)
