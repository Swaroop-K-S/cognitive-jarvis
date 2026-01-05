
import os
import sys
import time
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ui():
    print("🧪 Testing BRO UI Launch...")
    
    try:
        from bro_ui import BROApp
        import customtkinter as ctk
        
        # Initialize App (this creates the window)
        app = BROApp()
        
        # Force an update to ensure widgets are created
        app.update()
        
        # Check for new pages
        pages = app.pages
        print(f"📂 Pages found: {list(pages.keys())}")
        
        if "vision" in pages and "web" in pages:
            print("✅ PASS: Vision and Web pages created successfully.")
        else:
            print("❌ FAIL: Missing new pages.")
            sys.exit(1)
            
        # Check sidebar buttons
        btns = app.nav_buttons
        if "vision" in btns and "web" in btns:
             print("✅ PASS: Sidebar buttons verified.")
        else:
             print("❌ FAIL: Sidebar buttons missing.")
             sys.exit(1)

        print("🛑 Closing UI...")
        app.destroy()
        print("✅ UI Test Complete.")
        
    except Exception as e:
        print(f"❌ CRITICAL FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_ui()
