"""
BRO Reminders & Notes
Quick notes and time-based reminders.
"""

import os
import sys
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try TOML
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w
    TOML_WRITE = True
except ImportError:
    TOML_WRITE = False


# =============================================================================
# STORAGE
# =============================================================================

DATA_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "bro_memory"
NOTES_FILE = DATA_DIR / "notes.toml"
REMINDERS_FILE = DATA_DIR / "reminders.toml"


def _load_toml(path: Path, default: dict) -> dict:
    """Load TOML file."""
    try:
        if path.exists() and tomllib:
            with open(path, "rb") as f:
                return tomllib.load(f)
    except:
        pass
    return default.copy()


def _save_toml(path: Path, data: dict):
    """Save TOML file."""
    DATA_DIR.mkdir(exist_ok=True)
    
    if TOML_WRITE:
        with open(path, "wb") as f:
            tomli_w.dump(data, f)
    else:
        # Fallback: simple TOML
        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    lines.append(f"[[{key}]]")
                    for k, v in item.items():
                        if isinstance(v, str):
                            lines.append(f'{k} = "{v}"')
                        elif isinstance(v, bool):
                            lines.append(f'{k} = {"true" if v else "false"}')
                        else:
                            lines.append(f'{k} = {v}')
                    lines.append("")
            else:
                if isinstance(value, str):
                    lines.append(f'{key} = "{value}"')
                else:
                    lines.append(f'{key} = {value}')
        
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


# =============================================================================
# NOTES
# =============================================================================

class NoteManager:
    """Quick notes manager."""
    
    def __init__(self):
        self.notes = _load_toml(NOTES_FILE, {"items": []}).get("items", [])
    
    def add(self, content: str, tags: List[str] = None) -> str:
        """Add a quick note."""
        note = {
            "id": len(self.notes) + 1,
            "content": content,
            "tags": ",".join(tags) if tags else "",
            "created": datetime.now().isoformat(),
            "pinned": False
        }
        self.notes.append(note)
        _save_toml(NOTES_FILE, {"items": self.notes})
        return f"📝 Note saved! (#{note['id']})"
    
    def list_all(self, limit: int = 10) -> str:
        """List recent notes."""
        if not self.notes:
            return "📝 No notes yet. Add one with: note('your note here')"
        
        output = "📝 YOUR NOTES\n" + "="*40 + "\n\n"
        
        # Show pinned first, then recent
        pinned = [n for n in self.notes if n.get("pinned")]
        recent = [n for n in self.notes if not n.get("pinned")][-limit:]
        
        for note in pinned + recent:
            pin = "📌 " if note.get("pinned") else ""
            tags = f" [{note['tags']}]" if note.get("tags") else ""
            output += f"{pin}#{note['id']}: {note['content']}{tags}\n"
        
        return output
    
    def search(self, query: str) -> str:
        """Search notes."""
        results = [n for n in self.notes if query.lower() in n["content"].lower()]
        
        if not results:
            return f"🔍 No notes found for: {query}"
        
        output = f"🔍 Notes matching '{query}':\n\n"
        for note in results:
            output += f"#{note['id']}: {note['content']}\n"
        
        return output
    
    def delete(self, note_id: int) -> str:
        """Delete a note."""
        self.notes = [n for n in self.notes if n["id"] != note_id]
        _save_toml(NOTES_FILE, {"items": self.notes})
        return f"🗑️ Deleted note #{note_id}"
    
    def pin(self, note_id: int) -> str:
        """Pin a note."""
        for note in self.notes:
            if note["id"] == note_id:
                note["pinned"] = not note.get("pinned", False)
                _save_toml(NOTES_FILE, {"items": self.notes})
                return f"📌 {'Pinned' if note['pinned'] else 'Unpinned'} note #{note_id}"
        return f"Note #{note_id} not found"


# =============================================================================
# REMINDERS
# =============================================================================

class ReminderManager:
    """Time-based reminders."""
    
    def __init__(self):
        self.reminders = _load_toml(REMINDERS_FILE, {"items": []}).get("items", [])
        self._checker_thread = None
        self._running = False
    
    def add(self, message: str, when: str) -> str:
        """
        Add a reminder.
        
        when can be:
        - "5m" or "5 minutes" - in 5 minutes
        - "1h" or "1 hour" - in 1 hour
        - "tomorrow 9am" - tomorrow at 9am
        - "3pm" - today at 3pm
        """
        remind_time = self._parse_time(when)
        if not remind_time:
            return f"❌ Couldn't understand time: {when}"
        
        reminder = {
            "id": len(self.reminders) + 1,
            "message": message,
            "time": remind_time.isoformat(),
            "created": datetime.now().isoformat(),
            "done": False
        }
        self.reminders.append(reminder)
        _save_toml(REMINDERS_FILE, {"items": self.reminders})
        
        time_str = remind_time.strftime("%I:%M %p on %b %d")
        return f"⏰ Reminder set for {time_str}: {message}"
    
    def _parse_time(self, when: str) -> Optional[datetime]:
        """Parse time string to datetime."""
        now = datetime.now()
        when = when.lower().strip()
        
        # Relative times: "5m", "1h", "30min"
        import re
        match = re.match(r'(\d+)\s*(m|min|minutes?|h|hr|hours?)', when)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            if unit.startswith('m'):
                return now + timedelta(minutes=amount)
            else:
                return now + timedelta(hours=amount)
        
        # Absolute times: "3pm", "15:00"
        match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', when)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2) or 0)
            meridian = match.group(3)
            
            if meridian == "pm" and hour < 12:
                hour += 12
            elif meridian == "am" and hour == 12:
                hour = 0
            
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target < now:
                target += timedelta(days=1)
            return target
        
        # "tomorrow"
        if "tomorrow" in when:
            target = now + timedelta(days=1)
            match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', when)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2) or 0)
                if match.group(3) == "pm" and hour < 12:
                    hour += 12
                target = target.replace(hour=hour, minute=minute, second=0, microsecond=0)
            else:
                target = target.replace(hour=9, minute=0, second=0, microsecond=0)
            return target
        
        return None
    
    def list_all(self) -> str:
        """List pending reminders."""
        pending = [r for r in self.reminders if not r.get("done")]
        
        if not pending:
            return "⏰ No pending reminders"
        
        output = "⏰ REMINDERS\n" + "="*40 + "\n\n"
        
        for r in sorted(pending, key=lambda x: x["time"]):
            time_obj = datetime.fromisoformat(r["time"])
            time_str = time_obj.strftime("%I:%M %p, %b %d")
            output += f"#{r['id']}: {r['message']}\n   ⏰ {time_str}\n\n"
        
        return output
    
    def complete(self, reminder_id: int) -> str:
        """Mark reminder as done."""
        for r in self.reminders:
            if r["id"] == reminder_id:
                r["done"] = True
                _save_toml(REMINDERS_FILE, {"items": self.reminders})
                return f"✅ Completed: {r['message']}"
        return f"Reminder #{reminder_id} not found"
    
    def delete(self, reminder_id: int) -> str:
        """Delete a reminder."""
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
        _save_toml(REMINDERS_FILE, {"items": self.reminders})
        return f"🗑️ Deleted reminder #{reminder_id}"
    
    def check_due(self) -> List[Dict]:
        """Check for due reminders."""
        now = datetime.now()
        due = []
        
        for r in self.reminders:
            if r.get("done"):
                continue
            
            remind_time = datetime.fromisoformat(r["time"])
            if remind_time <= now:
                due.append(r)
                r["done"] = True
        
        if due:
            _save_toml(REMINDERS_FILE, {"items": self.reminders})
        
        return due
    
    def notify_due(self):
        """Show notification for due reminders."""
        due = self.check_due()
        for r in due:
            print(f"\n🔔 REMINDER: {r['message']}")
            # Try Windows toast notification
            try:
                import subprocess
                msg = r['message'].replace('"', "'")
                subprocess.run([
                    "powershell", "-Command",
                    f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; '
                    f'$template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02; '
                    f'$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template); '
                    f'$xml.GetElementsByTagName("text")[0].AppendChild($xml.CreateTextNode("BRO Reminder")) > $null; '
                    f'$xml.GetElementsByTagName("text")[1].AppendChild($xml.CreateTextNode("{msg}")) > $null; '
                    f'$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); '
                    f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("BRO").Show($toast)'
                ], capture_output=True)
            except:
                pass


# =============================================================================
# GLOBAL INSTANCES
# =============================================================================

_notes = NoteManager()
_reminders = ReminderManager()


# Convenience functions
def note(content: str, tags: List[str] = None) -> str:
    """Add a quick note."""
    return _notes.add(content, tags)


def notes(limit: int = 10) -> str:
    """List notes."""
    return _notes.list_all(limit)


def search_notes(query: str) -> str:
    """Search notes."""
    return _notes.search(query)


def delete_note(note_id: int) -> str:
    """Delete a note."""
    return _notes.delete(note_id)


def remind(message: str, when: str) -> str:
    """Set a reminder."""
    return _reminders.add(message, when)


def reminders() -> str:
    """List reminders."""
    return _reminders.list_all()


def complete_reminder(reminder_id: int) -> str:
    """Complete a reminder."""
    return _reminders.complete(reminder_id)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Notes & Reminders")
    parser.add_argument("command", choices=["note", "notes", "remind", "reminders", "check"])
    parser.add_argument("args", nargs="*")
    
    args = parser.parse_args()
    
    if args.command == "note":
        print(note(" ".join(args.args)))
    elif args.command == "notes":
        print(notes())
    elif args.command == "remind":
        # remind "message" "when"
        if len(args.args) >= 2:
            print(remind(args.args[0], args.args[1]))
        else:
            print("Usage: remind 'message' 'when'")
    elif args.command == "reminders":
        print(reminders())
    elif args.command == "check":
        _reminders.notify_due()
