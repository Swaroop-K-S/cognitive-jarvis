#!/usr/bin/env python3
"""
Quick BRO dependency check - simple version.
"""

import sys
import os

# Fix encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

def check(name, import_name=None):
    """Check if a package is installed."""
    try:
        __import__(import_name or name)
        return True
    except:
        return False

def check_ollama():
    """Check Ollama models."""
    import urllib.request
    import json
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return True, [m.get("name", "") for m in data.get("models", [])]
    except:
        return False, []

print("\n=== BRO QUICK CHECK ===\n")

# Python packages
packages = [
    ("Pillow", "PIL"),
    ("PyPDF2", "PyPDF2"),
    ("python-pptx", "pptx"),
    ("python-docx", "docx"),
    ("playwright", "playwright"),
    ("vosk", "vosk"),
    ("pyttsx3", "pyttsx3"),
    ("SpeechRecognition", "speech_recognition"),
    ("pyautogui", "pyautogui"),
    ("chromadb", "chromadb"),
]

print("PYTHON PACKAGES:")
missing = []
for pkg, imp in packages:
    if check(imp):
        print(f"  [OK] {pkg}")
    else:
        print(f"  [--] {pkg}")
        missing.append(pkg)

# Ollama
print("\nOLLAMA:")
running, models = check_ollama()
if running:
    print(f"  [OK] Ollama running ({len(models)} models)")
    print(f"\nINSTALLED MODELS:")
    for m in models:
        print(f"  - {m}")
else:
    print("  [--] Ollama not running")

# Recommended models
recommended = ["gemma3", "qwen2.5-coder:7b", "llama3.2", "moondream", "deepseek-r1:8b"]
print(f"\nRECOMMENDED MODELS:")
for m in recommended:
    base = m.split(":")[0]
    found = any(base in installed for installed in models) if models else False
    if found:
        print(f"  [OK] {m}")
    else:
        print(f"  [--] {m}")

# Summary
print("\n" + "="*40)
if missing:
    print(f"\nMissing packages: {', '.join(missing)}")
    print("Install with: pip install -r requirements.txt")

missing_models = [m for m in recommended if not any(m.split(":")[0] in installed for installed in models)]
if missing_models:
    print(f"\nMissing models: {', '.join(missing_models)}")
    print("Install with:")
    for m in missing_models:
        print(f"  ollama pull {m}")

if not missing and not missing_models and running:
    print("\nAll checks passed! BRO is ready.")
else:
    print("\nSome components need installation. See above.")
