"""
Browser Control Tools
Provides tools for web browsing and automation.
"""

import subprocess
import webbrowser
from urllib.parse import quote_plus

from .registry import tool


@tool("open_url", "Opens a URL in the default web browser")
def open_url(url: str) -> str:
    """
    Opens a URL in the default web browser.
    
    Args:
        url: The URL to open
        
    Returns:
        A success or error message
    """
    try:
        # Add https:// if no protocol specified
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        webbrowser.open(url)
        return f"Opened URL: {url}"
    
    except Exception as e:
        return f"Error opening URL: {str(e)}"


@tool("search_web", "Performs a web search using Google")
def search_web(query: str, engine: str = "google") -> str:
    """
    Performs a web search.
    
    Args:
        query: The search query
        engine: The search engine to use (google, bing, duckduckgo)
        
    Returns:
        A success message with the search URL
    """
    try:
        encoded_query = quote_plus(query)
        
        search_urls = {
            "google": f"https://www.google.com/search?q={encoded_query}",
            "bing": f"https://www.bing.com/search?q={encoded_query}",
            "duckduckgo": f"https://duckduckgo.com/?q={encoded_query}",
        }
        
        engine = engine.lower()
        if engine not in search_urls:
            engine = "google"
        
        url = search_urls[engine]
        webbrowser.open(url)
        
        return f"Searched for '{query}' using {engine.capitalize()}"
    
    except Exception as e:
        return f"Error performing search: {str(e)}"


@tool("open_youtube", "Opens YouTube with an optional search query")
def open_youtube(search_query: str = None) -> str:
    """
    Opens YouTube, optionally with a search query.
    
    Args:
        search_query: Optional search query to search on YouTube
        
    Returns:
        A success message
    """
    try:
        if search_query:
            encoded_query = quote_plus(search_query)
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            message = f"Opened YouTube search for: {search_query}"
        else:
            url = "https://www.youtube.com"
            message = "Opened YouTube"
        
        webbrowser.open(url)
        return message
    
    except Exception as e:
        return f"Error opening YouTube: {str(e)}"


@tool("open_github", "Opens GitHub with an optional search query")
def open_github(search_query: str = None) -> str:
    """
    Opens GitHub, optionally with a search query.
    
    Args:
        search_query: Optional search query for GitHub repositories
        
    Returns:
        A success message
    """
    try:
        if search_query:
            encoded_query = quote_plus(search_query)
            url = f"https://github.com/search?q={encoded_query}"
            message = f"Searched GitHub for: {search_query}"
        else:
            url = "https://github.com"
            message = "Opened GitHub"
        
        webbrowser.open(url)
        return message
    
    except Exception as e:
        return f"Error opening GitHub: {str(e)}"
