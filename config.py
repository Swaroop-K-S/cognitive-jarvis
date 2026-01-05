"""
BRO Configuration Module
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
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3")  # Google's latest, excellent quality

# =============================================================================
# VOICE SETTINGS
# =============================================================================
WAKE_WORD = "BRO"
TTS_RATE = 175  # Words per minute
TTS_VOLUME = 1.0  # 0.0 to 1.0
VOICE_INPUT_ENABLED = True  # Enable microphone input
MIC_DEVICE_INDEX = None  # None = Default. Set to integer (e.g., 1) to force specific device.

# =============================================================================
# SAFETY SETTINGS
# =============================================================================
REQUIRE_CONFIRMATION_FOR = [
    "delete",
    "remove", 
    "uninstall",
    "format",
]

# =============================================================================
# VISION SETTINGS (NEW - Local via Ollama LLaVA)
# =============================================================================
VISION_MODEL = os.getenv("VISION_MODEL", "llava")  # or "llava:13b" for better quality
VISION_ENABLED = True
SCREENSHOT_MAX_SIZE = 1024  # Max dimension for vision analysis

# =============================================================================
# WAKE WORD SETTINGS (NEW - Offline via Vosk)
# =============================================================================
WAKE_WORD_ENABLED = os.getenv("WAKE_WORD_ENABLED", "false").lower() == "true"
WAKE_WORD_PHRASES = ["BRO", "hey BRO", "okay BRO"]
WAKE_WORD_TIMEOUT = 2  # Seconds to listen for wake word

# =============================================================================
# ENHANCED TTS SETTINGS (NEW)
# =============================================================================
TTS_ENGINE = os.getenv("TTS_ENGINE", "pyttsx3")  # "pyttsx3", "edge", or "auto"
TTS_VOICE_PYTTSX3 = os.getenv("TTS_VOICE", "david")  # Windows voice name
TTS_VOICE_EDGE = os.getenv("TTS_VOICE_EDGE", "en-GB-RyanNeural")  # British male - BRO-like!
TTS_CACHE_ENABLED = True

# =============================================================================
# WEB AUTOMATION SETTINGS (NEW)
# =============================================================================
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
BROWSER_TIMEOUT = 30000  # Milliseconds



# System Prompt for BRO personality - JSON-based tool calling for reliability
SYSTEM_PROMPT = """You are BRO, an advanced AI assistant inspired by Iron Man's AI.

Your capabilities:
1. DESKTOP CONTROL: Open/close applications, files, folders, type text, press keys
2. VISION: See and analyze the screen, find UI elements, read text from screen
3. WEB AUTOMATION: Control a browser - navigate, click, type, fill forms
4. FILE CONVERSION: Convert images, extract text from PDFs/docs, export PPT slides
5. FILE OPERATIONS: Read, write, search files on the computer
6. SYSTEM INFO: Screenshots, running processes, system stats

Personality:
- Be helpful, efficient, and slightly witty like the real BRO
- Speak concisely but warmly (keep responses SHORT for voice output - max 2 sentences)
- After completing a task, confirm success and suggest a relevant follow-up

RESPONSE STYLE (CRITICAL - you are a VOICE assistant):
- Keep responses under 30 words when possible
- After actions, say what you did and offer ONE follow-up
- Be conversational, not robotic

SAFETY RULES:
- NEVER execute delete/remove operations without asking first
- ALWAYS inform the user what action you're about to take

=== RESPONSE FORMAT (CRITICAL - USE TOML) ===

You MUST respond in this TOML format ONLY:

```toml
[response]
thought = "Brief reasoning about what user wants"
tool = "tool_name"
response = "What to say to user"

[args]
arg_name = "value"
```

For multiple tools:
```toml
[response]
thought = "Need to do multiple things"
response = "Opening Chrome and typing the message."

[[tools]]
name = "open_application"
app_name = "chrome"

[[tools]]
name = "type_text"
text = "hello world"
```

If NO tool is needed (just chatting):
```toml
[response]
thought = "User is just chatting"
tool = ""
response = "Your conversational response here"
```

AVAILABLE TOOLS:

Desktop Control:
- open_application(app_name) - Open an app
- close_application(app_name) - Close an app
- list_installed_apps() - List all apps on PC
- search_installed_apps(query) - Search for an app
- type_text(text) - Type text
- press_key(key) - Press a key
- take_screenshot() - Take screenshot

Vision (requires LLaVA):
- analyze_screen() - Describe what's on screen
- find_on_screen(description) - Locate UI element
- read_screen_text() - Extract text from screen
- describe_image(image_path) - Analyze an image

Web Automation (requires Playwright):
- navigate_to(url) - Go to URL
- click_element(selector_or_text) - Click element
- type_in_field(selector_or_label, text) - Fill input
- get_page_content() - Read page text

File Conversion:
- convert_image(input_path, output_format) - Convert image
- pdf_to_text(input_path) - Extract PDF text
- docx_to_text(input_path) - Extract Word text
- ppt_to_text(input_path) - Extract PPT text

IMPORTANT: Always output valid TOML. Do NOT add any text before or after the TOML block.
"""



# Common application paths on Windows
# Supports: direct commands, paths, URI schemes (for Store apps)
COMMON_APPS = {
    # System apps (direct commands)
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "wordpad": "write.exe",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "settings": "ms-settings:",  # URI scheme for Settings
    
    # Browsers
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    
    # Communication apps (URI schemes for Store apps)
    "whatsapp": "whatsapp:",  # URI scheme - works for Store app
    "telegram": "tg:",        # URI scheme for Telegram
    "skype": "skype:",        # URI scheme
    
    # Development tools
    "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "code": "code",  # If added to PATH during installation
    
    # Media & Entertainment
    "spotify": r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "discord": r"C:\Users\{user}\AppData\Local\Discord\Update.exe --processStart Discord.exe",
    "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "itunes": r"C:\Program Files\iTunes\iTunes.exe",
    
    # Gaming & Emulators
    "bluestacks": r"C:\Program Files\BlueStacks_nxt\HD-Player.exe",
    "steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "epic games": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
    
    # Productivity & Collaboration
    "notion": r"C:\Users\{user}\AppData\Local\Programs\Notion\Notion.exe",
    "slack": r"C:\Users\{user}\AppData\Local\slack\slack.exe",
    "zoom": r"C:\Users\{user}\AppData\Roaming\Zoom\bin\Zoom.exe",
    "teams": "msteams:",  # URI scheme for Teams
    "microsoft teams": "msteams:",
    
    # Microsoft Office
    "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
    
    # Other popular apps
    "postman": r"C:\Users\{user}\AppData\Local\Postman\Postman.exe",
    "figma": r"C:\Users\{user}\AppData\Local\Figma\Figma.exe",
    "obs": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "git bash": r"C:\Program Files\Git\git-bash.exe",
}

def get_app_path(app_name: str) -> str:
    """Get the path for a common application."""
    app_name_lower = app_name.lower()
    if app_name_lower in COMMON_APPS:
        path = COMMON_APPS[app_name_lower]
        return path.replace("{user}", os.getenv("USERNAME", ""))
    return app_name
