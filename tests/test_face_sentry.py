from jarvis.vision.face_detect import FaceSentry
import cv2
import numpy as np
import os

print("Testing Face Sentry (OpenCV)...")

try:
    sentry = FaceSentry()
    
    if not sentry.available:
        print("FAILED: Sentry reports unavailable (Haar Cascade load failed?)")
        # Check path
        print(f"Cascade Path: {sentry.cascade_path}")
        print(f"Exists: {os.path.exists(sentry.cascade_path)}")
        exit(1)
        
    print("Sentry initialized.")
    
    # Create a dummy image
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Process (Should return None, 0.0)
    name, conf = sentry.process_frame(dummy_frame)
    print(f"Processed Blank Frame: Name={name}, Conf={conf}")
    
    # Draw a "Fake Face" (White Rectangle) - Haar won't detect this easily, 
    # but we just want to ensure code doesn't crash.
    cv2.rectangle(dummy_frame, (100, 100), (300, 300), (255, 255, 255), -1)
    name, conf = sentry.process_frame(dummy_frame)
    print(f"Processed Fake Frame: Name={name}, Conf={conf}")
    
    print("Face Sentry Interface: OK")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
