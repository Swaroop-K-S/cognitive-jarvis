"""
BRO Developer Tools
Tools for coding, running scripts, and terminal operations.
"""

import subprocess
import os
import sys
from typing import Optional
from .registry import tool

# Forbidden commands for safety
FORBIDDEN_COMMANDS = [
    "rm -rf", "del /s", "format", "mkfs", "dd",
    "shutdown", "reboot", ":(){ :|:& };:"
]

@tool("run_terminal_command", "Runs a terminal command. Use caution. Captures stdout/stderr.", requires_confirmation=True)
def run_terminal_command(command: str, timeout: int = 30) -> str:
    """
    Executes a shell command and returns output.
    
    Args:
        command: The command to run (e.g., 'dir', 'python --version')
        timeout: Max time in seconds
    """
    # Safety Check
    for bad in FORBIDDEN_COMMANDS:
        if bad in command.lower():
            return f"❌ Command blocked for safety: {bad}"
            
    try:
        # Run command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
            
        if not output.strip():
            return "✓ Command executed (no output)"
            
        return f"✓ Output:\n{output[:2000]}" # Truncate long output
    except subprocess.TimeoutExpired:
        return "❌ Command timed out."
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


@tool("create_python_script", "Creates a new Python script with the given code.")
def create_python_script(filename: str, code: str) -> str:
    """
    Creates a python file.
    
    Args:
        filename: Name of file (e.g. 'hello.py')
        code: Content of the script
    """
    try:
        if not filename.endswith(".py"):
            filename += ".py"
            
        # Security: Don't allow overwriting critical files easily
        # For now, simplistic check
        if os.path.exists(filename):
            return f"⚠️ File {filename} already exists. Use 'overwrite' tool or choose new name."
            
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
            
        return f"✓ Created {filename}"
        
    except Exception as e:
        return f"❌ Error creating file: {str(e)}"

@tool("run_python_script", "Runs a Python script.")
def run_python_script(filename: str) -> str:
    """
    Runs a python script using the current python interpreter.
    """
    if not os.path.exists(filename):
        return f"❌ File not found: {filename}"
    
    return run_terminal_command(f"{sys.executable} {filename}")
