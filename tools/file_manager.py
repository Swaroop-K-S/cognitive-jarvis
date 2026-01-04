"""
BRO File Management Tools
Access and manage files on your PC - search, read, list, move, copy, delete.
All operations are local and secure.
"""

import os
import sys
import shutil
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.registry import tool

# =============================================================================
# COMMON PATHS
# =============================================================================

HOME = Path.home()
COMMON_FOLDERS = {
    "desktop": HOME / "Desktop",
    "documents": HOME / "Documents",
    "downloads": HOME / "Downloads",
    "pictures": HOME / "Pictures",
    "videos": HOME / "Videos",
    "music": HOME / "Music",
}


def _resolve_path(path: str) -> Path:
    """Resolve a path, handling shortcuts like 'desktop', 'downloads', etc."""
    path_lower = path.lower().strip()
    
    # Check if it's a shortcut
    if path_lower in COMMON_FOLDERS:
        return COMMON_FOLDERS[path_lower]
    
    # Handle ~ for home
    if path.startswith("~"):
        return HOME / path[1:].lstrip("/\\")
    
    return Path(path)


def _format_size(size_bytes: int) -> str:
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _format_time(timestamp: float) -> str:
    """Format timestamp to readable date."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


# =============================================================================
# FILE LISTING
# =============================================================================

@tool("list_files", "List files and folders in a directory.")
def list_files(path: str = ".", show_hidden: bool = False, limit: int = 50) -> str:
    """
    List files and folders in a directory.
    
    Args:
        path: Directory path (or shortcut: 'desktop', 'downloads', 'documents')
        show_hidden: Include hidden files (default False)
        limit: Maximum items to show (default 50)
        
    Returns:
        Formatted list of files and folders
    """
    try:
        target = _resolve_path(path)
        
        if not target.exists():
            return f"❌ Path not found: {target}"
        
        if not target.is_dir():
            return f"❌ Not a directory: {target}"
        
        items = []
        for item in target.iterdir():
            if not show_hidden and item.name.startswith('.'):
                continue
            
            try:
                stat = item.stat()
                is_dir = item.is_dir()
                size = stat.st_size if not is_dir else 0
                modified = stat.st_mtime
                
                items.append({
                    "name": item.name,
                    "is_dir": is_dir,
                    "size": size,
                    "modified": modified
                })
            except:
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": 0,
                    "modified": 0
                })
        
        # Sort: folders first, then by name
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        # Format output
        output = f"📁 {target}\n\n"
        
        folders = [i for i in items if i["is_dir"]][:limit]
        files = [i for i in items if not i["is_dir"]][:limit]
        
        if folders:
            output += "Folders:\n"
            for f in folders:
                output += f"  📁 {f['name']}/\n"
        
        if files:
            output += "\nFiles:\n"
            for f in files:
                size = _format_size(f["size"])
                output += f"  📄 {f['name']} ({size})\n"
        
        total = len(items)
        shown = len(folders) + len(files)
        if shown < total:
            output += f"\n... and {total - shown} more items"
        
        return output
        
    except Exception as e:
        return f"❌ Error listing files: {e}"


@tool("list_folder", "Quick shortcut to list common folders like Desktop, Downloads.")
def list_folder(folder: str) -> str:
    """
    List contents of common folders.
    
    Args:
        folder: One of: desktop, downloads, documents, pictures, videos, music
    """
    return list_files(folder)


# =============================================================================
# FILE SEARCH
# =============================================================================

@tool("search_files", "Search for files by name pattern.")
def search_files(
    pattern: str,
    path: str = ".",
    max_results: int = 20,
    include_subfolders: bool = True
) -> str:
    """
    Search for files matching a pattern.
    
    Args:
        pattern: Search pattern (e.g., "*.pdf", "report*", "*.jpg")
        path: Where to search (default: current folder)
        max_results: Maximum results to return
        include_subfolders: Search in subfolders too
        
    Returns:
        List of matching files
    """
    try:
        target = _resolve_path(path)
        
        if not target.exists():
            return f"❌ Path not found: {target}"
        
        results = []
        
        if include_subfolders:
            matches = target.rglob(pattern)
        else:
            matches = target.glob(pattern)
        
        for match in matches:
            if len(results) >= max_results:
                break
            try:
                stat = match.stat()
                results.append({
                    "path": str(match),
                    "name": match.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
            except:
                results.append({
                    "path": str(match),
                    "name": match.name,
                    "size": 0,
                    "modified": 0
                })
        
        if not results:
            return f"No files found matching '{pattern}' in {target}"
        
        output = f"🔍 Found {len(results)} file(s) matching '{pattern}':\n\n"
        for r in results:
            size = _format_size(r["size"])
            output += f"  📄 {r['name']} ({size})\n     {r['path']}\n"
        
        return output
        
    except Exception as e:
        return f"❌ Search error: {e}"


@tool("find_file", "Find a specific file by name anywhere in common folders.")
def find_file(filename: str) -> str:
    """
    Search for a file in common locations (Desktop, Documents, Downloads).
    
    Args:
        filename: The file name to search for
    """
    search_locations = ["desktop", "documents", "downloads", "pictures"]
    all_results = []
    
    for loc in search_locations:
        target = COMMON_FOLDERS.get(loc, HOME)
        try:
            for match in target.rglob(f"*{filename}*"):
                all_results.append(str(match))
                if len(all_results) >= 10:
                    break
        except:
            pass
        
        if len(all_results) >= 10:
            break
    
    if not all_results:
        return f"No files found containing '{filename}'"
    
    output = f"Found {len(all_results)} file(s):\n"
    for r in all_results:
        output += f"  📄 {r}\n"
    
    return output


# =============================================================================
# FILE READING
# =============================================================================

@tool("read_file", "Read the contents of a text file.")
def read_file(file_path: str, max_lines: int = 100) -> str:
    """
    Read contents of a text file.
    
    Args:
        file_path: Path to the file
        max_lines: Maximum lines to read (default 100)
        
    Returns:
        File contents
    """
    try:
        target = _resolve_path(file_path)
        
        if not target.exists():
            return f"❌ File not found: {target}"
        
        if not target.is_file():
            return f"❌ Not a file: {target}"
        
        # Check file size
        size = target.stat().st_size
        if size > 1024 * 1024:  # 1MB
            return f"❌ File too large ({_format_size(size)}). Use a text editor."
        
        # Try to read as text
        try:
            with open(target, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(target, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        if len(lines) > max_lines:
            content = "".join(lines[:max_lines])
            return f"📄 {target.name} (showing {max_lines}/{len(lines)} lines):\n\n{content}\n\n... truncated"
        else:
            content = "".join(lines)
            return f"📄 {target.name}:\n\n{content}"
        
    except Exception as e:
        return f"❌ Error reading file: {e}"


@tool("file_info", "Get detailed information about a file.")
def file_info(file_path: str) -> str:
    """
    Get detailed information about a file.
    
    Args:
        file_path: Path to the file
    """
    try:
        target = _resolve_path(file_path)
        
        if not target.exists():
            return f"❌ File not found: {target}"
        
        stat = target.stat()
        
        info = f"""📄 File Info: {target.name}

Path: {target}
Type: {"Directory" if target.is_dir() else "File"}
Size: {_format_size(stat.st_size)}
Created: {_format_time(stat.st_ctime)}
Modified: {_format_time(stat.st_mtime)}
Extension: {target.suffix or 'None'}
"""
        return info
        
    except Exception as e:
        return f"❌ Error: {e}"


# =============================================================================
# FILE OPERATIONS
# =============================================================================

@tool("copy_file", "Copy a file to another location.")
def copy_file(source: str, destination: str) -> str:
    """
    Copy a file to a new location.
    
    Args:
        source: Path to the source file
        destination: Destination path (file or folder)
    """
    try:
        src = _resolve_path(source)
        dst = _resolve_path(destination)
        
        if not src.exists():
            return f"❌ Source not found: {src}"
        
        if dst.is_dir():
            dst = dst / src.name
        
        shutil.copy2(src, dst)
        return f"✅ Copied: {src.name} → {dst}"
        
    except Exception as e:
        return f"❌ Copy failed: {e}"


@tool("move_file", "Move a file to another location.")
def move_file(source: str, destination: str) -> str:
    """
    Move a file to a new location.
    
    Args:
        source: Path to the source file
        destination: Destination path (file or folder)
    """
    try:
        src = _resolve_path(source)
        dst = _resolve_path(destination)
        
        if not src.exists():
            return f"❌ Source not found: {src}"
        
        if dst.is_dir():
            dst = dst / src.name
        
        shutil.move(str(src), str(dst))
        return f"✅ Moved: {src.name} → {dst}"
        
    except Exception as e:
        return f"❌ Move failed: {e}"


@tool("rename_file", "Rename a file.")
def rename_file(file_path: str, new_name: str) -> str:
    """
    Rename a file.
    
    Args:
        file_path: Path to the file
        new_name: New file name
    """
    try:
        src = _resolve_path(file_path)
        
        if not src.exists():
            return f"❌ File not found: {src}"
        
        dst = src.parent / new_name
        src.rename(dst)
        return f"✅ Renamed: {src.name} → {new_name}"
        
    except Exception as e:
        return f"❌ Rename failed: {e}"


@tool("delete_file", "Delete a file (moves to recycle bin if possible).")
def delete_file(file_path: str, confirm: bool = False) -> str:
    """
    Delete a file.
    
    Args:
        file_path: Path to the file
        confirm: Must be True to actually delete
    """
    try:
        target = _resolve_path(file_path)
        
        if not target.exists():
            return f"❌ File not found: {target}"
        
        if not confirm:
            size = target.stat().st_size
            return f"⚠️ This will delete: {target.name} ({_format_size(size)})\n\nTo confirm, call delete_file with confirm=True"
        
        # Try to use send2trash if available (safer)
        try:
            from send2trash import send2trash
            send2trash(str(target))
            return f"✅ Moved to Recycle Bin: {target.name}"
        except ImportError:
            # Permanent delete
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return f"✅ Deleted: {target.name}"
        
    except Exception as e:
        return f"❌ Delete failed: {e}"


@tool("create_folder", "Create a new folder.")
def create_folder(folder_path: str) -> str:
    """
    Create a new folder.
    
    Args:
        folder_path: Path for the new folder
    """
    try:
        target = _resolve_path(folder_path)
        target.mkdir(parents=True, exist_ok=True)
        return f"✅ Created folder: {target}"
    except Exception as e:
        return f"❌ Failed to create folder: {e}"


# =============================================================================
# DISK INFO
# =============================================================================

@tool("disk_usage", "Show disk space usage.")
def disk_usage(drive: str = "C:") -> str:
    """
    Show disk space usage.
    
    Args:
        drive: Drive letter (default C:)
    """
    try:
        if not drive.endswith(":"):
            drive = drive + ":"
        
        total, used, free = shutil.disk_usage(drive)
        
        return f"""💾 Disk Usage: {drive}

Total: {_format_size(total)}
Used:  {_format_size(used)} ({used * 100 // total}%)
Free:  {_format_size(free)} ({free * 100 // total}%)
"""
    except Exception as e:
        return f"❌ Error: {e}"


@tool("list_drives", "List available disk drives.")
def list_drives() -> str:
    """List available disk drives on Windows."""
    try:
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    total, used, free = shutil.disk_usage(drive)
                    drives.append(f"  💾 {letter}: - {_format_size(total)} total, {_format_size(free)} free")
                except:
                    drives.append(f"  💾 {letter}: - (not accessible)")
        
        return "Available Drives:\n" + "\n".join(drives)
    except Exception as e:
        return f"❌ Error: {e}"


# =============================================================================
# RECENT FILES
# =============================================================================

@tool("recent_files", "Show recently modified files.")
def recent_files(folder: str = "downloads", limit: int = 10) -> str:
    """
    Show recently modified files in a folder.
    
    Args:
        folder: Folder to check (default: downloads)
        limit: Number of files to show
    """
    try:
        target = _resolve_path(folder)
        
        if not target.exists():
            return f"❌ Folder not found: {target}"
        
        files = []
        for item in target.iterdir():
            if item.is_file():
                try:
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
                except:
                    pass
        
        # Sort by modified time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        output = f"📅 Recent files in {folder}:\n\n"
        for f in files[:limit]:
            time_str = _format_time(f["modified"])
            size = _format_size(f["size"])
            output += f"  📄 {f['name']} ({size}) - {time_str}\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error: {e}"


# =============================================================================
# STATUS
# =============================================================================

def file_tools_status() -> dict:
    """Get file tools status."""
    return {
        "available": True,
        "home": str(HOME),
        "common_folders": list(COMMON_FOLDERS.keys())
    }
