
import cv2
import time
from jarvis.vision.face_detect import FaceSentry

def test_camera():
    print("Initializing Face Sentry...")
    sentry = FaceSentry()
    
    if not sentry.available:
        print("Error: Face Sentry not available.")
        return

    print("Opening Camera (Index 0)...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Camera opened. Press 'q' to quit.")
    print("Look at the camera to test face detection.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame.")
            break

        # Process frame
        name, conf = sentry.process_frame(frame)
        
        # Draw results
        if name:
            cv2.putText(frame, f"User: {name} ({conf:.2f})", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.rectangle(frame, (10, 10), (frame.shape[1]-10, frame.shape[0]-10), (0, 255, 0), 2)
        else:
             cv2.putText(frame, "No Face Detected", (50, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow('BRO Vision Test', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_camera()
