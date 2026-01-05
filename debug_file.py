from tools.file_manager import file_info
import os

print(f"CWD: {os.getcwd()}")
print(f"File exists: {os.path.exists('requirements.txt')}")
print(file_info("requirements.txt"))
