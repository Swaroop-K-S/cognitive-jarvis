"""
BRO Advanced Browser Automation
Full browser control using Playwright for web tasks like booking, ordering, form-filling.
"""

import os
import sys
import time
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .registry import tool

# Try to import Playwright
PLAYWRIGHT_AVAILABLE = False
Browser = None
Page = None
Playwright = None
sync_playwright = None

try:
    from playwright.sync_api import sync_playwright as sp, Browser as B, Page as P, Playwright as PW
    sync_playwright = sp
    Browser = B
    Page = P
    Playwright = PW
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


class BrowserController:
    """
    Manages a persistent browser session for automation tasks.
    Uses Playwright for reliable cross-browser automation.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._playwright = None
        self._browser = None
        self._page = None
        self._initialized = True
    
    def _ensure_browser(self) -> bool:
        """Ensure browser is running."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        try:
            if self._playwright is None:
                self._playwright = sync_playwright().start()
            
            if self._browser is None or not self._browser.is_connected():
                # Launch visible browser (not headless) so user can see
                self._browser = self._playwright.chromium.launch(
                    headless=False,
                    args=['--start-maximized']
                )
            
            if self._page is None or self._page.is_closed():
                context = self._browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
                )
                self._page = context.new_page()
            
            return True
        
        except Exception as e:
            print(f"❌ Browser error: {e}")
            return False
    
    @property
    def page(self):
        if self._ensure_browser():
            return self._page
        return None
    
    def close(self):
        """Close the browser."""
        try:
            if self._page:
                self._page.close()
                self._page = None
            if self._browser:
                self._browser.close()
                self._browser = None
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
        except:
            pass


# Global browser controller
_browser = BrowserController()


def _get_page():
    """Get the current browser page."""
    if not PLAYWRIGHT_AVAILABLE:
        return None
    return _browser.page


@tool("navigate_to", "Navigates the browser to a URL and waits for page load. Use for 'go to google.com', 'open amazon', etc.")
def navigate_to(url: str) -> str:
    """
    Navigate to a URL in the browser.
    
    Args:
        url: The URL to navigate to
        
    Returns:
        Success message with page title
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed. Run: pip install playwright && playwright install chromium"
    
    page = _get_page()
    if not page:
        return "❌ Could not open browser"
    
    # Add https:// if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        title = page.title()
        return f"✓ Navigated to: {title}"
    except Exception as e:
        return f"❌ Navigation failed: {str(e)}"


@tool("click_element", "Clicks an element on the current page. Use for 'click the search button', 'click login', etc.")
def click_element(selector_or_text: str) -> str:
    """
    Click an element by CSS selector or visible text.
    
    Args:
        selector_or_text: CSS selector (e.g., '#submit') or visible text (e.g., 'Sign In')
        
    Returns:
        Success or failure message
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        # First try as CSS selector
        if selector_or_text.startswith(('#', '.', '[')) or '>' in selector_or_text:
            element = page.locator(selector_or_text).first
        else:
            # Try to find by text
            element = page.get_by_text(selector_or_text, exact=False).first
            
            # If not found, try by role (button, link, etc.)
            if not element.is_visible(timeout=1000):
                element = page.get_by_role("button", name=selector_or_text).first
            if not element.is_visible(timeout=1000):
                element = page.get_by_role("link", name=selector_or_text).first
        
        element.click(timeout=5000)
        time.sleep(0.5)  # Wait for any navigation/animation
        return f"✓ Clicked: {selector_or_text}"
    
    except Exception as e:
        return f"❌ Could not click '{selector_or_text}': {str(e)}"


@tool("type_in_field", "Types text into an input field. Use for 'type hello in the search box', 'enter my email', etc.")
def type_in_field(selector_or_label: str, text: str, press_enter: bool = False) -> str:
    """
    Type text into an input field.
    
    Args:
        selector_or_label: CSS selector, placeholder text, or label of the field
        text: The text to type
        press_enter: Whether to press Enter after typing
        
    Returns:
        Success or failure message
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        element = None
        
        # Try different strategies to find the input
        strategies = [
            lambda: page.locator(selector_or_label).first,  # CSS selector
            lambda: page.get_by_placeholder(selector_or_label).first,  # Placeholder
            lambda: page.get_by_label(selector_or_label).first,  # Label
            lambda: page.get_by_role("textbox", name=selector_or_label).first,  # Role
            lambda: page.get_by_role("searchbox").first,  # Search box
            lambda: page.locator(f'input[name*="{selector_or_label}" i]').first,  # Name contains
        ]
        
        for strategy in strategies:
            try:
                element = strategy()
                if element.is_visible(timeout=500):
                    break
            except:
                continue
        
        if element is None:
            return f"❌ Could not find field: {selector_or_label}"
        
        # Clear and type
        element.fill(text)
        
        if press_enter:
            element.press("Enter")
            time.sleep(0.5)
        
        return f"✓ Typed in {selector_or_label}"
    
    except Exception as e:
        return f"❌ Could not type in '{selector_or_label}': {str(e)}"


@tool("get_page_content", "Gets the visible text content of the current page. Use for 'read this page', 'what does it say', etc.")
def get_page_content(max_length: int = 2000) -> str:
    """
    Extract visible text from the current page.
    
    Args:
        max_length: Maximum characters to return
        
    Returns:
        The page's text content
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        # Get text from body, excluding scripts and styles
        text = page.evaluate("""
            () => {
                const body = document.body;
                const walker = document.createTreeWalker(
                    body,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: (node) => {
                            const parent = node.parentElement;
                            if (!parent) return NodeFilter.FILTER_REJECT;
                            const tag = parent.tagName.toLowerCase();
                            if (['script', 'style', 'noscript'].includes(tag)) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            if (node.textContent.trim()) {
                                return NodeFilter.FILTER_ACCEPT;
                            }
                            return NodeFilter.FILTER_REJECT;
                        }
                    }
                );
                
                const texts = [];
                while (walker.nextNode()) {
                    texts.push(walker.currentNode.textContent.trim());
                }
                return texts.join(' ');
            }
        """)
        
        text = ' '.join(text.split())[:max_length]
        return f"📄 Page content:\n{text}"
    
    except Exception as e:
        return f"❌ Could not read page: {str(e)}"


@tool("scroll_page", "Scrolls the page up, down, or to an element.")
def scroll_page(direction: str = "down", amount: int = 500) -> str:
    """
    Scroll the page.
    
    Args:
        direction: 'up', 'down', 'top', or 'bottom'
        amount: Pixels to scroll (for up/down)
        
    Returns:
        Success message
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        direction = direction.lower()
        
        if direction == "top":
            page.evaluate("window.scrollTo(0, 0)")
        elif direction == "bottom":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        elif direction == "up":
            page.evaluate(f"window.scrollBy(0, -{amount})")
        else:  # down
            page.evaluate(f"window.scrollBy(0, {amount})")
        
        return f"✓ Scrolled {direction}"
    
    except Exception as e:
        return f"❌ Scroll failed: {str(e)}"


@tool("take_page_screenshot", "Takes a screenshot of the current browser page.")
def take_page_screenshot(filename: str = None, full_page: bool = False) -> str:
    """
    Take a screenshot of the current page.
    
    Args:
        filename: Optional filename (default: auto-generated)
        full_page: Whether to capture the full scrollable page
        
    Returns:
        Path to saved screenshot
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pictures_folder = os.path.expanduser("~\\Pictures")
            filename = os.path.join(pictures_folder, f"browser_{timestamp}.png")
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        page.screenshot(path=filename, full_page=full_page)
        
        return f"✓ Screenshot saved: {filename}"
    
    except Exception as e:
        return f"❌ Screenshot failed: {str(e)}"


@tool("wait_for_element", "Waits for an element to appear on the page.")
def wait_for_element(selector_or_text: str, timeout: int = 10) -> str:
    """
    Wait for an element to appear.
    
    Args:
        selector_or_text: CSS selector or text to wait for
        timeout: Seconds to wait
        
    Returns:
        Success if found, failure if timeout
    """
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        if selector_or_text.startswith(('#', '.', '[')):
            page.wait_for_selector(selector_or_text, timeout=timeout * 1000)
        else:
            page.get_by_text(selector_or_text).wait_for(timeout=timeout * 1000)
        
        return f"✓ Found: {selector_or_text}"
    
    except Exception as e:
        return f"❌ Timeout waiting for '{selector_or_text}'"


@tool("go_back", "Goes back to the previous page in browser history.")
def go_back() -> str:
    """Go back one page in browser history."""
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        page.go_back()
        return f"✓ Went back to: {page.title()}"
    except Exception as e:
        return f"❌ Could not go back: {str(e)}"


@tool("close_browser", "Closes the automated browser window.")
def close_browser() -> str:
    """Close the browser."""
    try:
        _browser.close()
        return "✓ Browser closed"
    except Exception as e:
        return f"❌ Error closing browser: {str(e)}"


@tool("get_current_url", "Gets the current URL of the browser.")
def get_current_url() -> str:
    """Get the current page URL."""
    if not PLAYWRIGHT_AVAILABLE:
        return "❌ Playwright not installed"
    
    page = _get_page()
    if not page:
        return "❌ No browser page open"
    
    try:
        return f"📍 Current URL: {page.url}"
    except:
        return "❌ Could not get URL"


def browser_status() -> dict:
    """Get browser automation status."""
    return {
        "playwright_available": PLAYWRIGHT_AVAILABLE,
        "browser_open": _browser._browser is not None and _browser._browser.is_connected() if _browser else False,
    }
