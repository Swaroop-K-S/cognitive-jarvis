"""
Tool Registry Module
Provides a decorator-based system for registering tools that BRO can use.
Generates OpenAI-compatible function schemas for tool calling.
"""

from typing import Callable, Dict, Any, List
import inspect
import json

# Global registry of all tools
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, requires_confirmation: bool = False):
    """
    Decorator to register a function as a BRO tool.
    
    Args:
        name: The name of the tool (used by LLM to call it)
        description: Human-readable description of what the tool does
        requires_confirmation: If True, BRO will ask for user confirmation before executing
    
    Example:
        @tool("open_app", "Opens an application by name")
        def open_application(app_name: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Extract function signature for parameter info
        sig = inspect.signature(func)
        parameters = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            param_type = "string"  # Default type
            param_desc = f"The {param_name} parameter"
            
            # Try to get type hints
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == str:
                    param_type = "string"
                elif param.annotation == int:
                    param_type = "integer"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == float:
                    param_type = "number"
            
            parameters[param_name] = {
                "type": param_type,
                "description": param_desc
            }
            
            # If no default value, it's required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        # Register the tool
        _TOOL_REGISTRY[name] = {
            "function": func,
            "description": description,
            "requires_confirmation": requires_confirmation,
            "parameters": parameters,
            "required": required
        }
        
        return func
    return decorator


def get_all_tools() -> Dict[str, Dict[str, Any]]:
    """Returns the complete tool registry."""
    return _TOOL_REGISTRY


def get_tools_schema() -> List[Dict[str, Any]]:
    """
    Generates OpenAI-compatible tool schemas for all registered tools.
    This format is used for the 'tools' parameter in chat completions.
    """
    schemas = []
    for name, tool_info in _TOOL_REGISTRY.items():
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": tool_info["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool_info["parameters"],
                    "required": tool_info["required"]
                }
            }
        }
        schemas.append(schema)
    return schemas


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """
    Executes a registered tool by name with the given arguments.
    
    Args:
        name: The name of the tool to execute
        arguments: Dictionary of arguments to pass to the tool
        
    Returns:
        The result of the tool execution as a string
    """
    if name not in _TOOL_REGISTRY:
        return f"Error: Tool '{name}' not found"
    
    tool_info = _TOOL_REGISTRY[name]
    func = tool_info["function"]
    
    try:
        result = func(**arguments)
        return str(result)
    except Exception as e:
        return f"Error executing {name}: {str(e)}"


def tool_requires_confirmation(name: str) -> bool:
    """Check if a tool requires user confirmation before execution."""
    if name in _TOOL_REGISTRY:
        return _TOOL_REGISTRY[name].get("requires_confirmation", False)
    return False
