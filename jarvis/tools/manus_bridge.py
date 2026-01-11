"""
Bro <-> OpenManus Bridge
Allows Jarvis to utilize OpenManus agents for complex research and planning tasks.
"""
import sys
import os
import asyncio
import logging

# Add OpenManus to path
current_dir = os.path.dirname(os.path.abspath(__file__)) # jarvis/jarvis/tools
jarvis_root = os.path.dirname(os.path.dirname(current_dir)) # jarvis
project_root = os.path.dirname(jarvis_root) # Code/New folder (3)
manus_path = os.path.join(project_root, "OpenManus")

if manus_path not in sys.path:
    sys.path.append(manus_path)

# Import Manus lazily to avoid startup errors if config is missing
MANUS_ERROR = None
try:
    # Check if we can find the module first
    import importlib.util
    spec = importlib.util.find_spec("app.agent.manus")
    if spec is None:
        raise ImportError(f"Module 'app.agent.manus' not found in {manus_path}")

    from app.agent.manus import Manus
    from app.logger import logger as manus_logger
    MANUS_AVAILABLE = True
except ImportError as e:
    MANUS_ERROR = str(e)
    print(f"⚠️ OpenManus bridge warning: {e}")
    MANUS_AVAILABLE = False
except Exception as e:
    MANUS_ERROR = str(e)
    print(f"⚠️ OpenManus bridge warning: {e}")
    MANUS_AVAILABLE = False


from .registry import tool

@tool("activate_research_mode", "Deep Research & Planning Agent (Manus). Use for complex tasks like 'Research X and write a report', 'Plan a travel itinerary', 'Analyze this market'.")
def run_manus_agent(task_description: str) -> str:
    """
    Delegates a complex task to the OpenManus Autonomous Agent.
    
    Args:
        task_description: The detailed request for the agent.
        
    Returns:
        The result or status of the agent's operation.
    """
    if not MANUS_AVAILABLE:
        return f"❌ OpenManus Error: {MANUS_ERROR}. Path: {manus_path}"

    print(f"🚀 ACTIVATING MANUS AGENT for: {task_description}")
    
    # Run the async agent in a synchronous wrapper for tool compatibility
    try:
        # We need to run this in a new event loop or thread if we are already in one?
        # Jarvis tools run in threads usually.
        result = asyncio.run(_run_async_manus(task_description))
        return result
    except Exception as e:
        return f"❌ Manus Agent Error: {e}"

async def _run_async_manus(prompt: str) -> str:
    """Async wrapper for Manus execution"""
    try:
        agent = await Manus.create()
        # Redirect logger or capture output? 
        # For now, we trust Manus to write files and we just return success.
        
        await agent.run(prompt)
        
        return f"✅ Research Task Completed. Check the 'OpenManus/workspace' folder for results."
    except Exception as e:
        return f"❌ Agent Crashed: {e}"
