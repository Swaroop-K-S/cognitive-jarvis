"""
BRO Memory System
Long-term memory using ChromaDB + sentence-transformers.
Runs on CPU to save GPU VRAM for the LLM.
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class BROMemory:
    """
    Long-term memory for BRO using ChromaDB.
    Stores conversations, facts, and user preferences.
    """
    
    def __init__(self, memory_path: str = None):
        """
        Initialize the memory system.
        
        Args:
            memory_path: Path to store the persistent memory database
        """
        self.memory_path = memory_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "BRO_memory"
        )
        self.client = None
        self.collection = None
        self.embedder = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize the memory system."""
        if not CHROMADB_AVAILABLE:
            print("❌ ChromaDB not installed. Run: pip install chromadb")
            return False
        
        try:
            # Create persistent ChromaDB client
            os.makedirs(self.memory_path, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.memory_path)
            
            # Create or get the memories collection
            self.collection = self.client.get_or_create_collection(
                name="BRO_memories",
                metadata={"description": "BRO long-term memory"}
            )
            
            # Initialize sentence transformer for embeddings (runs on CPU)
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"❌ Memory init error: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if memory system is available."""
        return self._initialized and self.collection is not None
    
    def remember(self, content: str, memory_type: str = "conversation", 
                 metadata: Dict[str, Any] = None) -> bool:
        """
        Store a memory.
        
        Args:
            content: The text content to remember
            memory_type: Type of memory (conversation, fact, preference, task)
            metadata: Additional metadata to store
            
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            # Generate unique ID
            memory_id = hashlib.md5(f"{content}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
            
            # Build metadata
            meta = {
                "type": memory_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Add to collection
            self.collection.add(
                documents=[content],
                ids=[memory_id],
                metadatas=[meta]
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Memory save error: {e}")
            return False
    
    def recall(self, query: str, n_results: int = 3, 
               memory_type: str = None) -> List[Dict[str, Any]]:
        """
        Recall relevant memories.
        
        Args:
            query: The search query
            n_results: Maximum number of results
            memory_type: Filter by memory type (optional)
            
        Returns:
            List of matching memories with their metadata
        """
        if not self.is_available():
            return []
        
        try:
            # Build filter if type specified
            where = {"type": memory_type} if memory_type else None
            
            # Query the collection
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Format results
            memories = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    memories.append({
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results.get('distances') else 0
                    })
            
            return memories
            
        except Exception as e:
            print(f"❌ Memory recall error: {e}")
            return []
    
    def recall_text(self, query: str, n_results: int = 3) -> str:
        """
        Recall memories and return as formatted text.
        
        Args:
            query: The search query
            n_results: Maximum number of results
            
        Returns:
            Formatted string of memories
        """
        memories = self.recall(query, n_results)
        if not memories:
            return ""
        
        return "\n".join([m["content"] for m in memories])
    
    def remember_fact(self, fact: str) -> bool:
        """Store a fact about the user or world."""
        return self.remember(fact, memory_type="fact")
    
    def remember_preference(self, preference: str) -> bool:
        """Store a user preference."""
        return self.remember(preference, memory_type="preference")
    
    def remember_conversation(self, user_msg: str, assistant_msg: str) -> bool:
        """Store a conversation exchange."""
        content = f"User: {user_msg}\nBRO: {assistant_msg}"
        return self.remember(content, memory_type="conversation")
    
    def get_stats(self) -> Dict[str, int]:
        """Get memory statistics."""
        if not self.is_available():
            return {"total": 0}
        
        try:
            count = self.collection.count()
            return {"total": count}
        except:
            return {"total": 0}
    
    def clear_all(self) -> bool:
        """Clear all memories (use with caution!)."""
        if not self.client:
            return False
        
        try:
            self.client.delete_collection("BRO_memories")
            self.collection = self.client.get_or_create_collection(
                name="BRO_memories",
                metadata={"description": "BRO long-term memory"}
            )
            return True
        except:
            return False


# Global memory instance
_memory: Optional[BROMemory] = None


def get_memory() -> BROMemory:
    """Get the global memory instance."""
    global _memory
    if _memory is None:
        _memory = BROMemory()
        _memory.initialize()
    return _memory
