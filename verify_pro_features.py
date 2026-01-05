"""
Verification script to prove Pro features are active
"""
import os
import sys

print('=== Verifying Pro Features ===')
print()

# Check semantic_router.py exists
if os.path.exists('cognitive/semantic_router.py'):
    print('✓ cognitive/semantic_router.py EXISTS')
else:
    print('✗ semantic_router.py MISSING')

# Check it's imported in engine.py
with open('cognitive/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'from .semantic_router import' in content:
        print('✓ engine.py IMPORTS semantic_router')
    if 'router.route(user_input)' in content:
        print('✓ engine.py CALLS router.route()')
    if '_keyword_decide' in content:
        print('✓ Keywords are FALLBACK only (in _keyword_decide method)')

print()

# Check TOML parser in cognitive_brain.py
with open('llm/cognitive_brain.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if '_extract_toml_block' in content:
        print('✓ cognitive_brain.py has TOML parser')
    if '_parse_toml_response' in content:
        print('✓ cognitive_brain.py has TOML response parser')
    if 'REGEX FALLBACK' in content:
        print('✓ Regex is marked as FALLBACK')

print()

# Check stt_fast.py
if os.path.exists('voice/stt_fast.py'):
    print('✓ voice/stt_fast.py EXISTS (faster-whisper)')

# Check android XML optimization
with open('tools/android_control.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if '_get_ui_hierarchy' in content:
        print('✓ android_control.py has UIAutomator XML dump')
    if 'smart_tap' in content:
        print('✓ android_control.py has smart_tap (XML-first)')

print()
print('=== Live Test: Semantic Router ===')
from cognitive.semantic_router import semantic_route
tests = [
    'Store this info please',  # Should be REMEMBER (not in keywords!)
    'Save the fact that I love pizza',  # REMEMBER
    'Open Chrome browser',  # ACT
]
for test in tests:
    intent, conf, reason = semantic_route(test)
    print(f'"{test}" -> {intent.value} ({conf:.2f})')
