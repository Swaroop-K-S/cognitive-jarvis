#!/usr/bin/env python3
"""
JARVIS - Cognitive AI Assistant
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
import tools


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
║        [Cognitive: Think → Decide → Remember → Act]            ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")


def print_status(brain: CognitiveBrain):
    status = brain.get_status()
    
    inet = f"{Colors.GREEN}✓{Colors.ENDC}" if status["internet"] else f"{Colors.YELLOW}✗{Colors.ENDC}"
    gem = f"{Colors.GREEN}✓{Colors.ENDC}" if status["gemini_available"] else f"{Colors.DIM}✗{Colors.ENDC}"
    oll = f"{Colors.GREEN}✓{Colors.ENDC}" if status["ollama_available"] else f"{Colors.DIM}✗{Colors.ENDC}"
    mem = f"{Colors.GREEN}✓ ({status['memory_count']}){Colors.ENDC}" if status["memory_available"] else f"{Colors.DIM}✗{Colors.ENDC}"
    
    print(f"{Colors.BOLD}Status:{Colors.ENDC} Net[{inet}] Gemini[{gem}] Ollama[{oll}] Memory[{mem}]")
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
    
    print(f"{Colors.GREEN}✓ Cognitive JARVIS ready: {mode}{mem_msg}{Colors.ENDC}")
    print(f"{Colors.DIM}Type 'help' for commands{Colors.ENDC}\n")
    
    welcome = "JARVIS online. I can think, remember, and act. How can I help?"
    print(f"{Colors.BLUE}🤖 JARVIS:{Colors.ENDC} {welcome}\n")
    if TTS_AVAILABLE:
        speak(welcome, wait=True)
    
    while True:
        try:
            user_input = input(f"{Colors.CYAN}You:{Colors.ENDC} ").strip()
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
            print(f"\n{Colors.BLUE}🤖 JARVIS {Colors.DIM}{mode_str}{Colors.ENDC}:")
            print(response)
            print()
            
            if TTS_AVAILABLE:
                speak(response[:150], wait=True)
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Type 'quit' to exit{Colors.ENDC}")
        except EOFError:
            break
    
    print(f"\n{Colors.CYAN}Goodbye!{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
