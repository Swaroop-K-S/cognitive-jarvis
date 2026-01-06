"""
Semantic Router for Intent Classification
Uses sentence embeddings for intelligent intent routing instead of keyword matching.
"""

import sys
import os
from typing import Dict, List, Tuple, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import sentence-transformers
EMBEDDINGS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer, util
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    util = None


class Intent(Enum):
    """Possible intents for user messages."""
    REMEMBER = "remember"
    RECALL = "recall"
    ACT = "act"
    CODE = "code"
    CHAT = "chat"


# Intent anchor phrases - diverse examples for each intent
INTENT_ANCHORS = {
    Intent.REMEMBER: [
        # Direct memory commands
        "Remember that my name is John",
        "Save this information for later",
        "My favorite color is blue",
        "I prefer dark mode",
        "Note that I work at Google",
        "Keep in mind that I'm allergic to peanuts",
        "Store the fact that I hate mushrooms",
        "My email is john@example.com",
        "I use Python for most projects",
        "My birthday is March 15th",
        "Please remember I have a meeting tomorrow",
        "Add to memory: I like coffee",
        # Natural phrasing (fixes Test 1)
        "Make a note that I'm out of milk",
        "Make a note of this",
        "Jot this down",
        "Don't forget that I need groceries",
        "Write down that I have a dentist appointment",
        "I want you to remember this",
        "Store this for later",
        "Log this information",
        "Take note of my address",
        "Record that my password is abc123",
    ],
    Intent.RECALL: [
        # Memory retrieval
        "What is my name?",
        "What's my email address?",
        "Do you remember my preference?",
        "What did I tell you about my project?",
        "Remind me about my meeting",
        "What was my favorite color?",
        "Tell me about my information",
        "What do you know about me?",
        "Recall my settings",
        "What are my preferences?",
    ],
    Intent.ACT: [
        # System/app actions
        "Open Chrome browser",
        "Close Spotify",
        "Launch Visual Studio Code",
        "Start Notepad",
        "Take a screenshot",
        "Open the calculator",
        "Show my files",
        "Run the terminal",
        "Start BlueStacks",
        "Open WhatsApp",
        "Turn on dark mode",
        "Navigate to settings",
        "Click the button",
        "Type hello world",
        "Press enter key",
        "Search for Python",
        "Search for Python",
        "Go to google.com",
        # Video & Copilot
        "Summarize this video",
        "Find when this happens in the video",
        "Enable screen copilot",
        "Take over the screen",
        "Watch my screen",
        "Analyze this video",
    ],
    Intent.CODE: [
        # Programming related
        "Write a Python function to sort a list",
        "Debug this code for me",
        "How do I fix this error?",
        "Create a JavaScript class",
        "Explain this algorithm",
        "Write a regex pattern",
        "Help me with this function",
        "What's wrong with my code?",
        "Generate a REST API",
        "Write unit tests for this",
    ],
    Intent.CHAT: [
        # General conversation
        "Hello, how are you?",
        "Tell me a joke",
        "What's the weather like?",
        "Who is the president?",
        "What is the meaning of life?",
        "Good morning",
        "Thanks for your help",
        "You're awesome",
        "What can you do?",
        "Tell me something interesting",
    ],
}


class SemanticRouter:
    """
    Routes user input to the correct intent using semantic similarity.
    Much more robust than keyword matching.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic router.
        
        Args:
            model_name: Sentence transformer model to use.
                       "all-MiniLM-L6-v2" is fast and good quality.
        """
        self.model = None
        self.anchor_embeddings: Dict[Intent, any] = {}
        self.confidence_threshold = 0.35  # Minimum similarity for confident match
        
        if EMBEDDINGS_AVAILABLE:
            try:
                print("    📊 Loading semantic router...")
                self.model = SentenceTransformer(model_name)
                self._compute_anchor_embeddings()
                print("    ✓ Semantic router ready")
            except Exception as e:
                print(f"    ⚠️ Semantic router failed to load: {e}")
                self.model = None
    
    def _compute_anchor_embeddings(self):
        """Pre-compute embeddings for all anchor phrases."""
        if not self.model:
            return
        
        for intent, phrases in INTENT_ANCHORS.items():
            # Encode all anchor phrases for this intent
            embeddings = self.model.encode(phrases, convert_to_tensor=True)
            self.anchor_embeddings[intent] = embeddings
    
    def route(self, user_input: str) -> Tuple[Intent, float, str]:
        """
        Route user input to the best matching intent.
        
        Args:
            user_input: The user's message
            
        Returns:
            Tuple of (intent, confidence_score, reasoning)
        """
        if not self.model or not self.anchor_embeddings:
            # Fallback to keyword-based routing
            return self._keyword_fallback(user_input)
        
        try:
            # Encode user input
            input_embedding = self.model.encode(user_input, convert_to_tensor=True)
            
            # Compare with all intent anchors
            scores = {}
            best_matches = {}
            
            for intent, anchor_embeds in self.anchor_embeddings.items():
                # Compute cosine similarities
                similarities = util.cos_sim(input_embedding, anchor_embeds)[0]
                # Take the max similarity (best matching anchor)
                max_sim = float(similarities.max())
                max_idx = int(similarities.argmax())
                
                scores[intent] = max_sim
                best_matches[intent] = INTENT_ANCHORS[intent][max_idx]
            
            # Find the best intent
            best_intent = max(scores, key=scores.get)
            best_score = scores[best_intent]
            best_anchor = best_matches[best_intent]
            
            # Check confidence threshold
            if best_score < self.confidence_threshold:
                # Low confidence - default to CHAT
                return Intent.CHAT, best_score, f"Low confidence ({best_score:.2f}), defaulting to chat"
            
            return best_intent, best_score, f"Matched: '{best_anchor[:40]}...' ({best_score:.2f})"
            
        except Exception as e:
            return self._keyword_fallback(user_input)
    
    def _keyword_fallback(self, user_input: str) -> Tuple[Intent, float, str]:
        """Fallback keyword-based routing when embeddings unavailable."""
        input_lower = user_input.lower()
        
        # Remember keywords
        remember_kw = ["my name is", "remember that", "remember this", "save this", 
                       "note that", "keep in mind", "store the fact", "my favorite"]
        for kw in remember_kw:
            if kw in input_lower:
                return Intent.REMEMBER, 0.8, f"Keyword: '{kw}'"
        
        # Recall keywords
        recall_kw = ["what is my", "what's my", "do you remember", "remind me", 
                     "what did i", "tell me about my"]
        for kw in recall_kw:
            if kw in input_lower:
                return Intent.RECALL, 0.8, f"Keyword: '{kw}'"
        
        # Action keywords
        act_kw = ["open", "close", "start", "launch", "run", "click", "type", 
                  "press", "screenshot", "navigate", "go to"]
        for kw in act_kw:
            if kw in input_lower:
                return Intent.ACT, 0.8, f"Keyword: '{kw}'"
        
        # Code keywords
        code_kw = ["code", "program", "function", "debug", "script", "python", 
                   "javascript", "fix bug", "write", "algorithm"]
        for kw in code_kw:
            if kw in input_lower:
                return Intent.CODE, 0.8, f"Keyword: '{kw}'"
        
        # Default to chat
        return Intent.CHAT, 0.5, "No match, defaulting to chat"
    
    def is_available(self) -> bool:
        """Check if semantic routing is available."""
        return self.model is not None


# Global router instance (lazy initialization)
_router: Optional[SemanticRouter] = None


def get_semantic_router() -> SemanticRouter:
    """Get or create the global semantic router."""
    global _router
    if _router is None:
        _router = SemanticRouter()
    return _router


def semantic_route(user_input: str) -> Tuple[Intent, float, str]:
    """Convenience function to route user input."""
    router = get_semantic_router()
    return router.route(user_input)
