import speech_recognition as sr
import time

def debug_audio():
    print("🎤 Audio Debugger")
    print("--------------------------------")
    
    # 1. List Microphones
    print("\n🔍 Scanning audio devices...")
    mics = sr.Microphone.list_microphone_names()
    
    if not mics:
        print("❌ No microphones found!")
        return

    for i, name in enumerate(mics):
        print(f"  [{i}] {name}")
    
    # 2. Test Default Mic
    print("\n🎧 Testing Default Microphone...")
    r = sr.Recognizer()
    r.energy_threshold = 300  # Default
    r.dynamic_energy_threshold = True
    
    try:
        with sr.Microphone() as source:
            print(f"  > Using device: {source.device_index}")
            print("  > Please speak now! (Press Ctrl+C to stop)")
            print("  > Monitoring energy levels...")
            
            # Adjust for ambient noise
            print("  > adjusting for ambient noise (1s)...")
            r.adjust_for_ambient_noise(source, duration=1)
            print(f"  > Energy Threshold set to: {r.energy_threshold}")
            
            start = time.time()
            while time.time() - start < 10:  # Run for 10 seconds
                # Just read chunks to show we can access the stream
                buffer = source.stream.read(source.CHUNK)
                # Calculating RMS is complex here without numpy, so we'll just try to listen
                print(".", end="", flush=True)
                time.sleep(0.1)
                
            print("\n  > Microphone stream accessible.")
            
            print("\n🎤 Attempting actual recognition test (Speak 'Hello BRO')...")
            try:
                audio = r.listen(source, timeout=5)
                print("  > Audio captured. Recognizing...")
                text = r.recognize_google(audio)
                print(f"  > SUCCESS: Recognized text: '{text}'")
            except sr.WaitTimeoutError:
                print("  > FAILURE: Timeout (No speech detected)")
            except sr.UnknownValueError:
                print("  > FAILURE: Unknown Value (Speech too indistinct)")
            
    except OSError as e:
        print(f"\n❌ Error accessing microphone: {e}")
        print("Tip: Check Windows Privacy settings -> Microphone -> Allow desktop apps")

if __name__ == "__main__":
    try:
        debug_audio()
    except KeyboardInterrupt:
        print("\nStopped.")
