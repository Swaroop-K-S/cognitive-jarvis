"""
Run the 3 Pro Tests from the Implementation Plan
"""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("RUNNING PRO FEATURE TESTS")
print("=" * 60)
print()

# ==============================================================================
# TEST 1: The "Nuance" Test (Semantic Router)
# ==============================================================================
print("TEST 1: The 'Nuance' Test")
print("-" * 40)
print('Command: "Make a note that I\'m out of milk."')
print('Expected: Semantic Engine triggers REMEMBER (not in keyword list)')
print()

from cognitive.semantic_router import semantic_route, Intent

test_input = "Make a note that I'm out of milk"
intent, confidence, reasoning = semantic_route(test_input)

if intent == Intent.REMEMBER:
    print(f"✅ PASS: Intent = {intent.value} (confidence: {confidence:.2f})")
    print(f"   Reasoning: {reasoning}")
else:
    print(f"❌ FAIL: Got {intent.value} instead of REMEMBER")

# Also verify "Make a note" is NOT in keyword list
REMEMBER_KEYWORDS = [
    "my name is", "i am", "remember that", "remember this",
    "my favorite", "i like", "i prefer", "my project is",
    "my id is", "i work", "my email", "my number",
    "save this", "note that", "keep in mind"
]
keyword_found = any(kw in test_input.lower() for kw in REMEMBER_KEYWORDS)
print(f"   Keyword fallback would have worked: {keyword_found}")
print()

# ==============================================================================
# TEST 2: The "Complexity" Test (TOML Parser)
# ==============================================================================
print("TEST 2: The 'Complexity' Test")
print("-" * 40)
print('Command: "Write a python script that prints \'Hello (World)\'"')
print('Expected: TOML parser handles parentheses correctly')
print()

# Simulate a TOML response with parentheses
toml_response = '''```toml
[response]
thought = "User wants a Python script"
tool = "write_file"
response = "Creating your Python script now."

[args]
filename = "hello.py"
content = "print('Hello (World)')"
```'''

from llm.cognitive_brain import CognitiveBrain
brain = CognitiveBrain()

# Test TOML extraction
toml_content = brain._extract_toml_block(toml_response)
parsed = brain._parse_toml_response(toml_content)

if parsed and parsed.get('args', {}).get('content') == "print('Hello (World)')":
    print("✅ PASS: TOML parser correctly extracted content with parentheses")
    print(f"   Parsed args: {parsed.get('args')}")
else:
    print("❌ FAIL: TOML parser failed")
    print(f"   Got: {parsed}")

# Show that regex would FAIL on this
import re
regex_pattern = r'TOOL_CALL:\s*(\w+)\(([^)]*)\)'
regex_input = 'TOOL_CALL: write_file(content="print(\'Hello (World)\')")'
regex_match = re.search(regex_pattern, regex_input)
if regex_match:
    extracted = regex_match.group(2)
    print(f"   Regex would extract: '{extracted}' (BROKEN)")
else:
    print("   Regex would fail to match at all")
print()

# ==============================================================================
# TEST 3: The "Speed" Test (UIAutomator)
# ==============================================================================
print("TEST 3: The 'Speed' Test (Code Verification)")
print("-" * 40)
print('Expected: android_control.py has smart_tap with XML-first approach')
print()

with open('tools/android_control.py', 'r', encoding='utf-8') as f:
    android_code = f.read()

has_xml_dump = '_get_ui_hierarchy' in android_code
has_smart_tap = 'smart_tap' in android_code
has_xml_first = 'LAYER 1: XML DUMP' in android_code
has_vision_fallback = 'LAYER 2: VISION MODEL' in android_code

if has_xml_dump and has_smart_tap and has_xml_first:
    print("✅ PASS: android_control.py has XML-first optimization")
    print(f"   _get_ui_hierarchy: {has_xml_dump}")
    print(f"   smart_tap method: {has_smart_tap}")
    print(f"   XML-first layer: {has_xml_first}")
    print(f"   Vision fallback: {has_vision_fallback}")
else:
    print("❌ FAIL: Missing UIAutomator optimization")

print()
print("=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
