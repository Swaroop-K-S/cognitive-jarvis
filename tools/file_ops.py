"""
File Operations Tools
Provides tools for reading, writing, and searching files.
"""

import os
import glob
from typing import Optional

from .registry import tool


@tool("read_file", "Reads the contents of a text file")
def read_file(file_path: str, max_lines: int = 100) -> str:
    """
    Reads the contents of a text file.
    
    Args:
        file_path: The path to the file to read
        max_lines: Maximum number of lines to read (default 100)
        
    Returns:
        The file contents or an error message
    """
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        if not os.path.isfile(file_path):
            return f"Path is not a file: {file_path}"
        
        # Check file size to avoid reading huge files
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:  # 1 MB limit
            return f"File is too large ({file_size / 1024 / 1024:.1f} MB). Please specify a smaller file."
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if len(lines) > max_lines:
            content = ''.join(lines[:max_lines])
            return f"File contents (first {max_lines} lines of {len(lines)} total):\n\n{content}\n\n... (truncated)"
        else:
            return f"File contents:\n\n{''.join(lines)}"
    
    except PermissionError:
        return f"Permission denied: Cannot read {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool("write_file", "Writes content to a file. Use with caution!", requires_confirmation=True)
def write_file(file_path: str, content: str, append: bool = False) -> str:
    """
    Writes content to a file.
    
    Args:
        file_path: The path to the file to write
        content: The content to write
        append: If True, append to file instead of overwriting
        
    Returns:
        A success or error message
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        
        action = "Appended to" if append else "Wrote to"
        return f"{action} file: {file_path}"
    
    except PermissionError:
        return f"Permission denied: Cannot write to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@tool("list_directory", "Lists files and folders in a directory")
def list_directory(directory_path: str, show_hidden: bool = False) -> str:
    """
    Lists the contents of a directory.
    
    Args:
        directory_path: The path to the directory to list
        show_hidden: Whether to show hidden files (starting with .)
        
    Returns:
        A formatted list of directory contents
    """
    try:
        # Expand shortcuts
        folder_mappings = {
            "documents": os.path.expanduser("~\\Documents"),
            "downloads": os.path.expanduser("~\\Downloads"),
            "desktop": os.path.expanduser("~\\Desktop"),
            "pictures": os.path.expanduser("~\\Pictures"),
            "home": os.path.expanduser("~"),
            "~": os.path.expanduser("~"),
        }
        
        dir_lower = directory_path.lower()
        if dir_lower in folder_mappings:
            directory_path = folder_mappings[dir_lower]
        
        if not os.path.exists(directory_path):
            return f"Directory not found: {directory_path}"
        
        if not os.path.isdir(directory_path):
            return f"Path is not a directory: {directory_path}"
        
        items = os.listdir(directory_path)
        
        if not show_hidden:
            items = [item for item in items if not item.startswith('.')]
        
        # Separate directories and files
        dirs = []
        files = []
        
        for item in items:
            full_path = os.path.join(directory_path, item)
            if os.path.isdir(full_path):
                dirs.append(f"📁 {item}/")
            else:
                # Get file size
                try:
                    size = os.path.getsize(full_path)
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/1024/1024:.1f} MB"
                    files.append(f"📄 {item} ({size_str})")
                except:
                    files.append(f"📄 {item}")
        
        # Sort alphabetically
        dirs.sort()
        files.sort()
        
        result = f"Contents of {directory_path}:\n"
        result += "=" * 50 + "\n"
        
        if dirs:
            result += "\nFolders:\n"
            for d in dirs[:20]:  # Limit to 20 items
                result += f"  {d}\n"
            if len(dirs) > 20:
                result += f"  ... and {len(dirs) - 20} more folders\n"
        
        if files:
            result += "\nFiles:\n"
            for f in files[:30]:  # Limit to 30 items
                result += f"  {f}\n"
            if len(files) > 30:
                result += f"  ... and {len(files) - 30} more files\n"
        
        if not dirs and not files:
            result += "\n(Empty directory)\n"
        
        return result
    
    except PermissionError:
        return f"Permission denied: Cannot access {directory_path}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@tool("search_files", "Searches for files matching a pattern in a directory")
def search_files(pattern: str, directory: Optional[str] = None, recursive: bool = True) -> str:
    """
    Searches for files matching a pattern.
    
    Args:
        pattern: The search pattern (supports wildcards like *.txt, report*.pdf)
        directory: The directory to search in (defaults to user's home)
        recursive: Whether to search subdirectories
        
    Returns:
        A list of matching files
    """
    try:
        if directory is None:
            directory = os.path.expanduser("~")
        
        # Build the search pattern
        if recursive:
            search_pattern = os.path.join(directory, "**", pattern)
            matches = glob.glob(search_pattern, recursive=True)
        else:
            search_pattern = os.path.join(directory, pattern)
            matches = glob.glob(search_pattern)
        
        if not matches:
            return f"No files found matching pattern '{pattern}' in {directory}"
        
        # Limit results
        max_results = 25
        result = f"Found {len(matches)} file(s) matching '{pattern}':\n"
        result += "-" * 50 + "\n"
        
        for match in matches[:max_results]:
            # Make path relative if possible for readability
            try:
                rel_path = os.path.relpath(match, directory)
                result += f"  📄 {rel_path}\n"
            except:
                result += f"  📄 {match}\n"
        
        if len(matches) > max_results:
            result += f"\n... and {len(matches) - max_results} more files"
        
        return result
    
    except Exception as e:
        return f"Error searching files: {str(e)}"


@tool("get_file_info", "Gets detailed information about a file")
def get_file_info(file_path: str) -> str:
    """
    Gets detailed information about a file.
    
    Args:
        file_path: The path to the file
        
    Returns:
        Detailed file information
    """
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        stat = os.stat(file_path)
        
        # Format size
        size = stat.st_size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.2f} KB"
        elif size < 1024 * 1024 * 1024:
            size_str = f"{size/1024/1024:.2f} MB"
        else:
            size_str = f"{size/1024/1024/1024:.2f} GB"
        
        # Format times
        from datetime import datetime
        created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        accessed = datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")
        
        # Get extension
        _, ext = os.path.splitext(file_path)
        
        result = f"""
File Information: {os.path.basename(file_path)}
{'=' * 50}
Full Path: {os.path.abspath(file_path)}
Type: {'Directory' if os.path.isdir(file_path) else f'File ({ext or "no extension"})'}
Size: {size_str}
Created: {created}
Modified: {modified}
Last Accessed: {accessed}
"""
        return result
    
    except Exception as e:
        return f"Error getting file info: {str(e)}"
