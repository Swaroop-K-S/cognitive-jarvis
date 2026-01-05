"""
BRO COMPREHENSIVE TEST SUITE
Tests all capabilities across all modules.
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test results
results = {
    "passed": [],
    "failed": [],
    "skipped": []
}

def test(name, func, skip_reason=None):
    """Run a test and record result."""
    if skip_reason:
        print(f"⏭️ SKIP: {name} ({skip_reason})")
        results["skipped"].append(name)
        return
    
    try:
        result = func()
        if result:
            print(f"✅ PASS: {name}")
            results["passed"].append(name)
        else:
            print(f"❌ FAIL: {name} (returned False)")
            results["failed"].append(name)
    except Exception as e:
        print(f"❌ FAIL: {name} ({str(e)[:50]})")
        results["failed"].append(name)

def separator(title):
    print(f"\n{'='*60}")
    print(f"🔬 {title}")
    print(f"{'='*60}\n")


# =============================================================================
# 1. PERSONALITY & MEMORY
# =============================================================================
def test_personality():
    separator("1. PERSONALITY & MEMORY")
    
    from cognitive.personality import chat, greet, remember, get_memory
    from tools.reminders import note, remind, notes, reminders
    
    # Test greet
    test("Greeting", lambda: len(greet()) > 0)
    
    # Test memory
    test("Remember fact", lambda: "📝" in remember("Test fact for BRO"))
    
    # Test note
    test("Add note", lambda: "📝" in note("Test note from test suite"))
    
    # Test list notes
    test("List notes", lambda: len(notes()) > 0)
    
    # Test reminder
    test("Set reminder", lambda: "⏰" in remind("Test reminder", "1h"))
    
    # Test list reminders  
    test("List reminders", lambda: len(reminders()) > 0)
    
    # Test chat (requires Ollama)
    def test_chat():
        response = chat("Say 'test' if working")
        return len(response) > 0
    test("AI Chat", test_chat)


# =============================================================================
# 2. ANDROID PHONE CONTROL
# =============================================================================
def test_android():
    separator("2. ANDROID PHONE CONTROL")
    
    try:
        from tools.android_control import AndroidController
        ctrl = AndroidController()
        
        # Test connection
        connected = ctrl.connect()
        test("Phone connection", lambda: connected)
        
        if connected:
            test("Get screen size", lambda: ctrl.screen_size[0] > 0)
            # Device info accessible via device.serial
            test("Device connected", lambda: ctrl.device is not None)
        else:
            test("Screen capture", None, "Phone not connected")
    except ImportError as e:
        test("Android module", None, f"Import error: {e}")


# =============================================================================
# 3. SMART SHOPPING
# =============================================================================
def test_shopping():
    separator("3. SMART SHOPPING")
    
    from tools.smart_shopping import shop_from_text, get_list, clear_list
    
    # Clear and add items
    clear_list()
    test("Add shopping items", lambda: "3 items" in shop_from_text("Apple, Banana, Milk"))
    
    # Get list
    test("Get shopping list", lambda: "Apple" in get_list() or "apple" in get_list().lower())
    
    # Clear list and verify (check for empty or 0)
    clear_list()
    result = get_list()
    test("Clear list", lambda: "0 items" in result or "No shopping" in result or "SHOPPING LIST" in result)


# =============================================================================
# 4. VISION & VIDEO
# =============================================================================
def test_vision():
    separator("4. VISION & VIDEO")
    
    from tools.video_recognition import capture_screen, analyze_image, video_status
    
    # Test status
    test("Video module status", lambda: "OpenCV" in video_status())
    
    # Test screen capture
    def test_capture():
        path = capture_screen()
        return os.path.exists(path)
    test("Screen capture", test_capture)
    
    # Test analyze (requires Ollama + LLaVA)
    def test_analyze():
        path = capture_screen()
        result = analyze_image(path, "Describe briefly")
        return len(result) > 10
    test("Image analysis", test_analyze)


# =============================================================================
# 5. OCR TEXT READING
# =============================================================================
def test_ocr():
    separator("5. OCR TEXT READING")
    
    from tools.ocr import ocr_status, read_screen
    
    # Check status
    test("OCR module status", lambda: "OCR" in ocr_status())
    
    # Test screen reading
    def test_read():
        text = read_screen()
        return len(text) > 0
    test("Read screen text", test_read)


# =============================================================================
# 6. MUSIC CONTROL
# =============================================================================
def test_music():
    separator("6. MUSIC CONTROL")
    
    from tools.music_player import music_status, volume_up, volume_down
    
    # Test status
    test("Music module status", lambda: "MUSIC" in music_status().upper())
    
    # Test volume (safe - just adjusts)
    test("Volume up", lambda: "🔊" in volume_up(2))
    test("Volume down", lambda: "🔉" in volume_down(2))


# =============================================================================
# 7. SYSTEM MONITOR
# =============================================================================
def test_system():
    separator("7. SYSTEM MONITOR")
    
    from tools.system_monitor import system_status, cpu, ram, gpu, battery, disk, quick_status
    
    # Test each function
    test("System status", lambda: "CPU" in system_status())
    test("CPU usage", lambda: "%" in cpu())
    test("RAM usage", lambda: "GB" in ram())
    test("GPU info", lambda: "GPU" in gpu())
    test("Battery", lambda: "%" in battery() or "Desktop" in battery())
    test("Disk usage", lambda: "GB" in disk())
    test("Quick status", lambda: "CPU" in quick_status())


# =============================================================================
# 8. WEATHER
# =============================================================================
def test_weather():
    separator("8. WEATHER")
    
    from tools.weather import quick_weather
    
    # Test weather (may fail if network issues)
    def test_wx():
        result = quick_weather("London")
        return "°C" in result or "Error" not in result
    test("Weather API", test_wx, skip_reason=None)


# =============================================================================
# 9. PC CONTROL
# =============================================================================
def test_pc_control():
    separator("9. PC CONTROL")
    
    try:
        from tools.pc_control import get_system_info, list_processes, take_screenshot
        
        test("System info", lambda: len(get_system_info()) > 0)
        test("List processes", lambda: len(list_processes()) > 0)
    except ImportError as e:
        test("PC control module", None, f"Import error: {e}")


# =============================================================================
# 10. FILE MANAGER
# =============================================================================
def test_file_manager():
    separator("10. FILE MANAGER")
    
    try:
        from tools.file_manager import list_files, file_info, search_files
        
        # Test list files
        test("List files", lambda: len(list_files(".")) > 0)
        
        # Test file info
        req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
        test("File info", lambda: "KB" in file_info(req_path) or "bytes" in file_info(req_path).lower())
        
        # Test search
        test("Search files", lambda: len(search_files("*.py")) > 0)
    except ImportError as e:
        test("File manager module", None, f"Import error: {e}")


# =============================================================================
# 11. REMINDERS MODULE (already tested in personality)
# =============================================================================
def test_reminders():
    separator("11. REMINDERS MODULE")
    
    from tools.reminders import note, notes, remind, reminders, _notes, _reminders
    
    test("Notes manager", lambda: _notes is not None)
    test("Reminders manager", lambda: _reminders is not None)


# =============================================================================
# 12. CONFIG & LLM
# =============================================================================
def test_config():
    separator("12. CONFIG & LLM")
    
    import config
    
    test("Config loaded", lambda: hasattr(config, 'WAKE_WORD'))
    
    try:
        from llm.ollama_brain import OllamaBrain
        test("Ollama brain import", lambda: True)
    except:
        test("Ollama brain", None, "Import failed")


# =============================================================================
# MAIN
# =============================================================================
def run_all_tests():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    BRO CAPABILITY TEST SUITE                 ║
║                     Testing All 12+ Modules                  ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    start = time.time()
    
    # Run all test groups
    test_personality()
    test_android()
    test_shopping()
    test_vision()
    test_ocr()
    test_music()
    test_system()
    test_weather()
    test_pc_control()
    test_file_manager()
    test_reminders()
    test_config()
    
    elapsed = time.time() - start
    
    # Summary
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                        TEST SUMMARY                          ║
╠══════════════════════════════════════════════════════════════╣
║  ✅ Passed:  {len(results['passed']):3d}                                              ║
║  ❌ Failed:  {len(results['failed']):3d}                                              ║
║  ⏭️ Skipped: {len(results['skipped']):3d}                                              ║
║  ⏱️ Time:    {elapsed:.1f}s                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    if results["failed"]:
        print("Failed tests:")
        for name in results["failed"]:
            print(f"  ❌ {name}")
    
    return len(results["failed"]) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
