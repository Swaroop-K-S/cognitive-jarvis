"""
JARVIS Offline Brain Module
Uses Ollama for local LLM inference - works completely offline!
"""

import json
import sys
import os
import re
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SYSTEM_PROMPT
from tools import get_tools_schema, execute_tool
from tools.registry import tool_requires_confirmation, get_all_tools


class OllamaBrain:
    """
    Offline JARVIS brain using Ollama for local LLM inference.
    No internet required!
    """
    
    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        """
        Initialize the Ollama brain.
        
        Args:
            model: The Ollama model to use (e.g., 'llama3.2', 'mistral', 'phi3')
            host: The Ollama server URL (default: localhost:11434)
        """
        self.model = model
        self.host = host
        self.conversation_history: List[Dict[str, Any]] = []
        self.confirmation_callback = None
        
        # Build the system prompt with tool information
        self.system_prompt = self._build_system_prompt()
        
        # Initialize conversation with system prompt
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with available tools."""
        tools_info = "\n\nAVAILABLE TOOLS:\n"
        for name, tool_info in get_all_tools().items():
            params = ", ".join(tool_info.get("required", []))
            tools_info += f"- {name}({params}): {tool_info['description']}\n"
        
        tools_info += """
TO USE A TOOL, respond with EXACTLY this format (on its own line):
TOOL_CALL: tool_name(arg1="value1", arg2="value2")

Example responses:
- User says "open notepad" -> TOOL_CALL: open_application(app_name="notepad")
- User says "show my downloads" -> TOOL_CALL: open_folder(folder_path="downloads")
- User says "search for Python" -> TOOL_CALL: search_web(query="Python")

After the tool executes, explain what you did briefly.
If no tool is needed, just respond conversationally.
"""
        return SYSTEM_PROMPT + tools_info
    
    def is_available(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except:
            return False
    
    def check_model_exists(self) -> bool:
        """Check if the configured model is available in Ollama."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                return self.model.split(":")[0] in models
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return [m.get("name", "") for m in data.get("models", [])]
        except:
            return []
    
    def set_confirmation_callback(self, callback):
        """Set a callback for confirming dangerous actions."""
        self.confirmation_callback = callback
    
    def process(self, user_input: str) -> str:
        """
        Process user input and return JARVIS's response.
        
        Args:
            user_input: The user's message or command
            
        Returns:
            JARVIS's response as a string
        """
        if not self.is_available():
            return self._handle_ollama_unavailable()
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            # Call Ollama API
            response = self._call_ollama()
            
            # Check for tool calls in response
            tool_result = self._extract_and_execute_tool(response)
            if tool_result:
                # Add the tool execution result to the response
                response = f"{response}\n\n[Tool Result: {tool_result}]"
            
            # Add response to history
            self.conversation_history.append({
                "role": "assistant", 
                "content": response
            })
            
            return response
            
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def _call_ollama(self) -> str:
        """Make a request to Ollama API."""
        payload = {
            "model": self.model,
            "messages": self.conversation_history,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500
            }
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            return result.get("message", {}).get("content", "")
    
    def _extract_and_execute_tool(self, response: str) -> Optional[str]:
        """
        Extract tool call from response and execute it.
        
        Args:
            response: The LLM response text
            
        Returns:
            Tool execution result, or None if no tool call
        """
        # Look for TOOL_CALL pattern
        pattern = r'TOOL_CALL:\s*(\w+)\(([^)]*)\)'
        match = re.search(pattern, response)
        
        if not match:
            return None
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        # Parse arguments
        args = {}
        if args_str:
            # Parse key="value" patterns
            arg_pattern = r'(\w+)=["\'](.*?)["\']'
            for arg_match in re.finditer(arg_pattern, args_str):
                args[arg_match.group(1)] = arg_match.group(2)
        
        # Check if confirmation required
        if tool_requires_confirmation(tool_name):
            if self.confirmation_callback:
                if not self.confirmation_callback(tool_name, args):
                    return f"Action '{tool_name}' was cancelled by user."
        
        # Execute the tool
        result = execute_tool(tool_name, args)
        return result
    
    def _handle_ollama_unavailable(self) -> str:
        """Handle case when Ollama is not running."""
        return """Ollama is not running. To use offline mode:

1. Install Ollama from: https://ollama.com/download
2. Start Ollama (it runs in the background)
3. Pull a model: ollama pull llama3.2
4. Restart JARVIS

Available models: llama3.2, mistral, phi3, gemma2
"""
    
    def clear_history(self):
        """Clear conversation history, keeping only system prompt."""
        self.conversation_history = [self.conversation_history[0]]
    
    def get_history_length(self) -> int:
        """Get the number of messages in history."""
        return len(self.conversation_history)


# Convenience function
_default_brain: Optional[OllamaBrain] = None

def process_offline(message: str) -> str:
    """Process a message using the default Ollama brain."""
    global _default_brain
    if _default_brain is None:
        _default_brain = OllamaBrain()
    return _default_brain.process(message)
