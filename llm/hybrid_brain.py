"""
BRO Hybrid Brain with Smart Model Selection
- Online: Gemini API (0% VRAM, max intelligence)
- Offline: Specialist models (auto-selected per task)

Specialist Models:
- qwen2.5-coder:7b  → Code
- moondream         → Vision
- deepseek-r1:8b    → Math/Logic
- llama3.2          → General
"""

import json
import sys
import os
import re
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from config import SYSTEM_PROMPT, GEMINI_API_KEY, GEMINI_MODEL, OLLAMA_HOST
from tools import get_tools_schema, execute_tool
from tools.registry import tool_requires_confirmation, get_all_tools
from .model_selector import ModelSelector, TaskType, get_task_emoji, MODELS


class HybridBrain:
    """
    Hybrid AI brain with smart model selection.
    - Online: Uses Gemini (saves VRAM)
    - Offline: Auto-selects specialist model per task
    """
    
    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.confirmation_callback = None
        self.current_mode = None
        self.current_task_type = None
        
        # Initialize model selector
        self.selector = ModelSelector(OLLAMA_HOST)
        
        # Initialize Gemini
        if GEMINI_AVAILABLE and GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        else:
            self.gemini_model = None
        
        # Build system prompt
        self.system_prompt = self._build_system_prompt()
        self.conversation_history.append({
            "role": "system",
            "content": self.system_prompt
        })
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with tools."""
        tools_info = "\n\nAVAILABLE TOOLS:\n"
        for name, tool_info in get_all_tools().items():
            params = ", ".join(tool_info.get("required", []))
            tools_info += f"- {name}({params}): {tool_info['description']}\n"
        
        tools_info += """
TO USE A TOOL, respond with:
TOOL_CALL: tool_name(arg1="value1", arg2="value2")

Examples:
- "open notepad" -> TOOL_CALL: open_application(app_name="notepad")
- "show downloads" -> TOOL_CALL: open_folder(folder_path="downloads")
"""
        return SYSTEM_PROMPT + tools_info
    
    def check_internet(self) -> bool:
        """Check internet connectivity."""
        try:
            req = urllib.request.Request("https://www.google.com", method='HEAD')
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except:
            return False
    
    def check_ollama_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except:
            return False
    
    def is_available(self) -> bool:
        """Check if any brain is available."""
        return (self.gemini_model and self.check_internet()) or self.check_ollama_available()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        internet = self.check_internet()
        ollama = self.check_ollama_available()
        gemini = bool(self.gemini_model) and internet
        
        return {
            "internet": internet,
            "gemini_available": gemini,
            "ollama_available": ollama,
            "active_mode": "gemini" if gemini else ("ollama" if ollama else "none"),
            "current_model": self.selector.current_model,
            "current_task_type": self.current_task_type
        }
    
    def set_confirmation_callback(self, callback):
        self.confirmation_callback = callback
    
    def process(self, user_input: str, image_path: str = None) -> str:
        """
        Process request with smart model selection.
        
        Args:
            user_input: User's message
            image_path: Optional image for vision tasks
        """
        is_online = self.check_internet()
        gemini_ready = bool(self.gemini_model) and is_online
        ollama_ready = self.check_ollama_available()
        
        # Analyze the task type
        model_spec, task_type = self.selector.select_model(user_input, bool(image_path))
        self.current_task_type = task_type
        task_emoji = get_task_emoji(task_type)
        
        if gemini_ready:
            # Online: Use Gemini (no model switching needed)
            self.current_mode = "gemini"
            print(f"    {task_emoji} Task: {task_type.value} → Using Gemini (cloud)")
            response = self._process_gemini(user_input, image_path)
        elif ollama_ready:
            # Offline: Use specialist model
            self.current_mode = "ollama"
            
            # Switch to the right specialist
            current = self.selector.current_model
            target = model_spec.name
            
            if current != target:
                print(f"    {task_emoji} Task: {task_type.value} → Switching to {target}")
                self.selector.ensure_model_loaded(target)
            else:
                print(f"    {task_emoji} Task: {task_type.value} → Using {target}")
            
            response = self._process_ollama(user_input, model_spec.name)
        else:
            return self._handle_no_brain()
        
        # Execute tool calls
        tool_result = self._extract_and_execute_tool(response)
        if tool_result:
            response = f"{response}\n\n✓ {tool_result}"
        
        return response
    
    def _process_gemini(self, user_input: str, image_path: str = None) -> str:
        """Process with Gemini API."""
        try:
            if image_path:
                import PIL.Image
                img = PIL.Image.open(image_path)
                response = self.gemini_model.generate_content([user_input, img])
            else:
                full_prompt = f"{self.system_prompt}\n\nUser: {user_input}\n\nAssistant:"
                response = self.gemini_model.generate_content(full_prompt)
            
            result = response.text
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": result})
            return result
            
        except Exception as e:
            if self.check_ollama_available():
                print(f"⚠️ Gemini error, falling back to local: {e}")
                self.current_mode = "ollama"
                return self._process_ollama(user_input, "llama3.2")
            return f"Error: {e}"
    
    def _process_ollama(self, user_input: str, model_name: str) -> str:
        """Process with local Ollama model."""
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            
            payload = {
                "model": model_name,
                "messages": self.conversation_history,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 500}
            }
            
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{OLLAMA_HOST}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode())
                content = result.get("message", {}).get("content", "")
            
            self.conversation_history.append({"role": "assistant", "content": content})
            return content
            
        except Exception as e:
            return f"Error: {e}"
    
    def _extract_and_execute_tool(self, response: str) -> Optional[str]:
        """Extract and run tool calls."""
        match = re.search(r'TOOL_CALL:\s*(\w+)\(([^)]*)\)', response)
        if not match:
            return None
        
        tool_name = match.group(1)
        args_str = match.group(2)
        
        args = {}
        for m in re.finditer(r'(\w+)=["\'](.*?)["\']', args_str):
            args[m.group(1)] = m.group(2)
        
        if tool_requires_confirmation(tool_name):
            if self.confirmation_callback:
                if not self.confirmation_callback(tool_name, args):
                    return f"Cancelled: {tool_name}"
        
        return execute_tool(tool_name, args)
    
    def _handle_no_brain(self) -> str:
        return """No AI available!

Setup:
1. ONLINE: Add GEMINI_API_KEY to .env
2. OFFLINE: Install Ollama, run 'ollama pull llama3.2'
"""
    
    def clear_history(self):
        self.conversation_history = [self.conversation_history[0]]
    
    def get_current_mode(self) -> str:
        return self.current_mode or "none"
    
    def get_current_model(self) -> str:
        if self.current_mode == "gemini":
            return GEMINI_MODEL
        return self.selector.current_model or "none"
