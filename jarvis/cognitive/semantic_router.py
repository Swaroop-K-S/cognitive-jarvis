"""
Semantic Capability Router
Uses vector embeddings to route user prompts to the correct cognitive engine (Memory, Automation, Chat, etc.)
even without exact keyword matches.
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
from jarvis.cognitive import CognitiveAction

# Try to import sentence_transformers, handle if missing
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


class SemanticRouter:
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        self.model = None
        self.routes = {}
        self.embeddings = {}
        
        global EMBEDDINGS_AVAILABLE
        
        if EMBEDDINGS_AVAILABLE:
            # Load a lightweight model for speed
            print("    🧠 Loading Semantic Router (all-MiniLM-L6-v2)...")
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self._initialize_routes()
                print("    ✅ Semantic Router Online")
            except Exception as e:
                print(f"    ⚠️ Router Load Failed: {e}")
                EMBEDDINGS_AVAILABLE = False

    def _initialize_routes(self):
        """Define anchor phrases for each cognitive action."""
        # Anchors are representative phrases for each intent
        route_anchors = {
            CognitiveAction.REMEMBER: [
                "remember that", "store this information", "save this to memory",
                "don't forget that", "keep a note of this", "memorize this fact",
                "add this to your database", "I want you to know that",
                "here is a new fact", "update your knowledge", "the sky is blue",
                "my name is"
            ],
            CognitiveAction.RECALL: [
                "what do you know about", "search your memory for", "recall information on",
                "have we talked about", "do you remember", "look up in database",
                "what did I tell you about", "retrieve notes on", "check your logs"
            ],
            CognitiveAction.CODE: [
                "write a python script", "generate code for", "debug this function",
                "create a react component", "implement a class", "fix this error",
                "refactor this code", "how do I code this", "programming help"
            ],
            CognitiveAction.ACT: [
                "open the application", "click on the button", "scroll down",
                "take a screenshot", "type this text", "press enter",
                "go to website", "search google for", "play some music",
                "turn up volume", "set a timer", "check the weather",
                "launch chrome", "open browser", "run this app"
            ]
        }
        
        self.routes = {}
        self.embeddings = {}
        
        # Pre-compute embeddings for anchors
        for action, phrases in route_anchors.items():
            self.routes[action] = phrases
            self.embeddings[action] = self.model.encode(phrases)

    def route(self, query: str) -> Optional[Tuple[CognitiveAction, float]]:
        """
        Route a query to an action based on semantic similarity.
        Returns (Action, Confidence) or None if below threshold.
        """
        if not EMBEDDINGS_AVAILABLE or not self.model:
            return None
            
        # Encode query
        query_emb = self.model.encode([query])[0]
        
        best_action = None
        best_score = -1.0
        
        # Compare against all route anchors
        for action, anchor_embs in self.embeddings.items():
            # Calculate cosine similarities
            # (A . B) / (|A| * |B|)
            # sentence-transformers returns normalized vectors, so just dot product is enough
            scores = np.dot(anchor_embs, query_emb)
            max_score = np.max(scores)
            
            if max_score > best_score:
                best_score = max_score
                best_action = action
                
        # print(f"    🔍 Semantic Route: {best_action} (Conf: {best_score:.2f})")
        
        if best_score >= self.threshold:
            return best_action, float(best_score)
            
        return None, float(best_score)

# Singleton instance
_router_instance = None

def get_semantic_router():
    global _router_instance
    if _router_instance is None:
        _router_instance = SemanticRouter()
    return _router_instance
