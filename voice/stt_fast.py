"""
Faster Whisper STT Implementation for Local Voice Recognition.
"""
import os
import time
from faster_whisper import WhisperModel
from jarvis.config import MIC_DEVICE_INDEX

# Model settings
MODEL_SIZE = "medium"  # 'tiny', 'base', 'small', 'medium', 'large-v2'
COMPUTE_TYPE = "int8"  # 'float16' for GPU, 'int8' for CPU/Mixed

class FasterWhisperSTT:
    def __init__(self):
        print(f"    ⏳ Loading Faster-Whisper ({MODEL_SIZE})...")
        start = time.time()
        # Run on CPU to avoid CUDA complexity for now, or "cuda" if available
        device = "cuda" if self._check_cuda() else "cpu"
        
        self.model = WhisperModel(MODEL_SIZE, device=device, compute_type=COMPUTE_TYPE)
        print(f"    ✅ Whisper Loaded in {time.time() - start:.2f}s ({device})")

    def _check_cuda(self):
        # Simplified check - implies torch is installed with cuda support
        # For now defaults to CPU for stability unless user has configured otherwise
        return False 

    def transcribe(self, audio_source):
        """
        Transcribe audio data. 
        Args:
            audio_source: File path (str) or binary file-like object (BytesIO)
        """
        # beam_size=5 is good for accuracy
        segments, info = self.model.transcribe(audio_source, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()
        return text

stt_instance = None

def get_stt():
    global stt_instance
    if stt_instance is None:
        stt_instance = FasterWhisperSTT()
    return stt_instance

def listen_and_transcribe_fast(audio_file_path):
    """Convenience function to transcribe an audio file."""
    stt = get_stt()
    return stt.transcribe(audio_file_path)
