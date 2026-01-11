import eel
import sys
import os
import psutil

# Adjust path to ensure we can import 'jarvis' modules if run directly
current_dir = os.path.dirname(os.path.abspath(__file__)) # jarvis/jarvis
parent_dir = os.path.dirname(current_dir) # jarvis
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from jarvis.llm.cognitive_brain import CognitiveBrain
except ImportError:
    # Fallback if running from proper package context isn't working as expected
    print("Warning: Direct import failed, attempting relative import fix...")
    from llm.cognitive_brain import CognitiveBrain

# Initialize the Brain
print("Initializing Cognitive Brain...")
brain = CognitiveBrain()

# Initialize Eel (point to the 'web' folder)
web_dir = os.path.join(current_dir, 'web')
eel.init(web_dir)

# --- EXPOSE PYTHON FUNCTIONS TO JAVASCRIPT ---

@eel.expose
def process_user_input(text):
    """Called from JS when user types or speaks."""
    print(f"User Input: {text}")
    
    # 1. Ask Brain
    try:
        # State handled by JS, but we can enforce if needed
        response = brain.process(text)
    except Exception as e:
        print(f"Brain Error: {e}")
        response = f"**System Error**: {str(e)}"
    
    # 2. Send Response back to JS
    eel.display_jarvis_response(response)
    print(f"Brain Response: {response}")
    return response

@eel.expose
def get_status():
    """Returns real system stats to UI."""
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        return {"cpu": cpu, "ram": ram}
    except Exception:
        return {"cpu": 0, "ram": 0}

@eel.expose
def listen_voice():
    """Called from JS to trigger backend voice recording."""
    print("🎤 Starting Voice Listener...")
    try:
        from jarvis.tools.voice_input import listen_and_transcribe
        text, err = listen_and_transcribe()
        if text:
            return text
        if err:
            return f"Error: {err}"
    except ImportError:
        return "Error: Voice module not found."
    return ""

@eel.expose
def activate_sentinel_mode():
    """Called from JS to open Camera Sentry."""
    print("👁️ Activating Sentinel Mode...")
    try:
        from jarvis.vision.face_detect import start_sentry_mode
        result = start_sentry_mode(duration=15)
        return result
    except ImportError:
        return "Error: Vision module not found."
    return ""

# --- START THE APP ---
def start_ui():
    print("🚀 Starting BRO GLASS-HUD Interface (Advanced Mode)...")
    try:
        # Start in a new chrome-like window (app mode)
        # size=(width, height)
        eel.start('index.html', size=(1280, 800), mode='chrome', cmdline_args=['--start-maximized']) 
    except EnvironmentError:
        # Fallback to default browser if Chrome is missing/fails
        print("Chrome not found or error, falling back to default browser...")
        eel.start('index.html', size=(1280, 800), mode='default')


if __name__ == "__main__":
    start_ui()
