"""
BRO Music Player
Control music playback on your PC and phone.
"""

import os
import sys
import subprocess
import webbrowser
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# MUSIC CONTROL (Windows)
# =============================================================================

def play_pause() -> str:
    """Toggle play/pause on current media."""
    try:
        # Use PowerShell to send media keys
        subprocess.run([
            "powershell", "-Command",
            "(New-Object -ComObject WScript.Shell).SendKeys([char]179)"
        ], capture_output=True)
        return "⏯️ Toggled play/pause"
    except Exception as e:
        return f"Error: {e}"


def next_track() -> str:
    """Skip to next track."""
    try:
        subprocess.run([
            "powershell", "-Command",
            "(New-Object -ComObject WScript.Shell).SendKeys([char]176)"
        ], capture_output=True)
        return "⏭️ Next track"
    except Exception as e:
        return f"Error: {e}"


def previous_track() -> str:
    """Go to previous track."""
    try:
        subprocess.run([
            "powershell", "-Command",
            "(New-Object -ComObject WScript.Shell).SendKeys([char]177)"
        ], capture_output=True)
        return "⏮️ Previous track"
    except Exception as e:
        return f"Error: {e}"


def volume_up(amount: int = 10) -> str:
    """Increase volume."""
    try:
        for _ in range(amount // 2):
            subprocess.run([
                "powershell", "-Command",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"
            ], capture_output=True)
        return f"🔊 Volume up by {amount}%"
    except Exception as e:
        return f"Error: {e}"


def volume_down(amount: int = 10) -> str:
    """Decrease volume."""
    try:
        for _ in range(amount // 2):
            subprocess.run([
                "powershell", "-Command",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"
            ], capture_output=True)
        return f"🔉 Volume down by {amount}%"
    except Exception as e:
        return f"Error: {e}"


def mute() -> str:
    """Toggle mute."""
    try:
        subprocess.run([
            "powershell", "-Command",
            "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
        ], capture_output=True)
        return "🔇 Toggled mute"
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# MUSIC STREAMING
# =============================================================================

def open_spotify(search: str = None) -> str:
    """Open Spotify, optionally search for something."""
    try:
        if search:
            url = f"https://open.spotify.com/search/{search.replace(' ', '%20')}"
            webbrowser.open(url)
            return f"🎵 Searching Spotify for: {search}"
        else:
            subprocess.run(["start", "spotify:"], shell=True)
            return "🎵 Opening Spotify..."
    except:
        webbrowser.open("https://open.spotify.com")
        return "🎵 Opening Spotify in browser..."


def open_youtube_music(search: str = None) -> str:
    """Open YouTube Music."""
    if search:
        url = f"https://music.youtube.com/search?q={search.replace(' ', '+')}"
    else:
        url = "https://music.youtube.com"
    webbrowser.open(url)
    return f"🎵 Opening YouTube Music{' - ' + search if search else ''}..."


def play_on_youtube(song: str) -> str:
    """Search and play a song on YouTube."""
    url = f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
    webbrowser.open(url)
    return f"🎵 Searching YouTube for: {song}"


# =============================================================================
# PHONE MUSIC CONTROL
# =============================================================================

def phone_music_control(action: str = "play") -> str:
    """Control music on connected phone."""
    try:
        from tools.android_control import AndroidController
        ctrl = AndroidController()
        if not ctrl.connect():
            return "❌ Phone not connected"
        
        key_map = {
            "play": 85,      # KEYCODE_MEDIA_PLAY_PAUSE
            "pause": 85,
            "next": 87,      # KEYCODE_MEDIA_NEXT
            "previous": 88,  # KEYCODE_MEDIA_PREVIOUS
            "stop": 86,      # KEYCODE_MEDIA_STOP
        }
        
        keycode = key_map.get(action.lower(), 85)
        ctrl.device.shell(f"input keyevent {keycode}")
        
        return f"📱 Phone: {action.capitalize()}"
    except Exception as e:
        return f"Error: {e}"


# =============================================================================
# CONVENIENCE
# =============================================================================

def play_music(query: str = None, platform: str = "youtube") -> str:
    """Play music from a query."""
    if not query:
        return play_pause()
    
    platform = platform.lower()
    if platform == "spotify":
        return open_spotify(query)
    elif platform == "youtube music" or platform == "ytmusic":
        return open_youtube_music(query)
    else:
        return play_on_youtube(query)


def music_status() -> str:
    """Get music control status."""
    return """
🎵 BRO MUSIC CONTROL
====================

PC Controls:
  • play_pause() - Toggle playback
  • next_track() - Next song
  • previous_track() - Previous song
  • volume_up(10) - Increase volume
  • volume_down(10) - Decrease volume
  • mute() - Toggle mute

Streaming:
  • play_music("song name") - Search on YouTube
  • play_music("song", "spotify") - Search on Spotify
  • open_spotify() - Open Spotify
  • open_youtube_music() - Open YT Music

Phone:
  • phone_music_control("play") - Control phone music
"""


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Music Control")
    parser.add_argument("command", nargs="?", default="status",
                       choices=["status", "play", "pause", "next", "prev", "up", "down", "mute", "search"])
    parser.add_argument("args", nargs="*")
    
    args = parser.parse_args()
    
    if args.command == "status":
        print(music_status())
    elif args.command in ["play", "pause"]:
        print(play_pause())
    elif args.command == "next":
        print(next_track())
    elif args.command == "prev":
        print(previous_track())
    elif args.command == "up":
        print(volume_up())
    elif args.command == "down":
        print(volume_down())
    elif args.command == "mute":
        print(mute())
    elif args.command == "search":
        query = " ".join(args.args) or "chill music"
        print(play_music(query))
