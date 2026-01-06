"""
BRO Call Sentry - LOCAL VERSION
100% Offline AI Call Screening - No cloud services required!

How it works:
1. Put your phone on speaker OR use audio cable to PC
2. BRO listens via your PC microphone (Vosk - fully offline)
3. AI thinks using Ollama (local LLM)
4. Speaks response via your PC speakers (pyttsx3 - offline)
5. Summary saved locally

No Twilio, no cloud, no internet required!
"""

import os
import sys
import json
import time
import threading
import queue
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================

# Vosk for offline speech recognition
VOSK_AVAILABLE = False
try:
    import vosk
    import pyaudio
    VOSK_AVAILABLE = True
except ImportError:
    print("Vosk not available. Install: pip install vosk pyaudio")

# Local TTS
TTS_AVAILABLE = False
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    print("TTS not available. Install: pip install pyttsx3")

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class PersonalityConfig:
    """Configuration for a call screening personality."""
    name: str
    greeting: str
    voice_tone: str
    system_prompt: str
    tts_rate: int = 175  # Words per minute
    
PERSONALITIES = {
    "professional": PersonalityConfig(
        name="Executive Assistant",
        greeting="Hello, thank you for calling. Mr. Creation is currently unavailable. How may I assist you?",
        voice_tone="calm, polite, and professional",
        system_prompt="""You are BRO, an Executive Assistant screening calls.

Your behavior:
- Be polite, concise, and formal
- Use "Sir" or "Ma'am" when addressing callers
- Inform callers that your employer is currently unavailable
- Ask for their name and the purpose of their call
- Assure them their message will be delivered
- Keep responses under 25 words
- Do NOT reveal personal information

If spam/telemarketing: "I'm sorry, we're not interested. Goodbye."
""",
        tts_rate=160
    ),
    
    "friendly": PersonalityConfig(
        name="Chill Friend",
        greeting="Yo, what's up? He's busy right now. What you need?",
        voice_tone="casual, friendly, and relaxed",
        system_prompt="""You're covering for your friend who's busy.

Your vibe:
- Be chill and casual
- Use slang: "What's up", "No worries", "Bet", "Peace"
- Tell them he's "out doing stuff"
- Ask them to leave a quick message
- Keep it brief - under 20 words
- For spam: "Nah, we're good. Later!"
""",
        tts_rate=185
    ),
    
    "guard": PersonalityConfig(
        name="Security Screener", 
        greeting="This call is being screened. State your name and purpose.",
        voice_tone="firm, direct, no-nonsense",
        system_prompt="""You are a security screener. Filter calls strictly.

Rules:
- Be direct and efficient
- Ask for: Name, Organization, Purpose
- Do not reveal any information
- If unclear answers: "This call cannot be completed."
- Keep responses under 15 words
- Block suspicious calls immediately
""",
        tts_rate=150
    )
}

# Current mode
CURRENT_MODE = "professional"

# Vosk model path (auto-downloads if missing)
VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "vosk-model")

# Call history
CALL_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "call_history.toml")


# =============================================================================
# CALL RECORD MANAGEMENT
# =============================================================================

@dataclass
class CallRecord:
    """Record of a single call."""
    timestamp: str
    personality_mode: str
    duration_seconds: int
    transcript: List[Dict[str, str]]
    summary: str
    action_items: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "personality_mode": self.personality_mode,
            "duration_seconds": self.duration_seconds,
            "transcript": self.transcript,
            "summary": self.summary,
            "action_items": self.action_items
        }


class CallHistoryManager:
    """Manages call history storage."""
    
    def __init__(self, filepath: str = CALL_HISTORY_FILE):
        self.filepath = filepath
        self._ensure_file()
    
    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                f.write(_toml_dumps({"calls": []})); # record: CallRecord):
        data = self._load()
        data["calls"].append(record.to_dict())
        self._save(data)
    
    def get_recent_calls(self, count: int = 10) -> List[dict]:
        data = self._load()
        return data["calls"][-count:][::-1]
    
    def get_todays_calls(self) -> List[dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        data = self._load()
        return [c for c in data["calls"] if c["timestamp"].startswith(today)]
    
    def _load(self) -> dict:
        with open(self.filepath, 'r') as f:
            return tomllib.load(f)
    
    def _save(self, data: dict):
        with open(self.filepath, 'w') as f:
            f.write(_toml_dumps(data)); # indent=2)


# =============================================================================
# LOCAL SPEECH RECOGNITION (Vosk)
# =============================================================================

class LocalSpeechRecognizer:
    """Offline speech recognition using Vosk."""
    
    def __init__(self):
        self.model = None
        self.recognizer = None
        self._audio = None
        self._stream = None
        
    def initialize(self) -> bool:
        """Initialize the Vosk model."""
        if not VOSK_AVAILABLE:
            print("[!] Vosk not installed")
            return False
        
        # Check for model
        if os.path.exists(VOSK_MODEL_PATH):
            model_path = VOSK_MODEL_PATH
        else:
            # Try to find any vosk model
            parent = os.path.dirname(VOSK_MODEL_PATH)
            models = [d for d in os.listdir(parent) if d.startswith("vosk-model")] if os.path.exists(parent) else []
            if models:
                model_path = os.path.join(parent, models[0])
            else:
                print("[!] Vosk model not found. Downloading small model...")
                self._download_model()
                model_path = VOSK_MODEL_PATH
        
        try:
            vosk.SetLogLevel(-1)  # Suppress logs
            self.model = vosk.Model(model_path)
            self._audio = pyaudio.PyAudio()
            return True
        except Exception as e:
            print(f"[!] Vosk init error: {e}")
            return False
    
    def _download_model(self):
        """Download Vosk model."""
        import urllib.request
        import zipfile
        
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        zip_path = VOSK_MODEL_PATH + ".zip"
        
        print("    Downloading Vosk model (~40MB)...")
        urllib.request.urlretrieve(url, zip_path)
        
        print("    Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(os.path.dirname(VOSK_MODEL_PATH))
        
        # Rename to standard path
        extracted = os.path.join(os.path.dirname(VOSK_MODEL_PATH), "vosk-model-small-en-us-0.15")
        if os.path.exists(extracted):
            os.rename(extracted, VOSK_MODEL_PATH)
        
        os.remove(zip_path)
        print("    Model ready!")
    
    def listen_once(self, timeout: float = 10.0) -> Optional[str]:
        """Listen for speech and return transcription."""
        if not self.model:
            return None
        
        try:
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4000
            )
            
            print("    [Listening...]")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                data = self._stream.read(4000, exception_on_overflow=False)
                
                if self.recognizer.AcceptWaveform(data):
                    result = tomllib.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()
                    if text:
                        self._stream.stop_stream()
                        self._stream.close()
                        return text
            
            # Get final result
            result = tomllib.loads(self.recognizer.FinalResult())
            self._stream.stop_stream()
            self._stream.close()
            return result.get("text", "").strip() or None
            
        except Exception as e:
            print(f"    [Listen error: {e}]")
            return None
    
    def cleanup(self):
        if self._stream:
            self._stream.close()
        if self._audio:
            self._audio.terminate()


# =============================================================================
# LOCAL TEXT-TO-SPEECH
# =============================================================================

class LocalTTS:
    """Offline text-to-speech using pyttsx3."""
    
    def __init__(self):
        self.engine = None
        
    def initialize(self) -> bool:
        if not TTS_AVAILABLE:
            return False
        try:
            self.engine = pyttsx3.init()
            return True
        except:
            return False
    
    def speak(self, text: str, rate: int = 175):
        """Speak text aloud."""
        if not self.engine:
            print(f"[BRO would say]: {text}")
            return
        
        try:
            self.engine.setProperty('rate', rate)
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"[TTS Error: {e}]")
            print(f"[BRO]: {text}")


# =============================================================================
# AI RESPONSE GENERATION (Local Ollama)
# =============================================================================

def generate_response(caller_text: str, conversation: List[Dict], mode: str) -> str:
    """Generate AI response using local Ollama."""
    import urllib.request
    
    personality = PERSONALITIES.get(mode, PERSONALITIES["professional"])
    
    messages = [{"role": "system", "content": personality.system_prompt}]
    
    # Add conversation history
    for msg in conversation[-4:]:
        messages.append(msg)
    
    messages.append({"role": "user", "content": f"Caller says: {caller_text}"})
    
    try:
        payload = json.dumps({
            "model": "gemma3",  # Use your installed model
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 60}
        }).encode()
        
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = tomllib.loads(resp.read().decode())
            return result["message"]["content"]
    
    except Exception as e:
        print(f"    [AI Error: {e}]")
        return "I'm sorry, I'm having technical difficulties. Please call back later."


def generate_summary(transcript: List[Dict]) -> tuple:
    """Generate call summary locally."""
    import urllib.request
    
    text = "\n".join([f"{m['role']}: {m['content']}" for m in transcript])
    
    prompt = f"""Summarize this call in 2 sentences. List any callback requests.

{text}

SUMMARY:"""
    
    try:
        payload = json.dumps({
            "model": "gemma3",
            "prompt": prompt,
            "stream": False
        }).encode()
        
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = tomllib.loads(resp.read().decode())
            summary = result.get("response", "Call recorded.")
            
            # Extract action items
            actions = []
            if "call back" in summary.lower() or "callback" in summary.lower():
                actions.append("Return call")
            
            return summary.strip(), actions
    except:
        return "Call recorded.", []


# =============================================================================
# MODE SWITCHING
# =============================================================================

def set_mode(mode: str) -> str:
    """Switch personality mode."""
    global CURRENT_MODE
    if mode.lower() in PERSONALITIES:
        CURRENT_MODE = mode.lower()
        p = PERSONALITIES[CURRENT_MODE]
        return f"Switched to {p.name} mode."
    return f"Unknown mode. Available: {', '.join(PERSONALITIES.keys())}"


def get_mode() -> str:
    """Get current mode."""
    return f"Current mode: {CURRENT_MODE} ({PERSONALITIES[CURRENT_MODE].name})"


def get_call_summary() -> str:
    """Get today's call summaries."""
    manager = CallHistoryManager()
    calls = manager.get_todays_calls()
    
    if not calls:
        return "No calls today."
    
    output = f"You had {len(calls)} call(s) today:\n"
    for i, call in enumerate(calls, 1):
        output += f"\n{i}. ({call['personality_mode']}): {call['summary']}\n"
    return output


# =============================================================================
# MAIN CALL HANDLER
# =============================================================================

class LocalCallSentry:
    """
    Fully local call screening system.
    
    Usage:
    1. Put phone on speaker near PC microphone
    2. Run this to start screening
    3. BRO listens, responds, and logs calls
    """
    
    def __init__(self, mode: str = "professional"):
        global CURRENT_MODE
        CURRENT_MODE = mode
        
        self.stt = LocalSpeechRecognizer()
        self.tts = LocalTTS()
        self.running = False
        
    def start(self):
        """Start the call sentry."""
        print("\n" + "="*50)
        print("BRO CALL SENTRY - LOCAL MODE")
        print("="*50)
        print(f"Mode: {CURRENT_MODE} ({PERSONALITIES[CURRENT_MODE].name})")
        print("\nSetup:")
        print("  1. Put your phone on speaker")
        print("  2. Place near PC microphone")
        print("  3. Press ENTER when caller is on the line")
        print("  4. Press Ctrl+C to end call")
        print("="*50)
        
        # Initialize
        if not self.stt.initialize():
            print("[!] Speech recognition failed to initialize")
            return
        
        self.tts.initialize()
        
        self.running = True
        
        try:
            while self.running:
                input("\n[Press ENTER when call starts...]")
                self._handle_call()
                
        except KeyboardInterrupt:
            print("\n[Call Sentry stopped]")
        finally:
            self.stt.cleanup()
    
    def _handle_call(self):
        """Handle a single call."""
        personality = PERSONALITIES[CURRENT_MODE]
        conversation = []
        start_time = datetime.now()
        
        print(f"\n📞 CALL STARTED ({CURRENT_MODE} mode)")
        print("-" * 40)
        
        # Greeting
        print(f"[BRO]: {personality.greeting}")
        self.tts.speak(personality.greeting, personality.tts_rate)
        conversation.append({"role": "assistant", "content": personality.greeting})
        
        # Conversation loop
        max_turns = 10
        for turn in range(max_turns):
            # Listen for caller
            caller_text = self.stt.listen_once(timeout=15)
            
            if not caller_text:
                print("[No speech detected]")
                response = "I didn't catch that. Could you please repeat?"
            else:
                print(f"[Caller]: {caller_text}")
                conversation.append({"role": "user", "content": caller_text})
                
                # Check for goodbye
                if any(word in caller_text.lower() for word in ["bye", "goodbye", "that's all", "thanks", "thank you"]):
                    response = "Goodbye! Have a great day."
                    print(f"[BRO]: {response}")
                    self.tts.speak(response, personality.tts_rate)
                    conversation.append({"role": "assistant", "content": response})
                    break
                
                # Generate response
                response = generate_response(caller_text, conversation, CURRENT_MODE)
            
            print(f"[BRO]: {response}")
            self.tts.speak(response, personality.tts_rate)
            conversation.append({"role": "assistant", "content": response})
        
        # End call
        duration = (datetime.now() - start_time).seconds
        print("-" * 40)
        print(f"📴 CALL ENDED (Duration: {duration}s)")
        
        # Generate summary
        if len(conversation) > 2:
            print("\n📝 Generating summary...")
            summary, actions = generate_summary(conversation)
            print(f"   Summary: {summary}")
            if actions:
                print(f"   Actions: {actions}")
            
            # Save
            record = CallRecord(
                timestamp=datetime.now().isoformat(),
                personality_mode=CURRENT_MODE,
                duration_seconds=duration,
                transcript=conversation,
                summary=summary,
                action_items=actions
            )
            CallHistoryManager().add_call(record)
            print("   [Saved to history]")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Call Sentry - Local Edition")
    parser.add_argument("command", nargs="?", default="start", 
                       choices=["start", "summary", "modes"],
                       help="Command to run")
    parser.add_argument("--mode", "-m", default="professional",
                       choices=list(PERSONALITIES.keys()),
                       help="Personality mode")
    
    args = parser.parse_args()
    
    if args.command == "start":
        sentry = LocalCallSentry(mode=args.mode)
        sentry.start()
    
    elif args.command == "summary":
        print(get_call_summary())
    
    elif args.command == "modes":
        print("\nAvailable Modes:")
        for name, p in PERSONALITIES.items():
            print(f"\n  {name.upper()} - {p.name}")
            print(f"    Greeting: \"{p.greeting}\"")


if __name__ == "__main__":
    main()
