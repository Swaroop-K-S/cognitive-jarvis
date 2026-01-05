"""
BRO Tools Package
Contains all the tools/actions that BRO can perform.
"""

from .registry import tool, get_all_tools, execute_tool, get_tools_schema

# PC Control Tools
from .pc_control import (
    open_application, close_application, check_app_running, restart_application,
    open_file, open_folder, take_screenshot, list_processes,
    type_text, press_key, get_system_info
)

# File Operations
from .file_ops import read_file, write_file, list_directory, search_files

# Browser Tools (basic)
from .browser import open_url, search_web, open_youtube, open_github

# Vision Tools (NEW - requires LLaVA)
from .vision import (
    analyze_screen, find_on_screen, read_screen_text,
    describe_image, save_screenshot, vision_status
)

# Web Automation Tools (NEW - requires Playwright)
from .web_automation import (
    navigate_to, click_element, type_in_field,
    get_page_content, scroll_page, take_page_screenshot,
    wait_for_element, go_back, close_browser, get_current_url,
    browser_status
)

# File Conversion Tools (NEW)
from .file_convert import (
    convert_image, resize_image, compress_image, images_to_pdf,
    pdf_to_text, merge_pdfs, docx_to_text,
    ppt_to_images, ppt_to_text, file_convert_status
)

# Memory Tools
from .memory_tools import clear_memory

__all__ = [
    # Registry
    "tool", "get_all_tools", "execute_tool", "get_tools_schema",
    
    # PC Control
    "open_application", "close_application", "check_app_running", "restart_application",
    "open_file", "open_folder", "take_screenshot", "list_processes",
    "type_text", "press_key", "get_system_info",
    
    # File Ops
    "read_file", "write_file", "list_directory", "search_files",
    
    # Browser
    "open_url", "search_web", "open_youtube", "open_github",
    
    # Vision (NEW)
    "analyze_screen", "find_on_screen", "read_screen_text",
    "describe_image", "save_screenshot", "vision_status",
    
    # Web Automation (NEW)
    "navigate_to", "click_element", "type_in_field",
    "get_page_content", "scroll_page", "take_page_screenshot",
    "wait_for_element", "go_back", "close_browser", "get_current_url",
    "browser_status",
    
    # File Conversion (NEW)
    "convert_image", "resize_image", "compress_image", "images_to_pdf",
    "pdf_to_text", "merge_pdfs", "docx_to_text",
    "ppt_to_images", "ppt_to_text", "file_convert_status",
    
    # Memory
    "clear_memory",
]
