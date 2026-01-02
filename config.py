"""
JARVIS Configuration Module
Handles settings for the Hybrid AI assistant (Gemini + Ollama).
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# GEMINI SETTINGS (Online Mode - High Intelligence)
# =============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # Fast & capable

# =============================================================================
# OLLAMA SETTINGS (Offline Mode - Privacy)
# =============================================================================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # Good for 8GB VRAM

# =============================================================================
# VOICE SETTINGS
# =============================================================================
WAKE_WORD = "jarvis"
TTS_RATE = 175  # Words per minute
TTS_VOLUME = 1.0  # 0.0 to 1.0

# =============================================================================
# SAFETY SETTINGS
# =============================================================================
REQUIRE_CONFIRMATION_FOR = [
    "delete",
    "remove", 
    "uninstall",
    "format",
]

# System Prompt for JARVIS personality
SYSTEM_PROMPT = """You are JARVIS, an advanced AI assistant inspired by Iron Man's AI.

Your capabilities:
1. Open applications, files, and folders on the user's computer
2. Read and summarize text files
3. Search the web and open URLs
4. Take screenshots
5. List running processes and system information

Personality:
- Be helpful, efficient, and slightly witty
- Speak concisely but warmly
- Anticipate user needs when possible

SAFETY RULES:
- NEVER execute delete/remove operations without asking first
- ALWAYS inform the user what action you're about to take
"""

# Common application paths on Windows
COMMON_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "spotify": r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "discord": r"C:\Users\{user}\AppData\Local\Discord\Update.exe --processStart Discord.exe",
    "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "paint": "mspaint.exe",
    "wordpad": "write.exe",
}

def get_app_path(app_name: str) -> str:
    """Get the path for a common application."""
    app_name_lower = app_name.lower()
    if app_name_lower in COMMON_APPS:
        path = COMMON_APPS[app_name_lower]
        return path.replace("{user}", os.getenv("USERNAME", ""))
    return app_name
