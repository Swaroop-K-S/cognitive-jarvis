
import os
import shutil
from pathlib import Path
from .registry import tool

@tool("clear_memory", "Clears all long-term memory and conversation history (Use with CAUTION)")
def clear_memory(confirm: bool = False) -> str:
    """
    Wipes all AI memory.
    
    Args:
        confirm: Must be set to True to execute.
        
    Returns:
        Status message.
    """
    if not confirm:
        return "⚠️ To clear memory, you must call clear_memory(confirm=True)."
        
    log = []
    
    # 1. Clear ChromaDB (Long-term Memory)
    try:
        from memory.memory import get_memory
        mem = get_memory()
        if mem.clear_all():
            log.append("✅ ChromaDB memory wiped.")
        else:
            log.append("⚠️ ChromaDB lookup failed (maybe empty).")
    except Exception as e:
        log.append(f"❌ ChromaDB error: {e}")

    # 2. Clear TOML Files (Personality Memory)
    try:
        # Path is usually ../bro_memory relative to this file
        # jarvis/tools/memory_tools.py -> jarvis/ -> bro_memory
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        memory_dir = os.path.join(root_dir, "bro_memory")
        
        if os.path.exists(memory_dir):
            files = [f for f in os.listdir(memory_dir) if f.endswith('.toml')]
            for f in files:
                os.remove(os.path.join(memory_dir, f))
            log.append(f"✅ Deleted {len(files)} TOML memory files.")
        else:
            log.append("ℹ️ No TOML memory directory found.")
            
    except Exception as e:
        log.append(f"❌ TOML file error: {e}")
        
    return "\n".join(log)
