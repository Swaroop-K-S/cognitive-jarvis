"""
BRO Cognitive Brain
Combines Hybrid LLM + Memory + Smart Routing into one unified brain.
"""

import json
import sys
import os
import re
from typing import Dict, Any, List, Optional
import urllib.request

# Gemini Removed - Local Only Mode

from jarvis.config import SYSTEM_PROMPT, OLLAMA_HOST
from jarvis.tools import execute_tool
from jarvis.tools.registry import tool_requires_confirmation, get_all_tools
from .model_selector import ModelSelector, TaskType, get_task_emoji, MODELS
from jarvis.cognitive import CognitiveEngine, CognitiveAction, get_action_emoji
from jarvis.memory import get_memory, CHROMADB_AVAILABLE


class CognitiveBrain:
    """
    BRO Cognitive Brain
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
        # Gemini Removed - Local Only
        
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
        return self.check_ollama()
    
    def get_status(self) -> Dict[str, Any]:
        internet = self.check_internet()
        ollama = self.check_ollama()
        # gemini removed
        memory_stats = self.cognitive.get_memory_stats()
        
        return {
            "internet": internet,
            "ollama_available": ollama,
            "memory_available": memory_stats.get("available", False),
            "memory_count": memory_stats.get("total", 0),
            "active_mode": "ollama" if ollama else "none",
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
        
        if ollama_ready:
            self.current_mode = "ollama"
            # Select best model for task
            model_spec, task_type = self.selector.select_model(user_input)
            self.current_task_type = task_type
            self.selector.ensure_model_loaded(model_spec.name)
            return self._call_ollama(enhanced_prompt, model_spec.name)
        
        return "No AI available. Is Ollama running?"
    
    # Gemini method removed

    
    def _call_ollama(self, prompt: str, model: str) -> str:
        try:
            # CONTEXT PRUNER: Prevent unbounded history growth (8k context limit)
            self._prune_context()
            
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
            
            # DEBUG: Print Raw LLM Response to see script usage
            print(f"\n🧠 [LLM RAW]: {content}\n")
            
            self.conversation_history.append({"role": "assistant", "content": content})
            return content
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return f"Error: {e}"

    def think_fast(self, prompt: str, image: str = None) -> str:
        """
        Fast, stateless thinking (no memory history). 
        Used for background monitoring loops.
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            if image:
                messages[0]["images"] = [image]
                
            payload = {
                "model": "llava:7b" if image else OLLAMA_MODEL, # Use Vision model if image provided
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 50} # Very short/fast
            }
            
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{OLLAMA_HOST}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result.get("message", {}).get("content", "").strip()
        except Exception as e:
            return f"Error: {e}"

    def think_with_vision(self, prompt: str, image: str) -> str:
        """
        Think about an image (stateless).
        Used for active visual tasks.
        """
        return self.think_fast(prompt, image)

    
    def _prune_context(self, max_messages: int = 20, keep_recent: int = 10):
        """
        Prune conversation history to prevent context window overflow.
        Keeps system prompt + last N messages.
        
        Args:
            max_messages: Trigger pruning when history exceeds this count
            keep_recent: Number of recent messages to keep after pruning
        """
        if len(self.conversation_history) > max_messages:
            # Keep system prompt [0] + last keep_recent messages
            system_prompt = self.conversation_history[0] if self.conversation_history else None
            recent_messages = self.conversation_history[-keep_recent:]
            
            if system_prompt and system_prompt.get("role") == "system":
                self.conversation_history = [system_prompt] + recent_messages
            else:
                self.conversation_history = recent_messages
            
            print(f"    📋 Context pruned: kept {len(self.conversation_history)} messages")
    
    def _extract_and_execute_tools(self, response: str) -> List[str]:
        """
        Extract and execute tool calls from the response.
        Uses JSON parsing first (robust), falls back to regex (legacy).
        """
        results = []
        
        # =====================================================================
        # METHOD 1: JSON PARSING (Robust - handles special characters)
        # =====================================================================
        try:
            # Try to find JSON block in response
            parsed = self._extract_json_block(response)
            if parsed:
                # DEBUG: Print parsed JSON
                # print(f"    🧩 Parsed JSON: {parsed}")
                tool_results = self._execute_parsed_tools(parsed)
                if tool_results:
                    return tool_results
        except Exception as e:
            print(f"    ⚠️ JSON parse failed, trying regex fallback: {e}")
        
        # =====================================================================
        # METHOD 2: REGEX FALLBACK (Legacy - for backward compatibility)
        # =====================================================================
        # Pattern for strict match: TOOL_CALL: name(args)
        strict_matches = list(re.finditer(r'TOOL_CALL:\s*(\w+)\(([^)]*)\)', response))
        
        # If no strict matches, try loose matches
        if not strict_matches:
            known_tools = "|".join(get_all_tools().keys())
            if known_tools:
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
            for m in re.finditer(r'(\w+)=["\']([^"\']*)["\']', args_str):
                args[m.group(1)] = m.group(2)
                
            if not args and args_str.strip():
                clean_arg = args_str.strip().strip('"\'')
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
    
    def _extract_json_block(self, response: str) -> dict:
        """Extract and parse JSON content from response."""
        import json
        
        # 1. Try to find ```json ... ``` block
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        content_to_parse = ""
        
        if json_match:
            content_to_parse = json_match.group(1).strip()
        else:
            # 2. Try to find raw JSON object { ... }
            # usage of regex to find the first { and last } might be fragile but works for most LLM outputs
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                content_to_parse = json_match.group(1).strip()
            # 3. If it looks like a simple dict
            elif response.strip().startswith('{') and response.strip().endswith('}'):
                content_to_parse = response.strip()

        if content_to_parse:
            try:
                # Attempt to fix common LLM JSON errors if strictly needed, 
                # but Llama 3 is usually good at valid JSON.
                return json.loads(content_to_parse)
            except json.JSONDecodeError:
                pass
                
        return None
    
    def _execute_parsed_tools(self, parsed: dict) -> List[str]:
        """Execute tools from parsed JSON structure."""
        results = []
        
        # Single tool case
        # In JSON format: {"tool": "name", "args": {...}}
        tool_name = parsed.get('tool', '')
        args = parsed.get('args', {})
        
        if tool_name and tool_name.strip():
            # If tool_name is actually a dict (misinterpretation), skip
            if isinstance(tool_name, str):
                if tool_requires_confirmation(tool_name):
                    if self.confirmation_callback:
                        if not self.confirmation_callback(tool_name, args):
                            return [f"Cancelled: {tool_name}"]
                results.append(execute_tool(tool_name, args))
        
        # Multiple tools case
        # In JSON format: {"tools": [{"name": "...", "args": {...}}]}
        tools_list = parsed.get('tools', [])
        for tool_data in tools_list:
            tool_name = tool_data.get('name') # Use .get() not .pop() to be safe
            tool_args = tool_data.get('args', {})
            
            if tool_name:
                if tool_requires_confirmation(tool_name):
                    if not self.confirmation_callback(tool_name, tool_data):
                        results.append(f"Cancelled: {tool_name}")
                        continue
                results.append(execute_tool(tool_name, tool_args))
        
        return results
    
    def get_spoken_response(self, response: str) -> str:
        """Extract just the spoken response from JSON output."""
        try:
            parsed = self._extract_json_block(response)
            if parsed:
                return parsed.get('response', response)
        except:
            pass
        return response

    
    def clear_history(self):
        self.conversation_history = [self.conversation_history[0]]
    
    def get_current_mode(self) -> str:
        return self.current_mode or "none"
    
    def get_current_model(self) -> str:
        return self.selector.current_model or "none"
