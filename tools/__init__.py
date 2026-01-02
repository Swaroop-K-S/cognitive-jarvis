"""
JARVIS Tools Package
Contains all the tools/actions that JARVIS can perform.
"""

from .registry import tool, get_all_tools, execute_tool, get_tools_schema
from .pc_control import open_application, open_file, open_folder, take_screenshot, list_processes
from .file_ops import read_file, write_file, list_directory, search_files
from .browser import open_url, search_web

__all__ = [
    "tool",
    "get_all_tools",
    "execute_tool",
    "get_tools_schema",
    "open_application",
    "open_file", 
    "open_folder",
    "take_screenshot",
    "list_processes",
    "read_file",
    "write_file",
    "list_directory",
    "search_files",
    "open_url",
    "search_web",
]
