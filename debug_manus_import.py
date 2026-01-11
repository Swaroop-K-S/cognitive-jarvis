import sys
import os

# Add OpenManus to path (Sibling directory)
current_dir = os.getcwd() # c:\Users\swaro\Code\New folder (3)\jarvis
project_root = os.path.dirname(current_dir) # c:\Users\swaro\Code\New folder (3)
manus_path = os.path.join(project_root, "OpenManus")
print(f"Adding to path: {manus_path}")

if manus_path not in sys.path:
    sys.path.append(manus_path)

try:
    print("Attempting to import app.agent.manus...")
    from app.agent.manus import Manus
    print("✅ SUCCESS: Manus imported.")
except ImportError as e:
    print(f"❌ ImportError: {e}")
except Exception as e:
    print(f"❌ Other Error: {e}")

# Check for specific dependencies likely to be missing
dependencies = ['tenacity', 'pydantic', 'openai', 'playwright', 'numpy', 'pandas']
print("\nChecking common dependencies:")
for dep in dependencies:
    try:
        __import__(dep)
        print(f"  {dep}: Installed")
    except ImportError:
        print(f"  {dep}: MISSING")
