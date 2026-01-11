from jarvis.voice.tts import say
import time

print("Testing Voice...")
try:
    say("System Check. Voice Module Online. Hello Boss.")
    print("Voice test complete.")
except Exception as e:
    print(f"FAILED: {e}")
