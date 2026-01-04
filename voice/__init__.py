"""
BRO Voice Package
Contains text-to-speech, speech-to-text, and wake word detection.
"""

from .tts import speak, say, TTS_AVAILABLE
from .stt import listen_one_shot

# Enhanced TTS (NEW)
try:
    from .local_tts import TTSEngine, get_tts_engine, speak as enhanced_speak
    ENHANCED_TTS_AVAILABLE = True
except ImportError:
    ENHANCED_TTS_AVAILABLE = False

# Wake Word (NEW)
try:
    from .wake_word import WakeWordListener, create_wake_word_listener
    WAKE_WORD_AVAILABLE = True
except ImportError:
    WAKE_WORD_AVAILABLE = False

__all__ = [
    "speak",
    "say",
    "TTS_AVAILABLE",
    "listen_one_shot",
    "ENHANCED_TTS_AVAILABLE",
    "WAKE_WORD_AVAILABLE",
]

