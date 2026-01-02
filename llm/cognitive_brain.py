"""
JARVIS Cognitive Brain
Combines Hybrid LLM + Memory + Smart Routing into one unified brain.
"""

import json
import sys
import os
import re
from typing import Dict, Any, List, Optional
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from config import SYSTEM_PROMPT, GEMINI_API_KEY, GEMINI_MODEL, OLLAMA_HOST
from tools import execute_tool
from tools.registry import tool_requires_confirmation, get_all_tools
from .model_selector import ModelSelector, TaskType, get_task_emoji, MODELS
from cognitive import CognitiveEngine, CognitiveAction, get_action_emoji
from memory import get_memory, CHROMADB_AVAILABLE


class CognitiveBrain:
    """
    JARVIS Cognitive Brain
    - Remembers context from past conversations
    - Thinks before acting
    - Smart-routes to specialist models
    - Online/Offline hybrid switching
    """
    
    def __init__(self):
        self.conversation_history: List[Dict[str, Any]] = []
        self.confirmation_callback = None
        self.current_mode = None
        self.current_task_type = None
        
        # Initialize components
        self.cognitive = CognitiveEngine(OLLAMA_HOST)
        self.selector = ModelSelector(OLLAMA_HOST)
        self.memory = get_memory() if CHROMADB_AVAILABLE else None
        
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
TO USE A TOOL:
TOOL_CALL: tool_name(arg1="value1")
"""
        return SYSTEM_PROMPT + tools_info
    
    def check_internet(self) -> bool:
        try:
            req = urllib.request.Request("https://www.google.com", method='HEAD')
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except:
            return False
    
    def check_ollama(self) -> bool:
        try:
            req = urllib.request.Request(f"{OLLAMA_HOST}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except:
            return False
    
    def is_available(self) -> bool:
        return (self.gemini_model and self.check_internet()) or self.check_ollama()
    
    def get_status(self) -> Dict[str, Any]:
        internet = self.check_internet()
        ollama = self.check_ollama()
        gemini = bool(self.gemini_model) and internet
        memory_stats = self.cognitive.get_memory_stats()
        
        return {
            "internet": internet,
            "gemini_available": gemini,
            "ollama_available": ollama,
            "memory_available": memory_stats.get("available", False),
            "memory_count": memory_stats.get("total", 0),
            "active_mode": "gemini" if gemini else ("ollama" if ollama else "none"),
            "current_model": self.selector.current_model
        }
    
    def set_confirmation_callback(self, callback):
        self.confirmation_callback = callback
    
    def process(self, user_input: str) -> str:
        """
        Process with full cognitive loop:
        1. REMEMBER (recall context)
        2. THINK (analyze intent)
        3. DECIDE (choose action)
        4. ACT (execute & respond)
        """
        # COGNITIVE LOOP: Think & Decide
        decision = self.cognitive.process(user_input)
        action_emoji = get_action_emoji(decision.action)
        
        # Show cognitive decision
        print(f"    {action_emoji} {decision.action.value.upper()}: {decision.reasoning}")
        if decision.memory_context:
            print(f"    🔍 Context: {decision.memory_context[:80]}...")
        
        # EXECUTE based on decision
        if decision.action == CognitiveAction.REMEMBER:
            response = self.cognitive.execute_remember(user_input)
            return response
        
        elif decision.action == CognitiveAction.RECALL:
            response = self.cognitive.execute_recall(user_input)
            return response
        
        elif decision.action in [CognitiveAction.ACT, CognitiveAction.CODE, CognitiveAction.CHAT]:
            # Use LLM to generate response with memory context
            response = self._generate_response(user_input, decision.memory_context)
            
            # Execute any tool calls
            tool_results = self._extract_and_execute_tools(response)
            if tool_results:
                response = f"{response}\n\n" + "\n".join([f"✓ {res}" for res in tool_results])
            
            # Save this conversation to memory
            self.cognitive.save_conversation(user_input, response)
            
            return response
        
        return "I'm not sure how to help with that."
    
    def _generate_response(self, user_input: str, context: str = "") -> str:
        """Generate response using best available brain."""
        is_online = self.check_internet()
        gemini_ready = bool(self.gemini_model) and is_online
        ollama_ready = self.check_ollama()
        
        # Enhance prompt with memory context
        if context:
            enhanced_prompt = f"Context from memory: {context}\n\nUser: {user_input}"
        else:
            enhanced_prompt = user_input
        
        if gemini_ready:
            self.current_mode = "gemini"
            return self._call_gemini(enhanced_prompt)
        elif ollama_ready:
            self.current_mode = "ollama"
            # Select best model for task
            model_spec, task_type = self.selector.select_model(user_input)
            self.current_task_type = task_type
            self.selector.ensure_model_loaded(model_spec.name)
            return self._call_ollama(enhanced_prompt, model_spec.name)
        
        return "No AI available. Setup Gemini or Ollama."
    
    def _call_gemini(self, prompt: str) -> str:
        try:
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            if self.check_ollama():
                self.current_mode = "ollama"
                return self._call_ollama(prompt, "llama3.2")
            return f"Error: {e}"
    
    def _call_ollama(self, prompt: str, model: str) -> str:
        try:
            self.conversation_history.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
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
    
    def _extract_and_execute_tools(self, response: str) -> List[str]:
        """Extract and execute ALL tool calls in the response."""
        results = []
        
        # Pattern for strict match: TOOL_CALL: name(args)
        # We process matches sequentially
        
        # 1. Find all strict matches
        strict_matches = list(re.finditer(r'TOOL_CALL:\s*(\w+)\(([^)]*)\)', response))
        
        # 2. If no strict matches, try loose matches
        if not strict_matches:
            known_tools = "|".join(get_all_tools().keys())
            if known_tools:
                # Look for known_tool_name(args)
                loose_matches = list(re.finditer(fr'({known_tools})\s*\(([^)]*)\)', response))
                matches = loose_matches
            else:
                matches = []
        else:
            matches = strict_matches
            
        for match in matches:
            tool_name = match.group(1)
            args_str = match.group(2)
            
            args = {}
            # Parse args: look for key="value" or key='value'
            for m in re.finditer(r'(\w+)=["\'](.*?)["\']', args_str):
                args[m.group(1)] = m.group(2)
                
            # If no named args found, check if it's a positional arg (simple case)
            if not args and args_str.strip():
                # Basic cleanup of quotes
                clean_arg = args_str.strip().strip('"\'')
                # If tool has 1 required arg, map it
                tool_info = get_all_tools().get(tool_name, {})
                required = tool_info.get("required", [])
                if len(required) == 1:
                    args[required[0]] = clean_arg
            
            if tool_requires_confirmation(tool_name):
                if self.confirmation_callback:
                    if not self.confirmation_callback(tool_name, args):
                        results.append(f"Cancelled: {tool_name}")
                        continue
            
            results.append(execute_tool(tool_name, args))
            
        return results
    
    def clear_history(self):
        self.conversation_history = [self.conversation_history[0]]
    
    def get_current_mode(self) -> str:
        return self.current_mode or "none"
    
    def get_current_model(self) -> str:
        if self.current_mode == "gemini":
            return GEMINI_MODEL
        return self.selector.current_model or "none"
