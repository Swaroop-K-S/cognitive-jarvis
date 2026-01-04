#!/usr/bin/env python3
"""
BRO System Diagnostic & Test Script
Checks all components and dependencies.
"""

import sys
import os
import subprocess
import urllib.request
import json
from typing import Tuple, Dict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Colors for terminal output
class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

def ok(msg): print(f"{C.GREEN}[OK]{C.END} {msg}")
def warn(msg): print(f"{C.YELLOW}[!!]{C.END} {msg}")
def fail(msg): print(f"{C.RED}[X]{C.END} {msg}")
def info(msg): print(f"{C.CYAN}[i]{C.END} {msg}")
def header(msg): print(f"\n{C.BOLD}{C.CYAN}{'='*60}\n{msg}\n{'='*60}{C.END}")


def check_python_version() -> bool:
    """Check Python version >= 3.9"""
    version = sys.version_info
    if version >= (3, 9):
        ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        fail(f"Python {version.major}.{version.minor} (need 3.9+)")
        return False


def check_package(name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a package is installed."""
    import_name = import_name or name
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, None


def check_core_packages() -> Dict[str, bool]:
    """Check core Python packages."""
    packages = {
        # Core AI
        "google-generativeai": ("google.generativeai", "Gemini API"),
        "chromadb": ("chromadb", "Memory storage"),
        "sentence-transformers": ("sentence_transformers", "Embeddings"),
        
        # PC Control
        "pyautogui": ("pyautogui", "Desktop automation"),
        "psutil": ("psutil", "Process control"),
        
        # Voice
        "pyttsx3": ("pyttsx3", "Text-to-speech"),
        "SpeechRecognition": ("speech_recognition", "Speech-to-text"),
        "pyaudio": ("pyaudio", "Audio input"),
        
        # Vision
        "Pillow": ("PIL", "Image processing"),
        
        # Web Automation
        "playwright": ("playwright", "Browser automation"),
        
        # File Conversion
        "PyPDF2": ("PyPDF2", "PDF handling"),
        "python-pptx": ("pptx", "PowerPoint"),
        "python-docx": ("docx", "Word docs"),
        
        # Wake Word
        "vosk": ("vosk", "Offline speech"),
        
        # Utilities
        "python-dotenv": ("dotenv", "Environment vars"),
        "colorama": ("colorama", "Terminal colors"),
    }
    
    results = {}
    for pkg, (import_name, desc) in packages.items():
        installed, version = check_package(pkg, import_name)
        results[pkg] = installed
        if installed:
            ok(f"{pkg} ({version}) - {desc}")
        else:
            warn(f"{pkg} - {desc} [NOT INSTALLED]")
    
    return results


def check_ollama() -> Tuple[bool, list]:
    """Check if Ollama is running and list models."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]
            return True, models
    except Exception as e:
        return False, []


def check_ollama_models(installed_models: list) -> Dict[str, bool]:
    """Check for recommended models."""
    recommended = [
        ("gemma2:9b", "General conversation"),
        ("qwen2.5-coder:7b", "Coding"),
        ("qwen2.5:7b", "General + reasoning"),
        ("llava", "Vision/screen"),
        ("deepseek-r1:8b", "Math/logic"),
    ]
    
    # Normalize model names (remove tags for comparison)
    installed_base = [m.split(":")[0] for m in installed_models]
    
    results = {}
    for model, desc in recommended:
        base_name = model.split(":")[0]
        # Check if any version of this model is installed
        found = any(base_name == m.split(":")[0] for m in installed_models)
        results[model] = found
        if found:
            # Find the exact installed version
            exact = next((m for m in installed_models if m.startswith(base_name)), model)
            ok(f"{exact} - {desc}")
        else:
            warn(f"{model} - {desc} [NOT INSTALLED]")
    
    return results


def check_playwright_browsers() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        # Check for chromium
        result = subprocess.run(
            ["playwright", "install", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if "chromium" in result.stdout.lower() or result.returncode == 0:
            return True
        return False
    except Exception:
        return False


def check_gemini_api() -> bool:
    """Check if Gemini API key is configured."""
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY", "")
    return len(api_key) > 10


def run_import_tests() -> Dict[str, bool]:
    """Test importing BRO modules."""
    tests = {
        "tools.vision": "Vision system",
        "tools.web_automation": "Web automation",
        "tools.file_convert": "File conversion",
        "voice.wake_word": "Wake word detection",
        "voice.local_tts": "Enhanced TTS",
        "llm.cognitive_brain": "Cognitive brain",
        "cognitive.engine": "Cognitive engine",
        "memory": "Memory system",
    }
    
    results = {}
    for module, desc in tests.items():
        try:
            __import__(module)
            ok(f"{module} - {desc}")
            results[module] = True
        except Exception as e:
            fail(f"{module} - {desc}: {str(e)[:50]}")
            results[module] = False
    
    return results


def print_summary(results: dict):
    """Print summary and recommendations."""
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{C.BOLD}Summary: {passed}/{total} checks passed{C.END}")
    
    if passed < total:
        print(f"\n{C.YELLOW}Recommendations:{C.END}")
        
        if not results.get("ollama"):
            print("  • Install Ollama: https://ollama.ai")
        
        missing_pkgs = [k for k, v in results.items() if not v and not k.startswith("model:")]
        if missing_pkgs:
            print(f"  • Install missing packages:")
            print(f"    pip install {' '.join(missing_pkgs)}")
        
        if results.get("playwright") and not results.get("playwright_browsers"):
            print("  • Install Playwright browsers:")
            print("    playwright install chromium")
        
        missing_models = [k.replace("model:", "") for k, v in results.items() if k.startswith("model:") and not v]
        if missing_models:
            print("  * Install recommended Ollama models:")
            for model in missing_models:
                print(f"    ollama pull {model}")


def main():
    print(f"""
{C.CYAN}+==============================================================+
|              BRO SYSTEM DIAGNOSTIC                        |
+==============================================================+{C.END}
""")
    
    all_results = {}
    
    # 1. Python Version
    header("1. Python Environment")
    all_results["python"] = check_python_version()
    
    # 2. Core Packages
    header("2. Python Packages")
    pkg_results = check_core_packages()
    all_results.update(pkg_results)
    
    # 3. Ollama
    header("3. Ollama LLM Server")
    ollama_running, models = check_ollama()
    if ollama_running:
        ok(f"Ollama is running ({len(models)} models installed)")
        all_results["ollama"] = True
        
        # Check models
        print(f"\n{C.BOLD}Installed Models:{C.END}")
        for model in models:
            info(model)
        
        print(f"\n{C.BOLD}Recommended Models:{C.END}")
        model_results = check_ollama_models(models)
        for model, installed in model_results.items():
            all_results[f"model:{model}"] = installed
    else:
        fail("Ollama not running (start with: ollama serve)")
        all_results["ollama"] = False
    
    # 4. Playwright Browsers
    header("4. Browser Automation")
    if pkg_results.get("playwright"):
        try:
            from playwright.sync_api import sync_playwright
            ok("Playwright installed")
            all_results["playwright_browsers"] = True
            info("Run 'playwright install chromium' if browsers not installed")
        except:
            warn("Playwright browsers may need installation")
            all_results["playwright_browsers"] = False
    else:
        warn("Playwright not installed - web automation unavailable")
        all_results["playwright_browsers"] = False
    
    # 5. Gemini API
    header("5. Gemini API (Cloud)")
    try:
        if check_gemini_api():
            ok("GEMINI_API_KEY configured in .env")
            all_results["gemini_api"] = True
        else:
            warn("GEMINI_API_KEY not set (optional - Ollama works offline)")
            all_results["gemini_api"] = False
    except:
        warn("Could not check Gemini API (dotenv not installed)")
        all_results["gemini_api"] = False
    
    # 6. BRO Module Imports
    header("6. BRO Module Tests")
    # Add BRO to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import_results = run_import_tests()
    all_results.update({f"import:{k}": v for k, v in import_results.items()})
    
    # 7. Summary
    header("7. Summary & Recommendations")
    print_summary(all_results)
    
    # Quick start commands
    print(f"\n{C.BOLD}{C.GREEN}Quick Fix Commands:{C.END}")
    print(f"""
# Install missing Python packages:
pip install -r requirements.txt

# Install Playwright browser:
playwright install chromium

# Install recommended Ollama models:
ollama pull gemma2:9b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5:7b
ollama pull llava
ollama pull deepseek-r1:8b
""")
    
    return 0 if all(v for v in all_results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
