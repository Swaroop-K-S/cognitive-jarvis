"""
JARVIS Voice Package (Offline)
Contains text-to-speech using pyttsx3 (works offline).
"""

from .tts import speak, say, TTS_AVAILABLE

__all__ = [
    "speak",
    "say",
    "TTS_AVAILABLE",
]
