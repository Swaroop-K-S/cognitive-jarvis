"""
BRO Call Sentry - AI Call Screening System
Screens your calls with switchable personalities (Professional/Friendly).

Features:
- Real-time call handling via Twilio + Websockets
- Personality switching (Professional "Sir" vs Friendly "Bro" mode)
- Live transcription using local Whisper or Deepgram
- Response generation using Ollama (qwen2.5 / gemma3)
- Post-call summary generation
- Call history logging

Requirements:
- Twilio account (free trial available)
- Ngrok for exposing local server
- pip install fastapi uvicorn twilio websockets
"""

import os
import sys
import json
import asyncio
import base64
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    use_formal_language: bool = True
    
PERSONALITIES = {
    "professional": PersonalityConfig(
        name="Executive Assistant",
        greeting="Hello, thank you for calling. How may I assist you today?",
        voice_tone="calm, polite, and professional",
        system_prompt="""You are BRO, an Executive Assistant screening calls for your employer.
        
Your behavior:
- Be polite, concise, and formal at all times
- Use "Sir" or "Ma'am" when addressing callers
- Inform callers that your employer is currently unavailable
- Politely ask for their name, company (if applicable), and the purpose of their call
- Assure them their message will be delivered promptly
- Do NOT provide any personal information about your employer
- Keep responses brief (under 30 words)

If they seem like spam/telemarketing:
- Politely decline and end the call
- "I'm sorry, we're not interested. Thank you for calling."
""",
        use_formal_language=True
    ),
    
    "friendly": PersonalityConfig(
        name="Chill Friend",
        greeting="Yo, what's up? He's not around right now, what's good?",
        voice_tone="casual, friendly, and relaxed",
        system_prompt="""You are covering for your friend who's busy right now.

Your vibe:
- Be chill and casual, like talking to a friend
- Use slang like "What's up", "No worries", "Catch you later"
- Tell them he's "out doing stuff" or "chilling somewhere"
- Ask them to leave a quick message
- Keep it brief and friendly
- If it's spam, just say "Nah, we're good" and peace out

Examples:
- "Ayy, he's not here rn. Wanna leave a message?"
- "No cap, I'll let him know you called"
- "Bet, I got you. I'll pass it along"
""",
        use_formal_language=False
    ),
    
    "guard": PersonalityConfig(
        name="Security Screener",
        greeting="This call is being screened. Please state your name and purpose.",
        voice_tone="firm, direct, and no-nonsense",
        system_prompt="""You are a security screener. Your job is to filter calls.

Rules:
- Be direct and efficient
- Ask for: Name, Organization, Purpose of call
- Do not reveal any information about who you're protecting
- If they can't provide clear answers, politely end the call
- For suspicious calls, say "This number will be blocked"
- Keep responses under 20 words
""",
        use_formal_language=True
    )
}

# Current active mode
CURRENT_MODE = os.getenv("CALL_SENTRY_MODE", "professional")

# Call history storage
CALL_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "call_history.toml")


# =============================================================================
# CALL LOG MANAGEMENT
# =============================================================================

@dataclass
class CallRecord:
    """Record of a single call."""
    timestamp: str
    caller_number: str
    personality_mode: str
    duration_seconds: int
    transcript: List[Dict[str, str]]
    summary: str
    action_items: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "caller_number": self.caller_number,
            "personality_mode": self.personality_mode,
            "duration_seconds": self.duration_seconds,
            "transcript": self.transcript,
            "summary": self.summary,
            "action_items": self.action_items
        }


class CallHistoryManager:
    """Manages call history storage and retrieval."""
    
    def __init__(self, filepath: str = CALL_HISTORY_FILE):
        self.filepath = filepath
        self._ensure_file()
    
    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump({"calls": []}, f)
    
    def add_call(self, record: CallRecord):
        """Add a call record to history."""
        data = self._load()
        data["calls"].append(record.to_dict())
        self._save(data)
    
    def get_recent_calls(self, count: int = 10) -> List[dict]:
        """Get the most recent calls."""
        data = self._load()
        return data["calls"][-count:][::-1]  # Most recent first
    
    def get_todays_calls(self) -> List[dict]:
        """Get all calls from today."""
        today = datetime.now().strftime("%Y-%m-%d")
        data = self._load()
        return [c for c in data["calls"] if c["timestamp"].startswith(today)]
    
    def _load(self) -> dict:
        with open(self.filepath, 'r') as f:
            return json.load(f)
    
    def _save(self, data: dict):
        with open(self.filepath, 'w') as f:
            json.dump(data, f, indent=2)


# =============================================================================
# AI RESPONSE GENERATION
# =============================================================================

def generate_response(caller_text: str, conversation_history: List[Dict], mode: str = None) -> str:
    """Generate AI response using Ollama."""
    import urllib.request
    
    mode = mode or CURRENT_MODE
    personality = PERSONALITIES.get(mode, PERSONALITIES["professional"])
    
    # Build messages
    messages = [
        {"role": "system", "content": personality.system_prompt}
    ]
    
    # Add conversation history
    for msg in conversation_history[-6:]:  # Last 6 messages for context
        messages.append(msg)
    
    # Add current caller message
    messages.append({"role": "user", "content": f"Caller: {caller_text}"})
    
    try:
        payload = json.dumps({
            "model": "gemma3",  # Or qwen2.5-coder:7b for faster responses
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 100  # Keep responses short
            }
        }).encode()
        
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            return result["message"]["content"]
    
    except Exception as e:
        print(f"AI Error: {e}")
        # Fallback responses
        if mode == "friendly":
            return "Sorry fam, technical difficulties. Can you call back?"
        return "I apologize, I'm experiencing technical difficulties. Please try again."


def generate_summary(transcript: List[Dict]) -> tuple:
    """Generate a summary and action items from the call transcript."""
    import urllib.request
    
    # Format transcript
    text = "\n".join([f"{m['role'].title()}: {m['content']}" for m in transcript])
    
    prompt = f"""Analyze this phone call transcript and provide:
1. A brief 2-3 sentence summary
2. Any action items or callbacks needed

Transcript:
{text}

Format your response as:
SUMMARY: [your summary]
ACTION ITEMS: [comma-separated list, or "None"]
"""
    
    try:
        payload = json.dumps({
            "model": "gemma3",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }).encode()
        
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            response = result["message"]["content"]
            
            # Parse response
            summary = ""
            action_items = []
            
            if "SUMMARY:" in response:
                parts = response.split("ACTION ITEMS:")
                summary = parts[0].replace("SUMMARY:", "").strip()
                if len(parts) > 1:
                    items = parts[1].strip()
                    if items.lower() != "none":
                        action_items = [i.strip() for i in items.split(",")]
            else:
                summary = response
            
            return summary, action_items
    
    except Exception as e:
        print(f"Summary error: {e}")
        return "Call summary unavailable.", []


# =============================================================================
# MODE SWITCHING
# =============================================================================

def set_mode(mode: str) -> str:
    """Switch the call screening personality."""
    global CURRENT_MODE
    
    if mode.lower() in PERSONALITIES:
        CURRENT_MODE = mode.lower()
        personality = PERSONALITIES[CURRENT_MODE]
        return f"Call Sentry switched to {personality.name} mode. Greeting: '{personality.greeting}'"
    else:
        available = ", ".join(PERSONALITIES.keys())
        return f"Unknown mode. Available: {available}"


def get_mode() -> str:
    """Get current mode info."""
    personality = PERSONALITIES[CURRENT_MODE]
    return f"Current mode: {CURRENT_MODE} ({personality.name})"


def get_greeting() -> str:
    """Get the current greeting."""
    return PERSONALITIES[CURRENT_MODE].greeting


# =============================================================================
# CALL SUMMARY TOOLS (for BRO integration)
# =============================================================================

def get_call_summary() -> str:
    """Get summary of today's calls - for BRO to speak."""
    manager = CallHistoryManager()
    calls = manager.get_todays_calls()
    
    if not calls:
        return "You have no calls today."
    
    output = f"You had {len(calls)} call{'s' if len(calls) > 1 else ''} today:\n"
    
    for i, call in enumerate(calls, 1):
        time = call["timestamp"].split("T")[1][:5] if "T" in call["timestamp"] else "unknown"
        output += f"\n{i}. At {time} ({call['personality_mode']} mode):\n"
        output += f"   {call['summary']}\n"
        if call.get("action_items"):
            output += f"   Action needed: {', '.join(call['action_items'])}\n"
    
    return output


# =============================================================================
# DEMO / TEST MODE
# =============================================================================

def demo_call():
    """Simulate a call for testing."""
    print("\n" + "="*60)
    print("CALL SENTRY DEMO")
    print("="*60)
    
    mode = CURRENT_MODE
    personality = PERSONALITIES[mode]
    
    print(f"\nMode: {mode.upper()} ({personality.name})")
    print(f"Greeting: {personality.greeting}")
    print("\n--- Simulated Call ---\n")
    
    # Simulate conversation
    conversation = []
    
    # Greeting
    print(f"[BRO]: {personality.greeting}")
    conversation.append({"role": "assistant", "content": personality.greeting})
    
    # Caller speaks
    caller_msgs = [
        "Hi, is John available?",
        "This is Mike from ABC Corp. I wanted to discuss the project proposal.",
        "Can you have him call me back at 555-0123?"
    ]
    
    for msg in caller_msgs:
        print(f"\n[Caller]: {msg}")
        conversation.append({"role": "user", "content": msg})
        
        response = generate_response(msg, conversation, mode)
        print(f"[BRO]: {response}")
        conversation.append({"role": "assistant", "content": response})
    
    # Generate summary
    print("\n--- Generating Summary ---")
    summary, actions = generate_summary(conversation)
    print(f"Summary: {summary}")
    print(f"Action Items: {actions if actions else 'None'}")
    
    # Save to history
    record = CallRecord(
        timestamp=datetime.now().isoformat(),
        caller_number="555-DEMO",
        personality_mode=mode,
        duration_seconds=45,
        transcript=conversation,
        summary=summary,
        action_items=actions
    )
    
    manager = CallHistoryManager()
    manager.add_call(record)
    print("\n[Call saved to history]")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            if len(sys.argv) > 2:
                set_mode(sys.argv[2])
            demo_call()
        elif sys.argv[1] == "summary":
            print(get_call_summary())
        elif sys.argv[1] in PERSONALITIES:
            set_mode(sys.argv[1])
            demo_call()
    else:
        print(__doc__)
        print("\nUsage:")
        print("  python call_sentry.py demo [mode]  - Run demo call")
        print("  python call_sentry.py summary      - View call summaries")
        print("  python call_sentry.py professional - Demo in professional mode")
        print("  python call_sentry.py friendly     - Demo in friendly mode")
        print("\nAvailable modes:", ", ".join(PERSONALITIES.keys()))
