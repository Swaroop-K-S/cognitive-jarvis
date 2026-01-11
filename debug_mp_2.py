try:
    import mediapipe.solutions
    print("Found mediapipe.solutions")
    print(dir(mediapipe.solutions))
except ImportError as e:
    print(f"Failed mediapipe.solutions: {e}")

try:
    import mediapipe.tasks
    print("Found mediapipe.tasks")
except ImportError as e:
    print(f"Failed mediapipe.tasks: {e}")
