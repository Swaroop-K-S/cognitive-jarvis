"""
Jarvis/BRO - Advanced Cognitive AI Assistant
=============================================

A hybrid neuro-symbolic AI assistant with:
- Semantic intent routing (embeddings-based)
- TOML-based tool calling (robust parsing)
- Local STT with faster-whisper (5x faster)
- Smart Android control (XML-first)
- Memory system with ChromaDB

Quick Start:
    from jarvis import CognitiveBrain
    brain = CognitiveBrain()
    response = brain.process("open chrome")

For CLI:
    python -m jarvis.main
"""

__version__ = "2.0.0"
__author__ = "BRO Team"

# Core exports
from .llm import CognitiveBrain
from .cognitive import CognitiveEngine, CognitiveAction, SemanticRouter
from .tools import execute_tool, get_all_tools

__all__ = [
    "CognitiveBrain",
    "CognitiveEngine", 
    "CognitiveAction",
    "SemanticRouter",
    "execute_tool",
    "get_all_tools",
    "__version__",
]
