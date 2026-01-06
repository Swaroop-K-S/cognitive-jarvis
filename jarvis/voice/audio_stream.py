import pyaudio
import numpy as np
import threading
import time
from jarvis.config import MIC_DEVICE_INDEX

class AudioStreamAnalyzer:
    def __init__(self):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.running = False
        self.thread = None
        
        self.current_volume = 0
        self.fft_data = np.zeros(30) # 30 bars
        
    def start(self):
        if self.running: return
        
        try:
            self.stream = self.p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=MIC_DEVICE_INDEX,
                frames_per_buffer=self.chunk
            )
            self.running = True
            self.thread = threading.Thread(target=self._process, daemon=True)
            self.thread.start()
            print("🎤 Audio Stream Started")
        except Exception as e:
            print(f"❌ Audio Stream Error: {e}")

    def stop(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except: pass
            self.stream = None

    def _process(self):
        while self.running:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                # Convert to numpy
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Volume
                vol = np.abs(audio_data).mean()
                self.current_volume = vol
                
                # FFT (Frequency Analysis)
                fft = np.fft.rfft(audio_data)
                fft = np.abs(fft)
                
                # Binning for 30 bars
                # We focus on 0-4000Hz range roughly
                step = len(fft) // 40 # Take lower frequencies
                binned = []
                for i in range(30):
                    start = i * step
                    end = start + step
                    val = np.mean(fft[start:end])
                    binned.append(val)
                
                # Log scale + Normalization
                self.fft_data = np.log10(np.array(binned) + 1) * 10
                
            except Exception as e:
                print(f"Stream Loop Error: {e}")
                time.sleep(0.1)

    def get_levels(self):
        """Get 30 normalized levels for visualization (0-50 approx)"""
        return self.fft_data
