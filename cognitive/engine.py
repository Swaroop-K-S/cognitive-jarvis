"""
BRO Cognitive Engine
Implements the Think-Decide-Remember-Act loop.
Standalone module - no LLM dependencies to avoid circular imports.
"""

import sys
import os
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory import get_memory, CHROMADB_AVAILABLE


class CognitiveAction(Enum):
    """Actions the cognitive engine can take."""
    REMEMBER = "remember"
    RECALL = "recall"
    ACT = "act"
    CHAT = "chat"
    CODE = "code"


@dataclass
class CognitiveDecision:
    """Result of the cognitive decision process."""
    action: CognitiveAction
    reasoning: str
    content: str
    memory_context: str


# Task detection keywords
REMEMBER_KEYWORDS = [
    "my name is", "i am", "remember that", "remember this",
    "my favorite", "i like", "i prefer", "my project is",
    "my id is", "i work", "my email", "my number",
    "save this", "note that", "keep in mind"
]

RECALL_KEYWORDS = [
    "what is my", "what's my", "do you remember",
    "what did i", "my name", "my project", "what was",
    "tell me about my", "remind me"
]

CODE_KEYWORDS = [
    "code", "program", "script", "function", "debug",
    "python", "javascript", "java", "fix bug", "write"
]

SYSTEM_KEYWORDS = [
    "open", "close", "run", "start", "folder",
    "file", "app", "screenshot", "process"
]


class CognitiveEngine:
    """The cognitive core of BRO."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.memory = get_memory() if CHROMADB_AVAILABLE else None
        self.ollama_host = ollama_host
        
    def is_memory_available(self) -> bool:
        return self.memory is not None and self.memory.is_available()
    
    def process(self, user_input: str) -> CognitiveDecision:
        """Process through cognitive loop."""
        memory_context = self._recall_context(user_input)
        action, reasoning = self._think_and_decide(user_input)
        
        return CognitiveDecision(
            action=action,
            reasoning=reasoning,
            content=user_input,
            memory_context=memory_context
        )
    
    def _recall_context(self, query: str) -> str:
        if not self.is_memory_available():
            return ""
        return self.memory.recall_text(query, n_results=3)
    
    def _think_and_decide(self, user_input: str) -> Tuple[CognitiveAction, str]:
        """Decide action based on keywords."""
        input_lower = user_input.lower()
        
        for kw in REMEMBER_KEYWORDS:
            if kw in input_lower:
                return CognitiveAction.REMEMBER, f"Storage: '{kw}'"
        
        for kw in RECALL_KEYWORDS:
            if kw in input_lower:
                return CognitiveAction.RECALL, f"Recall: '{kw}'"
        
        for kw in SYSTEM_KEYWORDS:
            if kw in input_lower:
                return CognitiveAction.ACT, f"System: '{kw}'"
        
        for kw in CODE_KEYWORDS:
            if kw in input_lower:
                return CognitiveAction.CODE, f"Code: '{kw}'"
        
        return CognitiveAction.CHAT, "General chat"
    
    def execute_remember(self, user_input: str) -> str:
        if not self.is_memory_available():
            return "Memory not available."
        
        if self.memory.remember_fact(user_input):
            return f"✓ Remembered: {user_input}"
        return "Failed to save."
    
    def execute_recall(self, query: str) -> str:
        if not self.is_memory_available():
            return "Memory not available."
        
        memories = self.memory.recall(query, n_results=3)
        if not memories:
            return "No matching memories."
        
        result = "I remember:\n"
        for mem in memories:
            result += f"• {mem['content']}\n"
        return result
    
    def save_conversation(self, user_msg: str, assistant_msg: str):
        if self.is_memory_available():
            self.memory.remember_conversation(user_msg, assistant_msg)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        if not self.is_memory_available():
            return {"available": False, "total": 0}
        stats = self.memory.get_stats()
        stats["available"] = True
        return stats


def get_action_emoji(action: CognitiveAction) -> str:
    return {
        CognitiveAction.REMEMBER: "💾",
        CognitiveAction.RECALL: "🔍",
        CognitiveAction.ACT: "⚡",
        CognitiveAction.CHAT: "💬",
        CognitiveAction.CODE: "💻"
    }.get(action, "🤖")
