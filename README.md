# BRO - Multimodal AI Assistant

**Think → Decide → Remember → See → Act → Automate**

A fully local, offline-capable AI assistant inspired by Iron Man's J.A.R.V.I.S.

## ✨ Features

| Capability | Description | Status |
|:-----------|:------------|:------:|
| 🧠 **Cognitive Loop** | Think before acting | ✅ |
| 💾 **Long-Term Memory** | Remembers facts across sessions | ✅ |
| 🔀 **Smart Routing** | Auto-selects specialist models | ✅ |
| 🌐 **Hybrid Mode** | Gemini (cloud) / Ollama (local) | ✅ |
| 👁️ **Vision** | See and understand your screen | ✅ NEW |
| ⏰ **Wake Word** | "Hey BRO" hands-free activation | ✅ NEW |
| 🌐 **Web Automation** | Control browser, fill forms, click | ✅ NEW |
| 📄 **File Conversion** | Convert images, PDFs, docs | ✅ NEW |
| 🎙️ **Voice I/O** | Talk to BRO, hear responses | ✅ |

## 🚀 Quick Start

```powershell
# 1. Clone and enter directory
cd BRO

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup AI (choose one or both)
# ONLINE: Add GEMINI_API_KEY to .env
# OFFLINE: ollama pull llama3.2

# 4. (Optional) Install vision support
ollama pull llava

# 5. (Optional) Install web automation
playwright install chromium

# 6. Run BRO
python main.py
```

## 🎮 Startup Modes

```powershell
python main.py              # Standard mode (type or say 'mic')
python main.py --voice      # Voice-first mode
python main.py --wake-word  # Always-on "Hey BRO" mode
```

## 💬 Example Commands

### Desktop Control
- "Open Chrome"
- "Close Spotify"
- "Take a screenshot"
- "What processes are running?"

### Vision (requires LLaVA)
- "What's on my screen?"
- "Find the save button"
- "Read the text on screen"
- "Describe this image"

### Web Automation (requires Playwright)
- "Go to google.com and search for Python tutorials"
- "Click the Sign In button"
- "Type my email in the login field"
- "What does this page say?"

### File Conversion
- "Convert this PNG to JPEG"
- "Extract text from document.pdf"
- "Read the slides from presentation.pptx"

### Memory
- "Remember my project is called Alpha"
- "What's my project name?"
- "My favorite color is blue"

## 📋 Text Commands

| Command | Action |
|---------|--------|
| `help` | Show available commands |
| `status` | System status (AI, memory, capabilities) |
| `models` | Show specialist model routing |
| `memory` | Show memory stats |
| `forget` | Clear all memories |
| `clear` | Clear conversation history |
| `mic` | Activate voice input |
| `quit` | Exit BRO |

## 🛠️ Architecture

```
BRO/
├── main.py              # Entry point & CLI
├── config.py            # All settings
├── requirements.txt     # Dependencies
│
├── llm/                 # AI Brains
│   ├── cognitive_brain.py   # Main brain (Gemini + Ollama)
│   ├── hybrid_brain.py      # Fallback hybrid
│   └── model_selector.py    # Smart model routing
│
├── cognitive/           # Thinking Engine
│   └── engine.py        # Think → Decide loop
│
├── memory/              # Long-term Memory
│   └── chromadb store   # Vector database
│
├── voice/               # Voice I/O
│   ├── tts.py           # Text-to-Speech
│   ├── stt.py           # Speech-to-Text
│   ├── wake_word.py     # "Hey BRO" detection (NEW)
│   └── local_tts.py     # Enhanced TTS (NEW)
│
└── tools/               # Actions
    ├── pc_control.py    # Open/close apps, type, keys
    ├── file_ops.py      # File operations
    ├── browser.py       # Basic web browsing
    ├── vision.py        # Screen vision (NEW)
    ├── web_automation.py # Playwright browser control (NEW)
    └── file_convert.py  # File format conversion (NEW)
```

## 🔧 Configuration

Edit `.env` or `config.py`:

```env
# AI
GEMINI_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Vision
VISION_MODEL=llava

# Voice
TTS_RATE=175
TTS_VOLUME=1.0
MIC_DEVICE_INDEX=  # Leave empty for default

# Wake Word
WAKE_WORD_ENABLED=false
```

## 📦 Optional Dependencies

| Feature | Install Command | Size |
|---------|-----------------|------|
| Vision | `ollama pull llava` | ~4GB |
| Web Automation | `playwright install chromium` | ~280MB |
| Wake Word | `pip install vosk` | ~50MB model |
| OCR | Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) | ~30MB |

## 🧪 Test Components

```powershell
# Test vision
python -c "from tools.vision import vision_status; print(vision_status())"

# Test TTS
python voice/local_tts.py

# Test wake word
python voice/wake_word.py
```

## 🎯 Cognitive Actions

| Action | Trigger | Example |
|--------|---------|---------|
| 💾 REMEMBER | "my name is...", "remember that..." | Saves to memory |
| 🔍 RECALL | "what's my...", "do you remember..." | Retrieves from memory |
| ⚡ ACT | "open...", "close...", "run..." | Executes system command |
| 💻 CODE | "write code...", "debug..." | Uses coding specialist |
| 👁️ SEE | "what's on screen...", "find..." | Uses vision model |
| 🌐 WEB | "go to...", "search...", "click..." | Controls browser |
| 📄 CONVERT | "convert...", "extract text..." | File operations |
| 💬 CHAT | Everything else | General conversation |

## 💡 How It Works

```
You: "Open my project folder"

1. 🎤 STT: Transcribes your voice
2. 🧠 THINK: Analyzes intent
3. 🔍 RECALL: Checks memory for "project"
4. ⚡ DECIDE: Action = open_folder
5. 🖱️ ACT: Opens the folder
6. 🔊 TTS: "Opened your Alpha project folder"
```

## 🔒 Privacy

- All processing happens locally when using Ollama
- Memory stored locally in `BRO_memory/`
- No data sent to cloud (unless using Gemini)
- Vision uses local LLaVA model

## 📝 License

MIT License - Feel free to modify and use!

---

**Made with ❤️ inspired by Iron Man's J.A.R.V.I.S.**
