
import os
import sys
import time
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_brain_integration():
    print("🧠 Testing BRO UI Brain Integration...")
    
    try:
        from bro_ui import BROApp
        import customtkinter as ctk
        
        # Initialize App
        app = BROApp()
        app.update()
        
        # Wait a bit for background thread to init brain
        print("⏳ Waiting for Brain initialization (background thread)...")
        timeout = 0
        while not hasattr(app, 'brain') or app.brain is None:
            app.update()
            time.sleep(0.1)
            timeout += 0.1
            if timeout > 10:
                print("❌ FAIL: Brain initialization timed out.")
                sys.exit(1)
                
        print("✅ Brain attached to UI.")
        
        # Check components
        if hasattr(app.brain, 'process'):
             print("✅ Brain has process() method.")
        else:
             print("❌ FAIL: Brain missing process method.")
             
        # Check confirmation callback
        if app.brain.confirmation_callback == app.gui_confirmation:
            print("✅ Confirmation callback correctly wired to GUI.")
        else:
            print(f"❌ FAIL: Callback wiring mismatch. Got {app.brain.confirmation_callback}")

        print("🛑 Closing UI...")
        app.destroy()
        print("✅ Brain Integration Test Complete.")
        
    except Exception as e:
        print(f"❌ CRITICAL FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_brain_integration()
