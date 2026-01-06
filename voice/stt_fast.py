"""
Fast Local Speech-to-Text using Faster-Whisper
Provides ~5x speed improvement over cloud-based Google STT.

Features:
- 100% Local (no cloud, no privacy concerns)
- Uses faster-whisper with CTranslate2 for optimized inference
- Voice Activity Detection (VAD) for instant end-of-speech detection
- Configurable model sizes (tiny, base, small, medium)
"""

import sys
import os
import time
import numpy as np
from typing import Optional, Tuple
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MIC_DEVICE_INDEX

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================

WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    pass

PYAUDIO_AVAILABLE = False
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    pass

# Silero VAD for voice activity detection
VAD_AVAILABLE = False
try:
    import torch
    VAD_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# CONFIGURATION
# =============================================================================

# Whisper model options (smaller = faster, larger = more accurate)
# "tiny.en" - 39M params, ~10x realtime on CPU
# "base.en" - 74M params, ~5x realtime on CPU  
# "small.en" - 244M params, ~2x realtime on CPU
DEFAULT_MODEL = "small"  # Multilingual model (supports Hindi/Kannada)
DEFAULT_DEVICE = "cpu"  # or "cuda" for GPU
DEFAULT_COMPUTE_TYPE = "int8"  # int8 for CPU, float16 for GPU

# Audio settings
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
CHANNELS = 1


# =============================================================================
# WHISPER STT CLASS
# =============================================================================

class WhisperSTT:
    """
    Fast local speech-to-text using Faster-Whisper.
    """
    
    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        device: str = DEFAULT_DEVICE,
        compute_type: str = DEFAULT_COMPUTE_TYPE
    ):
        """
        Initialize the Whisper STT engine.
        
        Args:
            model_size: Whisper model size (tiny.en, base.en, small.en)
            device: "cpu" or "cuda"
            compute_type: "int8" for CPU, "float16" for GPU
        """
        self.model = None
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.vad_model = None
        self._audio = None
        
        if WHISPER_AVAILABLE:
            self._load_model()
        
        if VAD_AVAILABLE:
            self._load_vad()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            print(f"    🎤 Loading Whisper model ({self.model_size})...")
            start = time.time()
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            print(f"    ✓ Whisper loaded in {time.time() - start:.1f}s")
        except Exception as e:
            print(f"    ⚠️ Failed to load Whisper: {e}")
            self.model = None
    
    def _load_vad(self):
        """Load Silero VAD for voice activity detection."""
        try:
            # Silero VAD is lightweight and fast
            self.vad_model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=True
            )
            self.get_speech_timestamps = utils[0]
            print("    ✓ VAD loaded")
        except Exception as e:
            print(f"    ⚠️ VAD not available: {e}")
            self.vad_model = None
    
    def _get_audio_stream(self):
        """Get or create PyAudio instance."""
        if not PYAUDIO_AVAILABLE:
            return None
        
        if self._audio is None:
            self._audio = pyaudio.PyAudio()
        return self._audio
    
    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: NumPy array of audio samples (float32, 16kHz)
            
        Returns:
            Transcribed text
        """
        if not self.model:
            return ""
        
        try:
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize to [-1, 1]
            if audio_data.max() > 1.0:
                audio_data = audio_data / 32768.0
            
            # Transcribe with fast settings
            segments, info = self.model.transcribe(
                audio_data,
                beam_size=1,  # Faster decoding
                language=None, # Auto-detect language (supports Hindi, Kannada, etc.)
                vad_filter=True,  # Built-in VAD
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200
                )
            )
            
            # Collect text from segments
            text = " ".join([segment.text for segment in segments]).strip()
            return text
            
        except Exception as e:
            print(f"    ⚠️ Transcription error: {e}")
            return ""
    
    def listen(
        self,
        timeout: float = 5.0,
        phrase_time_limit: float = 10.0,
        silence_threshold: float = 0.01,
        silence_duration: float = 1.0
    ) -> Optional[str]:
        """
        Listen for speech and transcribe.
        
        Args:
            timeout: Max seconds to wait for speech to start
            phrase_time_limit: Max seconds of speech to capture
            silence_threshold: Audio level below which is considered silence
            silence_duration: Seconds of silence to mark end of speech
            
        Returns:
            Transcribed text or None if timeout/error
        """
        if not self.model or not PYAUDIO_AVAILABLE:
            return None
        
        audio = self._get_audio_stream()
        if not audio:
            return None
        
        try:
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=MIC_DEVICE_INDEX,
                frames_per_buffer=CHUNK_SIZE
            )
            
            print(f"🎤 Listening (local Whisper)...")
            
            # Dynamic silence threshold: sample ambient noise for 0.5s
            calibration_samples = []
            calibration_start = time.time()
            while time.time() - calibration_start < 0.3:
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    calibration_samples.append(np.abs(chunk).mean())
                except:
                    pass
            
            if calibration_samples:
                # Set threshold at 2x the ambient noise level
                ambient_level = np.mean(calibration_samples)
                silence_threshold = max(silence_threshold, ambient_level * 2.0)
            
            frames = []
            speech_started = False
            silence_start = None
            start_time = time.time()
            
            while True:
                elapsed = time.time() - start_time
                
                # Check timeout
                if not speech_started and elapsed > timeout:
                    print("❌ No speech detected (timeout)")
                    return None
                
                # Check phrase time limit
                if speech_started and elapsed > phrase_time_limit:
                    break
                
                # Read audio chunk
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    frames.append(audio_chunk)
                except Exception:
                    continue
                
                # Detect speech/silence
                level = np.abs(audio_chunk).mean()
                
                if level > silence_threshold:
                    speech_started = True
                    silence_start = None
                elif speech_started:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > silence_duration:
                        # End of speech detected
                        break
            
            stream.stop_stream()
            stream.close()
            
            if not frames:
                return None
            
            # Combine all audio
            audio_data = np.concatenate(frames)
            
            print("⏳ Transcribing...")
            text = self.transcribe(audio_data)
            
            if text:
                print(f"✓ Heard: {text}")
            
            return text if text else None
            
        except Exception as e:
            print(f"❌ Listen error: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if Whisper STT is ready."""
        return self.model is not None
    
    def cleanup(self):
        """Release resources."""
        if self._audio:
            self._audio.terminate()
            self._audio = None


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_whisper_stt: Optional[WhisperSTT] = None


def get_whisper_stt() -> WhisperSTT:
    """Get or create the global Whisper STT instance."""
    global _whisper_stt
    if _whisper_stt is None:
        _whisper_stt = WhisperSTT()
    return _whisper_stt


def listen_whisper(timeout: float = 5.0, phrase_time_limit: float = 10.0) -> Optional[str]:
    """
    Convenience function to listen and transcribe using Whisper.
    
    Args:
        timeout: Max seconds to wait for speech
        phrase_time_limit: Max seconds of speech
        
    Returns:
        Transcribed text or None
    """
    stt = get_whisper_stt()
    if stt.is_available():
        return stt.listen(timeout=timeout, phrase_time_limit=phrase_time_limit)
    return None


def whisper_status() -> dict:
    """Get Whisper STT status."""
    return {
        "whisper_available": WHISPER_AVAILABLE,
        "pyaudio_available": PYAUDIO_AVAILABLE,
        "vad_available": VAD_AVAILABLE,
    }
