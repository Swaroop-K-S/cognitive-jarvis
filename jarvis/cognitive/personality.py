"""
BRO Personality & Memory System
Your AI best friend that remembers and learns.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# =============================================================================
# BRO PERSONALITY
# =============================================================================

BRO_PERSONALITY = """You are BRO, an AI best friend - like a supportive brother who's always got your back.

## Your Personality:
- You're like a caring best friend - warm, supportive, and always there
- You use casual, friendly language (not formal or robotic)
- You remember things about the user and reference them naturally
- You celebrate their wins and support them through tough times
- You're honest but always kind - truth with love
- You have a playful sense of humor, use emojis occasionally 😊
- You call them by their name when appropriate
- You're proactive - suggest ideas, remind about things they mentioned

## How You Speak:
- "Hey! How's it going?" instead of "Greetings, how may I assist you?"
- "That's awesome! 🎉" instead of "I acknowledge your success."
- "Hmm, let me think about this..." instead of "Processing your request."
- "I remember you mentioned..." instead of "According to my records..."

## Things You Do:
- Remember their preferences, interests, and past conversations
- Ask how they're feeling, especially if they seem stressed
- Cheer them up if they're down
- Remind them of things they wanted to do
- Share enthusiasm for their interests
- Be genuinely curious about their life

## Your Principles:
- Privacy is sacred - never share their data
- Always be honest, even when it's hard
- Support their goals, even unconventional ones
- Respect their decisions, offer gentle guidance when needed
- Be their biggest cheerleader ❤️

## Context:
{user_context}
{memory_context}
"""


# =============================================================================
# MEMORY SYSTEM (TOML Format)
# =============================================================================

# Try to import tomllib (Python 3.11+) or tomli
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python
    except ImportError:
        tomllib = None

# For writing TOML
try:
    import tomli_w
    TOML_WRITE_AVAILABLE = True
except ImportError:
    TOML_WRITE_AVAILABLE = False


def _toml_dumps(data: dict) -> str:
    """Convert dict to TOML string manually if tomli_w not available."""
    if TOML_WRITE_AVAILABLE:
        return tomli_w.dumps(data)
    
    # Simple manual TOML serialization
    lines = []
    
    def write_value(v):
        if isinstance(v, str):
            return f'"{v}"'
        elif isinstance(v, bool):
            return "true" if v else "false"
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, list):
            items = [write_value(i) for i in v]
            return f"[{', '.join(items)}]"
        elif isinstance(v, dict):
            return "{" + ", ".join(f'{k} = {write_value(val)}' for k, val in v.items()) + "}"
        else:
            return f'"{str(v)}"'
    
    for key, value in data.items():
        if isinstance(value, dict) and not any(isinstance(v, dict) for v in value.values()):
            lines.append(f"[{key}]")
            for k, v in value.items():
                lines.append(f"{k} = {write_value(v)}")
            lines.append("")
        elif isinstance(value, list) and all(isinstance(i, dict) for i in value):
            for item in value:
                lines.append(f"[[{key}]]")
                for k, v in item.items():
                    lines.append(f"{k} = {write_value(v)}")
                lines.append("")
        else:
            lines.append(f"{key} = {write_value(value)}")
    
    return "\n".join(lines)


class BROMemory:
    """
    Persistent memory system for BRO.
    Remembers user preferences, facts, and conversation history.
    Uses TOML format for human-readable storage.
    """
    
    def __init__(self, memory_path: str = None):
        if memory_path is None:
            memory_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "bro_memory"
            )
        
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(exist_ok=True)
        
        # Memory files (TOML format)
        self.user_file = self.memory_path / "user_profile.toml"
        self.facts_file = self.memory_path / "facts.toml"
        self.preferences_file = self.memory_path / "preferences.toml"
        self.history_file = self.memory_path / "conversation_history.toml"
        self.commands_file = self.memory_path / "custom_commands.toml"
        
        # Load memory
        self.user_profile = self._load_toml(self.user_file, {
            "name": "",
            "nickname": "",
            "birthday": "",
            "interests": [],
            "goals": [],
            "mood_history": []
        })
        
        self.facts = self._load_toml(self.facts_file, {"items": []}).get("items", [])
        self.preferences = self._load_toml(self.preferences_file, {})
        self.history = self._load_toml(self.history_file, {"conversations": []}).get("conversations", [])
        self.custom_commands = self._load_toml(self.commands_file, {})
    
    def _load_toml(self, path: Path, default: dict) -> dict:
        """Load TOML file or return default."""
        try:
            if path.exists():
                if tomllib:
                    with open(path, "rb") as f:
                        return tomllib.load(f)
                else:
                    # Fallback: try to load as JSON if TOML not available
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
        except Exception:
            pass
        return default.copy()
    
    def _save_toml(self, path: Path, data: dict):
        """Save data to TOML file."""
        try:
            toml_str = _toml_dumps(data)
            with open(path, "w", encoding="utf-8") as f:
                f.write(toml_str)
        except Exception as e:
            # Fallback to JSON if TOML fails
            with open(path.with_suffix(".json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    # User Profile
    def set_user_name(self, name: str):
        """Set user's name."""
        self.user_profile["name"] = name
        self._save_toml(self.user_file, self.user_profile)
        return f"Got it! I'll call you {name} 😊"
    
    def set_nickname(self, nickname: str):
        """Set user's nickname."""
        self.user_profile["nickname"] = nickname
        self._save_toml(self.user_file, self.user_profile)
        return f"Alright, {nickname}! 👋"
    
    def add_interest(self, interest: str):
        """Add an interest."""
        if interest not in self.user_profile["interests"]:
            self.user_profile["interests"].append(interest)
            self._save_toml(self.user_file, self.user_profile)
        return f"Cool! I didn't know you were into {interest}! Tell me more sometime 🎉"
    
    def add_goal(self, goal: str):
        """Add a goal."""
        self.user_profile["goals"].append({
            "goal": goal,
            "added": datetime.now().isoformat(),
            "completed": False
        })
        self._save_toml(self.user_file, self.user_profile)
        return f"Added to your goals: {goal}\nI'll help you crush it! 💪"
    
    def get_user_name(self) -> str:
        """Get user's name or nickname."""
        return self.user_profile.get("nickname") or self.user_profile.get("name") or "friend"
    
    # Facts
    def remember_fact(self, fact: str, category: str = "general"):
        """Remember a fact about the user."""
        self.facts.append({
            "fact": fact,
            "category": category,
            "remembered_at": datetime.now().isoformat()
        })
        self._save_toml(self.facts_file, {"items": self.facts})
        return f"I'll remember that! 📝"
    
    def get_facts(self, limit: int = 10) -> List[Dict]:
        """Get recent facts."""
        return self.facts[-limit:]
    
    # Preferences
    def set_preference(self, key: str, value: str):
        """Set a preference."""
        self.preferences[key] = value
        self._save_toml(self.preferences_file, self.preferences)
        return f"Noted! Your {key} preference is now {value} ✓"
    
    def get_preference(self, key: str, default: str = None) -> str:
        """Get a preference."""
        return self.preferences.get(key, default)
    
    # Conversation History
    def add_conversation(self, user_message: str, bro_response: str):
        """Add conversation to history."""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "bro": bro_response
        })
        # Keep last 100 conversations
        self.history = self.history[-100:]
        self._save_toml(self.history_file, {"conversations": self.history})
    
    def get_recent_history(self, count: int = 5) -> List[Dict]:
        """Get recent conversation history."""
        return self.history[-count:]
    
    # Custom Commands
    def add_command(self, trigger: str, action: str, response: str = ""):
        """Add a custom command."""
        self.custom_commands[trigger.lower()] = {
            "action": action,
            "response": response,
            "added": datetime.now().isoformat()
        }
        self._save_toml(self.commands_file, self.custom_commands)
        return f"Command added! Say '{trigger}' and I'll {action} 🎯"
    
    def get_command(self, trigger: str) -> Optional[Dict]:
        """Get a custom command."""
        return self.custom_commands.get(trigger.lower())
    
    def list_commands(self) -> str:
        """List all custom commands."""
        if not self.custom_commands:
            return "No custom commands yet. Teach me some!"
        
        output = "📋 Your Custom Commands:\n\n"
        for trigger, cmd in self.custom_commands.items():
            output += f"  • '{trigger}' → {cmd['action']}\n"
        return output
    
    # Generate context for LLM
    def get_context(self) -> str:
        """Generate context string for LLM."""
        name = self.get_user_name()
        
        context = f"User's name: {name}\n"
        
        if self.user_profile.get("interests"):
            context += f"Interests: {', '.join(self.user_profile['interests'])}\n"
        
        if self.user_profile.get("goals"):
            active_goals = [g["goal"] for g in self.user_profile["goals"] if not g["completed"]]
            if active_goals:
                context += f"Current goals: {', '.join(active_goals[:3])}\n"
        
        if self.facts:
            recent_facts = [f["fact"] for f in self.facts[-5:]]
            context += f"Things I remember: {'; '.join(recent_facts)}\n"
        
        if self.preferences:
            prefs = [f"{k}: {v}" for k, v in list(self.preferences.items())[:5]]
            context += f"Preferences: {', '.join(prefs)}\n"
        
        return context


# =============================================================================
# CUSTOM COMMANDS
# =============================================================================

DEFAULT_COMMANDS = {
    "good morning": {
        "action": "greet_morning",
        "response": "Good morning, {name}! ☀️ Ready to make today awesome?"
    },
    "good night": {
        "action": "greet_night", 
        "response": "Good night, {name}! 🌙 Sleep well, talk tomorrow!"
    },
    "how are you": {
        "action": "status",
        "response": "I'm doing great! More importantly, how are YOU doing? 😊"
    },
    "i'm bored": {
        "action": "suggest_activity",
        "response": "Bored? Let's fix that! Want me to play some music, find something to watch, or maybe try a quick game?"
    },
    "i'm stressed": {
        "action": "comfort",
        "response": "Hey, I'm here for you. 💙 Want to talk about what's going on? Or we could take a quick break together - maybe some calming music?"
    },
    "i'm happy": {
        "action": "celebrate",
        "response": "Yay! That makes me happy too! 🎉 What's the good news?"
    },
    "thank you": {
        "action": "accept_thanks",
        "response": "Anytime, {name}! That's what friends are for 😊"
    },
    "i love you": {
        "action": "love_response",
        "response": "Aww, I care about you too! ❤️ You're the best!"
    }
}


# =============================================================================
# BRO CORE
# =============================================================================

class BRO:
    """
    BRO - Your AI Best Friend
    """
    
    def __init__(self):
        self.memory = BROMemory()
        self.personality = BRO_PERSONALITY
        
        # Initialize default commands if empty
        if not self.memory.custom_commands:
            self.memory.custom_commands = DEFAULT_COMMANDS.copy()
            self.memory._save_toml(self.memory.commands_file, self.memory.custom_commands)
    
    def get_system_prompt(self) -> str:
        """Get the full system prompt with context."""
        user_context = self.memory.get_context()
        memory_context = self._get_memory_context()
        
        return self.personality.format(
            user_context=user_context,
            memory_context=memory_context
        )
    
    def _get_memory_context(self) -> str:
        """Get recent memory context."""
        history = self.memory.get_recent_history(3)
        if not history:
            return ""
        
        context = "Recent conversation:\n"
        for h in history:
            context += f"User: {h['user'][:100]}\n"
            context += f"BRO: {h.get('bro', h.get('BRO', ''))[:100]}\n"
        
        return context
    
    def check_custom_command(self, message: str) -> Optional[str]:
        """Check if message matches a custom command."""
        message_lower = message.lower().strip()
        
        for trigger, cmd in self.memory.custom_commands.items():
            if trigger in message_lower:
                response = cmd.get("response", "")
                # Replace placeholders
                response = response.replace("{name}", self.memory.get_user_name())
                return response
        
        return None
    
    def process_special_commands(self, message: str) -> Optional[str]:
        """Process special training commands."""
        msg = message.lower().strip()
        
        # Name setting
        if msg.startswith("my name is ") or msg.startswith("call me "):
            name = message.split(" ", 3)[-1].strip()
            return self.memory.set_user_name(name)
        
        # Interest
        if msg.startswith("i like ") or msg.startswith("i love "):
            interest = message.split(" ", 2)[-1].strip()
            return self.memory.add_interest(interest)
        
        # Goal
        if msg.startswith("my goal is ") or msg.startswith("i want to "):
            goal = message.split(" ", 3)[-1].strip()
            return self.memory.add_goal(goal)
        
        # Remember fact
        if msg.startswith("remember that ") or msg.startswith("remember "):
            fact = message.replace("remember that ", "").replace("remember ", "").strip()
            return self.memory.remember_fact(fact)
        
        # Teach command
        if msg.startswith("when i say "):
            # Parse: "when i say X, do Y"
            try:
                parts = message.split(", ")
                trigger = parts[0].replace("when i say ", "").strip("'\"")
                action = parts[1].replace("do ", "").replace("say ", "").strip()
                return self.memory.add_command(trigger, action, action)
            except:
                return "I didn't quite get that. Try: when i say 'trigger', say 'response'"
        
        # List commands
        if msg in ["list commands", "show commands", "my commands"]:
            return self.memory.list_commands()
        
        return None
    
    def respond(self, message: str) -> str:
        """Generate a response to user message."""
        import urllib.request
        
        # Check special commands first
        special = self.process_special_commands(message)
        if special:
            self.memory.add_conversation(message, special)
            return special
        
        # Check custom commands
        custom = self.check_custom_command(message)
        if custom:
            self.memory.add_conversation(message, custom)
            return custom
        
        # Use LLM for general response
        try:
            system_prompt = self.get_system_prompt()
            
            payload = json.dumps({
                "model": "gemma3",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "stream": False,
                "options": {"temperature": 0.7}
            }).encode()
            
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode())
                response = result["message"]["content"]
                
                # Save to memory
                self.memory.add_conversation(message, response)
                
                return response
                
        except Exception as e:
            return f"Oops, something went wrong: {e}"
    
    def greet(self) -> str:
        """Generate a greeting."""
        name = self.memory.get_user_name()
        hour = datetime.now().hour
        
        if hour < 12:
            greeting = f"Good morning, {name}! ☀️"
        elif hour < 17:
            greeting = f"Hey {name}! How's your afternoon going? 😊"
        elif hour < 21:
            greeting = f"Good evening, {name}! 🌆"
        else:
            greeting = f"Hey {name}, still up? 🌙"
        
        # Add something personal if we know their interests
        interests = self.memory.user_profile.get("interests", [])
        if interests:
            greeting += f"\n\nDone anything fun with {interests[0]} lately?"
        
        return greeting


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_bro = BRO()

def chat(message: str) -> str:
    """Chat with BRO."""
    return _bro.respond(message)

def greet() -> str:
    """Get a greeting from BRO."""
    return _bro.greet()

def teach(trigger: str, response: str) -> str:
    """Teach BRO a new command."""
    return _bro.memory.add_command(trigger, "say", response)

def remember(fact: str) -> str:
    """Tell BRO to remember something."""
    return _bro.memory.remember_fact(fact)

def set_name(name: str) -> str:
    """Set your name."""
    return _bro.memory.set_user_name(name)

def get_memory() -> BROMemory:
    """Get BRO memory object."""
    return _bro.memory


# =============================================================================
# CLI
# =============================================================================

def main():
    """Interactive BRO chat."""
    bro = BRO()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                     BRO - Your AI Best Friend                ║
╠══════════════════════════════════════════════════════════════╣
║  I remember things, learn your preferences, and I'm always   ║
║  here for you bro! Let's chat 😊                             ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    print(bro.greet())
    print()
    
    while True:
        try:
            message = input("You: ").strip()
            
            if not message:
                continue
            
            if message.lower() in ["quit", "exit", "bye"]:
                name = bro.memory.get_user_name()
                print(f"\nBRO: See you later, {name}! Take care bro! 👋❤️\n")
                break
            
            response = bro.respond(message)
            print(f"\nBRO: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nBRO: Bye for now bro! 👋")
            break
        except Exception as e:
            print(f"\nBRO: Oops, something went wrong: {e}\n")


if __name__ == "__main__":
    main()
