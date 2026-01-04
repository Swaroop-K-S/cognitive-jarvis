# BRO Call Sentry - LOCAL Edition

## 100% Offline Call Screening

No Twilio, no cloud, no internet required!

### How It Works

```
Phone (Speaker) → PC Microphone → Vosk (Local STT) → Ollama (Local AI) → PC Speaker
```

1. Put phone on speaker
2. BRO listens via your PC mic (Vosk - fully offline)
3. AI thinks using Ollama (gemma3 - local)
4. Speaks via PC speakers (pyttsx3 - offline)

### Quick Start

```powershell
cd "c:\Users\swaro\Code\New folder (3)\BRO"

# See available modes
python call_sentry/local_sentry.py modes

# Start call sentry (professional mode)
python call_sentry/local_sentry.py start

# Start in friendly mode
python call_sentry/local_sentry.py start --mode friendly

# View call summaries
python call_sentry/local_sentry.py summary
```

### Usage

1. Run `python call_sentry/local_sentry.py start`
2. When a call comes in, put phone on speaker near PC mic
3. Press ENTER to tell BRO the call has started
4. BRO greets and handles the conversation
5. Press Ctrl+C when call ends
6. Summary is saved automatically

### Modes

| Mode | Greeting | Use For |
|:-----|:---------|:--------|
| **professional** | "Hello, thank you for calling..." | Work, business |
| **friendly** | "Yo, what's up?" | Friends, family |
| **guard** | "This call is being screened..." | Unknown callers |

### Requirements (All Local!)

- ✅ Vosk (installed)
- ✅ pyttsx3 (installed)
- ✅ Ollama with gemma3 (installed)
- ✅ PyAudio (installed)

No internet needed once models are downloaded!
