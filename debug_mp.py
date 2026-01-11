import mediapipe as mp
print(f"MediaPipe Version: {mp.__version__}")
print(f"Dir(mp): {dir(mp)}")

try:
    print(f"Solutions: {mp.solutions}")
except AttributeError as e:
    print(f"Error accessing mp.solutions: {e}")
    try:
        import mediapipe.python.solutions as solutions
        print(f"Found solutions via direct import: {solutions}")
    except ImportError as e2:
        print(f"Direct import failed too: {e2}")
