# JARVIS - Cognitive AI Assistant

**Think → Decide → Remember → Act**

JARVIS with long-term memory and intelligent task routing.

## Features

- 🧠 **Cognitive Loop**: Think before acting
- 💾 **Memory**: Remembers facts across sessions
- 🔀 **Smart Routing**: Auto-selects specialist models
- 🌐 **Hybrid**: Gemini (online) / Ollama (offline)

## Cognitive Actions

| Action | Example | What Happens |
|--------|---------|--------------|
| 💾 REMEMBER | "My name is John" | Saves to memory |
| 🔍 RECALL | "What's my name?" | Retrieves from memory |
| ⚡ ACT | "Open notepad" | Executes system command |
| 💻 CODE | "Write a sort function" | Uses coding specialist |
| 💬 CHAT | "Tell me a joke" | General conversation |

## Quick Start

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup AI (choose one or both)
# ONLINE: Add GEMINI_API_KEY to .env
# OFFLINE: ollama pull llama3.2

# 3. Run
python main.py
```

## Commands

```
help    - Show commands
status  - System status
memory  - Memory stats
forget  - Clear all memory
models  - Show specialists
quit    - Exit
```

## How Memory Works

```
You: "My project is called Alpha"
JARVIS: 💾 REMEMBER → Saved!

... 3 days later ...

You: "Open the folder for my project"
JARVIS: 🔍 Recalls "Alpha" → Opens folder
```

Memory persists in `jarvis_memory/` folder.
