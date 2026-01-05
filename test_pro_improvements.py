"""
Test script for Pro-Level Improvements
"""
import sys
sys.path.insert(0, '.')

print('=== Testing Pro-Level Improvements ===')
print()

# Test 1: Semantic Router
print('1. Testing Semantic Router...')
try:
    from cognitive.semantic_router import semantic_route, Intent
    result = semantic_route('store the fact that I like pizza')
    print(f'   Input: "store the fact that I like pizza"')
    print(f'   Intent: {result[0].value}, Confidence: {result[1]:.2f}')
    print('   ✓ Semantic Router working!')
except Exception as e:
    print(f'   ✗ Error: {e}')

print()

# Test 2: TOML Parser
print('2. Testing TOML Parser...')
try:
    from llm.cognitive_brain import CognitiveBrain
    brain = CognitiveBrain()
    test_toml = '''[response]
thought = "User wants chrome"
tool = "open_application"
response = "Opening Chrome now."

[args]
app_name = "chrome"'''
    parsed = brain._parse_toml_response(test_toml)
    print(f'   Parsed tool: {parsed.get("response", {}).get("tool")}')
    print(f'   Parsed args: {parsed.get("args")}')
    print('   ✓ TOML Parser working!')
except Exception as e:
    print(f'   ✗ Error: {e}')

print()

# Test 3: Faster Whisper
print('3. Testing Faster-Whisper...')
try:
    from voice.stt_fast import WHISPER_AVAILABLE, WhisperSTT
    print(f'   Whisper available: {WHISPER_AVAILABLE}')
    if WHISPER_AVAILABLE:
        print('   ✓ Faster-Whisper ready!')
    else:
        print('   ⚠ Module found but whisper not loaded')
except Exception as e:
    print(f'   ✗ Error: {e}')

print()

# Test 4: App Discovery
print('4. Testing App Discovery...')
try:
    from tools.pc_control import discover_installed_apps
    apps = discover_installed_apps()
    print(f'   Discovered {len(apps)} apps on PC')
    sample = list(apps.keys())[:5]
    print(f'   Sample: {sample}')
    print('   ✓ App Discovery working!')
except Exception as e:
    print(f'   ✗ Error: {e}')

print()
print('=== All Tests Complete ===')
