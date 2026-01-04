#!/usr/bin/env python3
"""
BRO - Cognitive AI Assistant
Think → Decide → Remember → Act
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import GEMINI_MODEL
from llm import CognitiveBrain
from llm.model_selector import TaskType, MODELS, get_task_emoji
from cognitive import get_action_emoji
from voice.tts import say, speak, TTS_AVAILABLE
from voice.stt import listen_one_shot
from config import WAKE_WORD_ENABLED
import tools

# Import new capabilities
try:
    from tools.vision import vision_status
    VISION_AVAILABLE = vision_status().get('llava_available', False)
except ImportError:
    VISION_AVAILABLE = False

try:
    from tools.web_automation import browser_status
    PLAYWRIGHT_AVAILABLE = browser_status().get('playwright_available', False)
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from voice.wake_word import create_wake_word_listener
    WAKE_WORD_INSTALLED = True
except ImportError:
    WAKE_WORD_INSTALLED = False


class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_banner():
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗                 ║
║       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝                 ║
║       ██║███████║██████╔╝██║   ██║██║███████╗                 ║
║  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║                 ║
║  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║                 ║
║   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝                 ║
║                                                                ║
║          Just A Rather Very Intelligent System                 ║
║     [Think → Decide → Remember → See → Act → Automate]        ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")


def print_status(brain: CognitiveBrain):
    status = brain.get_status()
    
    inet = f"{Colors.GREEN}✓{Colors.ENDC}" if status["internet"] else f"{Colors.YELLOW}✗{Colors.ENDC}"
    gem = f"{Colors.GREEN}✓{Colors.ENDC}" if status["gemini_available"] else f"{Colors.DIM}✗{Colors.ENDC}"
    oll = f"{Colors.GREEN}✓{Colors.ENDC}" if status["ollama_available"] else f"{Colors.DIM}✗{Colors.ENDC}"
    mem = f"{Colors.GREEN}✓ ({status['memory_count']}){Colors.ENDC}" if status["memory_available"] else f"{Colors.DIM}✗{Colors.ENDC}"
    vis = f"{Colors.GREEN}✓{Colors.ENDC}" if VISION_AVAILABLE else f"{Colors.DIM}✗{Colors.ENDC}"
    web = f"{Colors.GREEN}✓{Colors.ENDC}" if PLAYWRIGHT_AVAILABLE else f"{Colors.DIM}✗{Colors.ENDC}"
    
    print(f"{Colors.BOLD}Core:{Colors.ENDC} Net[{inet}] Gemini[{gem}] Ollama[{oll}] Memory[{mem}]")
    print(f"{Colors.BOLD}Enhanced:{Colors.ENDC} Vision[{vis}] WebAuto[{web}]")
    print()


def print_help():
    print(f"""
{Colors.BOLD}Commands:{Colors.ENDC}
  help     - Show this
  status   - Show system status
  models   - Show specialist models
  memory   - Show memory stats
  forget   - Clear all memory
  clear    - Clear conversation
  quit     - Exit

{Colors.BOLD}Cognitive Actions:{Colors.ENDC}
  💾 REMEMBER: "My name is John"
  🔍 RECALL:   "What's my name?"
  ⚡ ACT:      "Open notepad"
  💻 CODE:    "Write a Python sort function"
  💬 CHAT:    "Tell me a joke"

{Colors.BOLD}New Capabilities:{Colors.ENDC}
  👁️ VISION:  "What's on my screen?" (requires: ollama pull llava)
  🌐 WEB:     "Go to google.com and search for cats"
  📄 CONVERT: "Convert this image to JPEG"
  
{Colors.BOLD}Startup Modes:{Colors.ENDC}
  python main.py --voice       # Voice-first mode
  python main.py --wake-word   # Always-on "Hey BRO" mode
""")


def print_models():
    print(f"\n{Colors.BOLD}Specialist Models:{Colors.ENDC}")
    for task_type, spec in MODELS.items():
        emoji = get_task_emoji(task_type)
        print(f"  {emoji} {task_type.value:<10} → {spec.name} ({spec.vram}GB)")
    print()


def confirmation_prompt(action_name: str, action_args: dict) -> bool:
    print(f"\n{Colors.YELLOW}⚠️ Confirm:{Colors.ENDC} {action_name}")
    return input("Proceed? (y/n): ").strip().lower() in ['y', 'yes']


def main():
    print_banner()
    
    brain = CognitiveBrain()
    brain.set_confirmation_callback(confirmation_prompt)
    
    print_status(brain)
    
    if not brain.is_available():
        print(f"{Colors.RED}❌ No AI available!{Colors.ENDC}")
        print("\nSetup:")
        print("  1. ONLINE: Add GEMINI_API_KEY to .env")
        print("  2. OFFLINE: Install Ollama + ollama pull llama3.2")
        return
    
    status = brain.get_status()
    mode = "Gemini (cloud)" if status["gemini_available"] else "Ollama (local)"
    mem_msg = f", {status['memory_count']} memories" if status["memory_available"] else ""
    
    print(f"{Colors.GREEN}✓ Cognitive BRO ready: {mode}{mem_msg}{Colors.ENDC}")
    print(f"{Colors.DIM}Type 'help' for commands{Colors.ENDC}\n")
    
    welcome = "BRO online. I can think, remember, and act. How can I help?"
    print(f"{Colors.BLUE}🤖 BRO:{Colors.ENDC} {welcome}\n")
    if TTS_AVAILABLE:
        speak(welcome, wait=True)
    
    # Check for startup arguments
    interactive_mode = len(sys.argv) > 1 and sys.argv[1] in ['--interactive', '--voice', '-i']
    wake_word_mode = len(sys.argv) > 1 and sys.argv[1] in ['--wake-word', '--wakeword', '-w']
    
    # WAKE WORD MODE: Always-on "Hey BRO" listening
    wake_listener = None
    if wake_word_mode:
        if WAKE_WORD_INSTALLED:
            print(f"{Colors.MAGENTA}⏰ Wake Word Mode Active - Say 'Hey BRO' to activate!{Colors.ENDC}")
            if TTS_AVAILABLE:
                speak("Wake word mode active. Say Hey BRO when you need me.", wait=True)
            
            # This will be set up below in the main loop
            wake_word_active = True
        else:
            print(f"{Colors.YELLOW}⚠️ Wake word not available. Install vosk: pip install vosk{Colors.ENDC}")
            wake_word_mode = False
    
    if interactive_mode:
        print(f"{Colors.YELLOW}🎤 Voice Mode Active - Speak commands or press ENTER to type!{Colors.ENDC}")
        if TTS_AVAILABLE:
            speak("Voice mode active. Just speak, or press Enter to type.", wait=True)
    
    while True:
        try:
            user_input = ""
            
            if interactive_mode:
                # VOICE-FIRST MODE: Listen for voice, but allow keyboard interrupt
                print(f"{Colors.DIM}(Listening... Press ENTER to type instead){Colors.ENDC}")
                
                # Check for keyboard input using msvcrt (Windows)
                import msvcrt
                import time as time_module
                
                # Give a tiny window to press Enter for typing
                start_wait = time_module.time()
                typed_mode = False
                while time_module.time() - start_wait < 0.5:
                    if msvcrt.kbhit():
                        key = msvcrt.getch()
                        if key == b'\r':  # Enter key
                            typed_mode = True
                            break
                    time_module.sleep(0.05)
                
                if typed_mode:
                    # User wants to type
                    user_input = input(f"{Colors.CYAN}Type command:{Colors.ENDC} ").strip()
                else:
                    # Listen for voice
                    spoken_text = listen_one_shot()
                    if spoken_text:
                        print(f"{Colors.CYAN}You said:{Colors.ENDC} {spoken_text}")
                        user_input = spoken_text
                    else:
                        continue  # No speech detected, loop again
            else:
                # STANDARD MODE: Type or say 'mic'
                mode_prompt = f"{Colors.CYAN}You (type or 'mic'):{Colors.ENDC} "
                user_input = input(mode_prompt).strip()
                
                if not user_input:
                    continue
                
                cmd = user_input.lower()
                
                # Voice Input Command
                if cmd in ['mic', 'listen', 'voice']:
                    print(f"{Colors.YELLOW}🎤 Listening...{Colors.ENDC}")
                    spoken_text = listen_one_shot()
                    if spoken_text:
                        print(f"{Colors.CYAN}You said:{Colors.ENDC} {spoken_text}")
                        user_input = spoken_text
                    else:
                        continue
            
            if not user_input:
                continue
            
            cmd = user_input.lower()
            
            if cmd in ['quit', 'exit', 'bye']:
                say("Goodbye!")
                break
            if cmd == 'help':
                print_help()
                continue
            if cmd == 'status':
                print_status(brain)
                continue
            if cmd == 'models':
                print_models()
                continue
            if cmd == 'memory':
                stats = brain.get_status()
                if stats["memory_available"]:
                    print(f"{Colors.MAGENTA}Memory: {stats['memory_count']} items stored{Colors.ENDC}")
                else:
                    print(f"{Colors.YELLOW}Memory not available{Colors.ENDC}")
                continue
            if cmd == 'forget':
                if brain.memory:
                    brain.memory.clear_all()
                    print(f"{Colors.GREEN}✓ All memories cleared{Colors.ENDC}")
                continue
            if cmd == 'clear':
                brain.clear_history()
                print(f"{Colors.GREEN}✓ Conversation cleared{Colors.ENDC}")
                continue
            
            # COGNITIVE PROCESSING
            print()
            response = brain.process(user_input)
            
            model = brain.get_current_model()
            mode_str = f"[{brain.get_current_mode()}/{model}]" if brain.get_current_mode() == "ollama" else "[gemini]"
            print(f"\n{Colors.BLUE}🤖 BRO {Colors.DIM}{mode_str}{Colors.ENDC}:")
            print(response)
            print()
            
            if TTS_AVAILABLE:
                # Speak the full response (or truncate at 300 chars for very long ones)
                tts_text = response[:300] if len(response) > 300 else response
                speak(tts_text, wait=True)
            
            # In interactive mode, immediately listen for next command
            if interactive_mode:
                print(f"{Colors.DIM}(Listening for next command...){Colors.ENDC}")
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Type 'quit' to exit{Colors.ENDC}")
        except EOFError:
            break
    
    print(f"\n{Colors.CYAN}Goodbye!{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
