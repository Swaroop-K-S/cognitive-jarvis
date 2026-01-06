"""
BRO Smart Model Selector
Intelligently routes requests to the best specialist model.

Models:
- qwen2.5-coder:7b  → Coding tasks
- moondream         → Vision/image analysis  
- deepseek-r1:8b    → Math/logic reasoning
- llama3.2          → General conversation

Auto-unloads inactive models to save VRAM.
"""

import re
import json
import urllib.request
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """Types of tasks BRO can handle."""
    CODING = "coding"
    VISION = "vision"
    REASONING = "reasoning"
    GENERAL = "general"
    SYSTEM = "system"  # PC control, file ops


@dataclass
class ModelSpec:
    """Specification for a specialist model."""
    name: str           # Ollama model name
    vram: float         # Estimated VRAM usage in GB
    task_type: TaskType
    keywords: list      # Keywords that trigger this model
    priority: int       # Higher = preferred when multiple match
    alternatives: list = None  # Alternative model names if primary unavailable


# Model Registry - Multiple options per category
# Primary models + alternatives for flexibility

MODELS = {
    TaskType.CODING: ModelSpec(
        name="qwen2.5-coder:7b",
        vram=5.5,
        task_type=TaskType.CODING,
        keywords=[
            "code", "program", "script", "function", "class", "debug",
            "python", "javascript", "java", "c++", "rust", "go",
            "fix", "error", "bug", "implement", "write", "create function",
            "refactor", "optimize", "algorithm", "api", "database"
        ],
        priority=10,
        alternatives=["qwen2.5-coder:3b", "codellama:7b", "deepseek-coder:6.7b"]
    ),
    TaskType.VISION: ModelSpec(
        name="moondream",  # User has moondream installed
        vram=1.5,
        task_type=TaskType.VISION,
        keywords=[
            "image", "picture", "photo", "screenshot", "look at",
            "see", "show me", "what is this", "describe", "analyze image",
            "read this", "ocr", "scan", "camera", "screen"
        ],
        priority=10,
        alternatives=["llava", "llava:13b", "bakllava"]
    ),
    TaskType.REASONING: ModelSpec(
        name="deepseek-r1:8b",
        vram=6.0,
        task_type=TaskType.REASONING,
        keywords=[
            "math", "calculate", "solve", "equation", "formula",
            "logic", "puzzle", "riddle", "think", "reason",
            "why", "explain how", "step by step", "proof", "theorem"
        ],
        priority=8,
        alternatives=["gemma3:12b", "qwen2.5:7b", "phi3:medium"]
    ),
    TaskType.GENERAL: ModelSpec(
        name="gemma3",  # User has gemma3 installed (Google's latest!)
        vram=5.0,
        task_type=TaskType.GENERAL,
        keywords=[],  # Fallback for unmatched queries
        priority=1,
        alternatives=["gemma3:12b", "llama3.2", "qwen2.5:7b", "mistral:7b"]
    ),
    TaskType.SYSTEM: ModelSpec(
        name="llama3.2",  # User has this installed - lightweight for commands
        vram=4.0,
        task_type=TaskType.SYSTEM,
        keywords=[
            "open", "close", "run", "start", "launch", "folder",
            "file", "directory", "app", "application", "process",
            "screenshot", "system", "computer", "settings"
        ],
        priority=9,
        alternatives=["gemma3", "phi3:mini"]
    )
}

# Alternative model presets for different hardware configurations
MODEL_PRESETS = {
    "high_vram": {
        # For GPUs with 12GB+ VRAM
        TaskType.CODING: "qwen2.5-coder:14b",
        TaskType.VISION: "llava:13b",
        TaskType.REASONING: "deepseek-r1:14b",
        TaskType.GENERAL: "gemma3:12b",
        TaskType.SYSTEM: "qwen2.5:7b",
    },
    "medium_vram": {
        # For GPUs with 8GB VRAM (default)
        TaskType.CODING: "qwen2.5-coder:7b",
        TaskType.VISION: "moondream",
        TaskType.REASONING: "deepseek-r1:8b",
        TaskType.GENERAL: "gemma3",
        TaskType.SYSTEM: "llama3.2",
    },
    "low_vram": {
        # For GPUs with 4-6GB VRAM
        TaskType.CODING: "qwen2.5-coder:3b",
        TaskType.VISION: "moondream",
        TaskType.REASONING: "qwen2.5:3b",
        TaskType.GENERAL: "gemma3",
        TaskType.SYSTEM: "llama3.2",
    },
    "cpu_only": {
        # For CPU-only systems
        TaskType.CODING: "qwen2.5-coder:1.5b",
        TaskType.VISION: "moondream",
        TaskType.REASONING: "qwen2.5:1.5b",
        TaskType.GENERAL: "gemma3",
        TaskType.SYSTEM: "llama3.2",
    }
}

# Recommended models to install (user already has most of these!)
RECOMMENDED_MODELS = [
    ("gemma3", "General conversation - Google's latest, very capable"),
    ("gemma3:12b", "Larger general model - more capable, needs 8GB+ VRAM"),
    ("qwen2.5-coder:7b", "Coding specialist - Excellent at programming"),
    ("llama3.2", "Fast general - Quick responses, system commands"),
    ("moondream", "Vision - Lightweight image analysis"),
    ("llava", "Vision - More accurate image analysis (optional)"),
    ("deepseek-r1:8b", "Reasoning - Math and logic specialist"),
]


class ModelSelector:
    """
    Intelligently selects and manages specialist models.
    Automatically loads/unloads models to optimize VRAM.
    """
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.current_model: Optional[str] = None
        self.model_cache: Dict[str, bool] = {}  # Track which models are pulled
        
    def analyze_request(self, text: str, has_image: bool = False) -> TaskType:
        """
        Analyze a user request and determine the best task type.
        
        Args:
            text: The user's message
            has_image: Whether an image is attached
            
        Returns:
            The detected TaskType
        """
        text_lower = text.lower()
        
        # If image is attached, it's vision
        if has_image:
            return TaskType.VISION
        
        # Score each task type based on keyword matches
        scores: Dict[TaskType, int] = {}
        
        for task_type, spec in MODELS.items():
            score = 0
            for keyword in spec.keywords:
                if keyword in text_lower:
                    score += spec.priority
            scores[task_type] = score
        
        # Get the highest scoring type
        best_type = max(scores, key=lambda t: scores[t])
        
        # If no keywords matched, use general
        if scores[best_type] == 0:
            return TaskType.GENERAL
        
        return best_type
    
    def get_model_for_task(self, task_type: TaskType) -> ModelSpec:
        """Get the model spec for a task type."""
        return MODELS[task_type]
    
    def select_model(self, text: str, has_image: bool = False) -> Tuple[ModelSpec, TaskType]:
        """
        Select the best model for a request.
        
        Args:
            text: User's request
            has_image: Whether an image is attached
            
        Returns:
            Tuple of (ModelSpec, TaskType)
        """
        task_type = self.analyze_request(text, has_image)
        model = self.get_model_for_task(task_type)
        return model, task_type
    
    def ensure_model_loaded(self, model_name: str) -> bool:
        """
        Ensure a model is loaded and ready.
        Unloads other models if needed to free VRAM.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            True if model is ready
        """
        if self.current_model == model_name:
            return True
        
        # Unload current model to free VRAM
        if self.current_model:
            self._unload_model(self.current_model)
        
        # Load new model
        success = self._load_model(model_name)
        if success:
            self.current_model = model_name
        
        return success
    
    def _load_model(self, model_name: str) -> bool:
        """Load a model into Ollama."""
        try:
            # Check if model exists first
            if not self._model_exists(model_name):
                print(f"⚠️ Model {model_name} not found. Run: ollama pull {model_name}")
                return False
            
            # Ollama auto-loads models on first request
            # We just need to verify it's available
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def _unload_model(self, model_name: str) -> bool:
        """Unload a model from VRAM."""
        try:
            # Ollama API to unload model
            payload = json.dumps({"model": model_name, "keep_alive": 0}).encode()
            req = urllib.request.Request(
                f"{self.ollama_host}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=5)
            print(f"🔄 Unloaded {model_name} from VRAM")
            return True
        except:
            return False
    
    def _model_exists(self, model_name: str) -> bool:
        """Check if a model is pulled in Ollama."""
        if model_name in self.model_cache:
            return self.model_cache[model_name]
        
        try:
            req = urllib.request.Request(f"{self.ollama_host}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                # Also check full name with tag
                full_names = [m.get("name", "") for m in data.get("models", [])]
                exists = model_name in models or model_name in full_names
                self.model_cache[model_name] = exists
                return exists
        except:
            return False
    
    def list_available_models(self) -> list:
        """List all available Ollama models."""
        try:
            req = urllib.request.Request(f"{self.ollama_host}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                return [m.get("name", "") for m in data.get("models", [])]
        except:
            return []
    
    def get_vram_estimate(self, model_name: str) -> float:
        """Get estimated VRAM usage for a model."""
        for spec in MODELS.values():
            if spec.name == model_name:
                return spec.vram
        return 4.0  # Default estimate


def get_task_emoji(task_type: TaskType) -> str:
    """Get emoji for task type."""
    emojis = {
        TaskType.CODING: "💻",
        TaskType.VISION: "👁️",
        TaskType.REASONING: "🧠",
        TaskType.GENERAL: "💬",
        TaskType.SYSTEM: "⚙️"
    }
    return emojis.get(task_type, "🤖")
