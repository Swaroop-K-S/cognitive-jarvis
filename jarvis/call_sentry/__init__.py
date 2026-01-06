"""
BRO Call Sentry Package
100% Local AI Call Screening - No cloud services!
"""

from .local_sentry import (
    PERSONALITIES,
    CURRENT_MODE,
    set_mode,
    get_mode,
    get_call_summary,
    LocalCallSentry,
    CallRecord,
    CallHistoryManager,
    VOSK_AVAILABLE,
    TTS_AVAILABLE
)

# Keep original for backwards compatibility
from .call_sentry import (
    generate_response,
    generate_summary,
    demo_call
)

__all__ = [
    "PERSONALITIES",
    "CURRENT_MODE", 
    "set_mode",
    "get_mode",
    "get_call_summary",
    "LocalCallSentry",
    "CallRecord",
    "CallHistoryManager",
    "generate_response",
    "generate_summary",
    "demo_call",
    "VOSK_AVAILABLE",
    "TTS_AVAILABLE"
]
