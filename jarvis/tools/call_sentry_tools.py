"""
BRO Call Sentry Tools
Voice commands to control and query the call screening system.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.registry import tool

# Import call sentry modules
try:
    from call_sentry import (
        set_mode as _set_mode,
        get_mode as _get_mode,
        get_call_summary as _get_call_summary,
        get_greeting,
        PERSONALITIES,
        CallHistoryManager
    )
    CALL_SENTRY_AVAILABLE = True
except ImportError:
    CALL_SENTRY_AVAILABLE = False


@tool("set_call_mode", "Switch call screening personality. Use 'professional', 'friendly', or 'guard'.")
def set_call_mode(mode: str) -> str:
    """
    Switch the call screening personality mode.
    
    Args:
        mode: One of 'professional', 'friendly', or 'guard'
        
    Returns:
        Confirmation message
    """
    if not CALL_SENTRY_AVAILABLE:
        return "❌ Call Sentry not available"
    
    return _set_mode(mode)


@tool("get_call_mode", "Get the current call screening mode.")
def get_call_mode() -> str:
    """Get the current call screening mode."""
    if not CALL_SENTRY_AVAILABLE:
        return "❌ Call Sentry not available"
    
    return _get_mode()


@tool("get_call_summary", "Get a summary of today's screened calls.")
def get_call_summary() -> str:
    """
    Get a summary of calls that were screened today.
    
    Returns:
        Summary of calls with caller info and action items
    """
    if not CALL_SENTRY_AVAILABLE:
        return "❌ Call Sentry not available"
    
    return _get_call_summary()


@tool("list_call_modes", "Show all available call screening personalities.")
def list_call_modes() -> str:
    """List all available call screening modes."""
    if not CALL_SENTRY_AVAILABLE:
        return "❌ Call Sentry not available"
    
    output = "📞 Available Call Sentry Modes:\n"
    for mode_name, config in PERSONALITIES.items():
        output += f"\n• {mode_name.upper()} ({config.name})\n"
        output += f"  Greeting: \"{config.greeting[:50]}...\"\n"
    
    return output


@tool("start_call_sentry", "Start the call screening server.")
def start_call_sentry() -> str:
    """
    Provides instructions to start the call sentry server.
    
    Returns:
        Instructions for starting the server
    """
    return """🚀 To start Call Sentry:

1. Open a new terminal
2. Run: cd BRO/call_sentry && python server.py
3. In another terminal: ngrok http 5000
4. Configure Twilio webhook with the ngrok URL

The server will then be ready to receive calls!"""


# Export for tools module
def call_sentry_status() -> dict:
    """Get status of call sentry system."""
    return {
        "available": CALL_SENTRY_AVAILABLE,
        "current_mode": _get_mode() if CALL_SENTRY_AVAILABLE else None,
    }
