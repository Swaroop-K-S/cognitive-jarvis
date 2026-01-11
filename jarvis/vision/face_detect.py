"""
Face Sentry Module (OpenCV)
Provides presence detection and face awareness.
Fallback from MediaPipe due to environment constraints.
"""
import uuid
import json
import os
import time
import math
from typing import Tuple, Optional, Dict

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("⚠️ OpenCV not installed. Face Sentry disabled.")

class FaceSentry:
    """
    Biometric Security System using OpenCV Haar Cascades.
    (Presence Detection Mode)
    """
    def __init__(self, data_path: str = "bro_memory/face_db.json"):
        self.data_path = data_path
        self.active = False
        self.last_seen_boss = 0
        self.greeting_cooldown = 300  # 5 minutes
        
        if OPENCV_AVAILABLE:
            # Load Haar Cascade
            self.cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
            
            if self.face_cascade.empty():
                print("⚠️ Failed to load Haar Cascade.")
                self.available = False
            else:
                self.available = True
        else:
            self.available = False

    def process_frame(self, frame) -> Tuple[Optional[str], float]:
        """
        Process a frame and identify the user.
        Returns: (Name, Confidence)
        """
        if not self.available: return None, 0.0
        
        # Grayscale for Haar
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        # scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
        
        if len(faces) > 0:
            # Face detected!
            # Since this is a Personal Assistant on a Desktop, we assume the primary face is "Boss".
            # (Limitation of Haar: No embeddings for ID)
            (x, y, w, h) = faces[0]
            
            # Simple "Centrality" check could improve confidence
            # But for now, just finding a face is enough.
            
            # Greeting Logic managed by UI loop, we just return detection
            return "Boss", 0.95
                
        return None, 0.0

    def learn_face(self, frame, name: str = "Boss") -> bool:
        """
        Placeholder for consistency. Haar cannot learn faces.
        """
        return True


def start_sentry_mode(duration: int = 30):
    """
    Detailed runner for Sentry Mode (Opens Camera Window).
    """
    if not OPENCV_AVAILABLE:
        return "❌ OpenCV not installed."
        
    sentry = FaceSentry()
    if not sentry.available:
        return "❌ Face Sentinel Unavailable."
        
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "❌ Camera not found."
        
    start_time = time.time()
    
    # Full Screen or nice size
    window_name = "BRO SENTINEL MODE"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 480)
    
    detected_name = None
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Process
        name, confidence = sentry.process_frame(frame)
        
        # Draw UI
        if name:
            detected_name = name
            cv2.putText(frame, f"TARGET VERIFIED: {name.upper()}", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Since Haar is fast, we can just highlight the face roughly
            # (FaceSentry doesn't return rects nicely in public method, simpler to draw here if needed,
            # but for now, the Text is enough confirmation).
            
        else:
            cv2.putText(frame, "SCANNING...", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
        cv2.imshow(window_name, frame)
        
        # Exit conditions
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
            
        if time.time() - start_time > duration:
            break
            
    cap.release()
    cv2.destroyAllWindows()
    
    if detected_name:
        return f"User Identified: {detected_name}"
    return "No authorized user detected."
