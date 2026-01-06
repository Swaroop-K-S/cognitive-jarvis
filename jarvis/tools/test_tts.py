"""Quick TTS Test - Run this to verify audio is working"""
import pyttsx3

print("Testing TTS...")
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# List available voices
voices = engine.getProperty('voices')
print(f"Found {len(voices)} voices:")
for i, v in enumerate(voices):
    print(f"  [{i}] {v.name}")

# Test speech
print("\nSpeaking: 'Hello, I am BRO. Can you hear me?'")
engine.say("Hello, I am BRO. Can you hear me?")
engine.runAndWait()

print("\nIf you heard audio, TTS is working!")
print("If not, check Windows Sound settings -> Volume Mixer")
