"""
BRO Calendar
Offline calendar with events, reminders, and scheduling.
Stores everything locally in TOML.
"""

import os
import sys
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Dict, Optional
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# TOML support
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
# CONFIG
# =============================================================================

CALENDAR_DIR = Path(os.path.dirname(os.path.dirname(__file__))) / "bro_memory"
EVENTS_FILE = CALENDAR_DIR / "calendar_events.toml"


# =============================================================================
# EVENT CLASS
# =============================================================================

class Event:
    """Calendar event."""
    
    def __init__(self, title: str, start: datetime, end: datetime = None,
                 description: str = "", location: str = "", 
                 recurring: str = None, event_id: str = None):
        self.id = event_id or str(uuid.uuid4())[:8]
        self.title = title
        self.start = start
        self.end = end or (start + timedelta(hours=1))
        self.description = description
        self.location = location
        self.recurring = recurring  # None, 'daily', 'weekly', 'monthly', 'yearly'
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "description": self.description,
            "location": self.location,
            "recurring": self.recurring or ""
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        return cls(
            title=data["title"],
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
            description=data.get("description", ""),
            location=data.get("location", ""),
            recurring=data.get("recurring") or None,
            event_id=data["id"]
        )
    
    def __str__(self):
        time_str = self.start.strftime("%I:%M %p")
        end_str = self.end.strftime("%I:%M %p")
        loc = f" 📍 {self.location}" if self.location else ""
        return f"[{time_str}-{end_str}] {self.title}{loc}"


# =============================================================================
# CALENDAR MANAGER
# =============================================================================

class Calendar:
    """Calendar manager."""
    
    def __init__(self):
        CALENDAR_DIR.mkdir(exist_ok=True)
        self.events: List[Event] = []
        self._load()
    
    def _load(self):
        """Load events from file."""
        try:
            if EVENTS_FILE.exists() and tomllib:
                with open(EVENTS_FILE, "rb") as f:
                    data = tomllib.load(f)
                self.events = [Event.from_dict(e) for e in data.get("events", [])]
        except Exception as e:
            print(f"Error loading calendar: {e}")
            self.events = []
    
    def _save(self):
        """Save events to file."""
        try:
            data = {"events": [e.to_dict() for e in self.events]}
            if TOML_WRITE:
                with open(EVENTS_FILE, "wb") as f:
                    tomli_w.dump(data, f)
            else:
                # Manual TOML write
                lines = ["# BRO Calendar Events\n"]
                for i, event in enumerate(self.events):
                    lines.append(f"\n[[events]]")
                    for k, v in event.to_dict().items():
                        if isinstance(v, str):
                            lines.append(f'{k} = "{v}"')
                        else:
                            lines.append(f'{k} = {v}')
                with open(EVENTS_FILE, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines))
        except Exception as e:
            print(f"Error saving calendar: {e}")
    
    def add_event(self, title: str, start: datetime, end: datetime = None,
                  description: str = "", location: str = "",
                  recurring: str = None) -> Event:
        """Add a new event."""
        event = Event(title, start, end, description, location, recurring)
        self.events.append(event)
        self._save()
        return event
    
    def delete_event(self, event_id: str) -> bool:
        """Delete an event by ID."""
        for i, event in enumerate(self.events):
            if event.id == event_id:
                self.events.pop(i)
                self._save()
                return True
        return False
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Get event by ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        return None
    
    def update_event(self, event_id: str, **kwargs) -> Optional[Event]:
        """Update an event."""
        event = self.get_event(event_id)
        if event:
            for key, value in kwargs.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            self._save()
        return event
    
    def get_events_for_date(self, target_date: date) -> List[Event]:
        """Get all events for a specific date."""
        events = []
        for event in self.events:
            event_date = event.start.date()
            
            if event_date == target_date:
                events.append(event)
            elif event.recurring:
                if self._matches_recurring(event, target_date):
                    # Create a virtual event for this date
                    virtual = Event(
                        title=event.title,
                        start=datetime.combine(target_date, event.start.time()),
                        end=datetime.combine(target_date, event.end.time()),
                        description=event.description,
                        location=event.location,
                        recurring=event.recurring,
                        event_id=event.id
                    )
                    events.append(virtual)
        
        return sorted(events, key=lambda e: e.start)
    
    def _matches_recurring(self, event: Event, target_date: date) -> bool:
        """Check if recurring event matches a date."""
        event_date = event.start.date()
        
        if target_date < event_date:
            return False
        
        if event.recurring == "daily":
            return True
        elif event.recurring == "weekly":
            return event_date.weekday() == target_date.weekday()
        elif event.recurring == "monthly":
            return event_date.day == target_date.day
        elif event.recurring == "yearly":
            return (event_date.month == target_date.month and 
                    event_date.day == target_date.day)
        return False
    
    def get_events_for_week(self, start_date: date = None) -> Dict[date, List[Event]]:
        """Get events for a week."""
        if start_date is None:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())  # Monday
        
        week = {}
        for i in range(7):
            day = start_date + timedelta(days=i)
            week[day] = self.get_events_for_date(day)
        
        return week
    
    def get_events_for_month(self, year: int = None, month: int = None) -> Dict[date, List[Event]]:
        """Get events for a month."""
        today = date.today()
        year = year or today.year
        month = month or today.month
        
        from calendar import monthrange
        _, days_in_month = monthrange(year, month)
        
        month_events = {}
        for day in range(1, days_in_month + 1):
            d = date(year, month, day)
            events = self.get_events_for_date(d)
            if events:
                month_events[d] = events
        
        return month_events
    
    def get_upcoming(self, days: int = 7) -> List[Event]:
        """Get upcoming events."""
        today = date.today()
        upcoming = []
        
        for i in range(days):
            day = today + timedelta(days=i)
            upcoming.extend(self.get_events_for_date(day))
        
        return upcoming
    
    def search(self, query: str) -> List[Event]:
        """Search events by title or description."""
        query = query.lower()
        return [e for e in self.events 
                if query in e.title.lower() or query in e.description.lower()]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_calendar = None

def get_calendar() -> Calendar:
    """Get or create calendar instance."""
    global _calendar
    if _calendar is None:
        _calendar = Calendar()
    return _calendar


def add_event(title: str, when: str, duration: int = 60, 
              description: str = "", location: str = "",
              recurring: str = None) -> str:
    """
    Add a calendar event.
    
    Args:
        title: Event title
        when: Date/time string (e.g., "tomorrow 3pm", "2024-01-15 14:00", "monday 9am")
        duration: Duration in minutes (default 60)
        description: Event description
        location: Event location
        recurring: None, 'daily', 'weekly', 'monthly', 'yearly'
    """
    cal = get_calendar()
    
    start = parse_datetime(when)
    if not start:
        return f"❌ Could not parse time: {when}"
    
    end = start + timedelta(minutes=duration)
    
    event = cal.add_event(title, start, end, description, location, recurring)
    
    date_str = start.strftime("%B %d, %Y at %I:%M %p")
    recurring_str = f" (recurring {recurring})" if recurring else ""
    
    return f"📅 Event added: {title}\n   {date_str}{recurring_str}"


def today() -> str:
    """Show today's events."""
    cal = get_calendar()
    events = cal.get_events_for_date(date.today())
    
    output = f"""
📅 TODAY - {date.today().strftime('%A, %B %d, %Y')}
{'='*50}
"""
    
    if not events:
        output += "\nNo events scheduled for today. 🎉"
    else:
        for event in events:
            output += f"\n{event}"
    
    return output


def tomorrow() -> str:
    """Show tomorrow's events."""
    cal = get_calendar()
    target = date.today() + timedelta(days=1)
    events = cal.get_events_for_date(target)
    
    output = f"""
📅 TOMORROW - {target.strftime('%A, %B %d, %Y')}
{'='*50}
"""
    
    if not events:
        output += "\nNo events scheduled."
    else:
        for event in events:
            output += f"\n{event}"
    
    return output


def week() -> str:
    """Show this week's events."""
    cal = get_calendar()
    week_events = cal.get_events_for_week()
    
    output = "📅 THIS WEEK\n" + "="*50
    
    for day, events in week_events.items():
        day_name = day.strftime("%a %d")
        is_today = day == date.today()
        marker = " ← TODAY" if is_today else ""
        
        output += f"\n\n📆 {day_name}{marker}"
        
        if events:
            for event in events:
                output += f"\n   {event}"
        else:
            output += "\n   (no events)"
    
    return output


def upcoming(days: int = 7) -> str:
    """Show upcoming events."""
    cal = get_calendar()
    events = cal.get_upcoming(days)
    
    output = f"📅 NEXT {days} DAYS\n" + "="*50
    
    if not events:
        output += "\n\nNo upcoming events."
    else:
        current_date = None
        for event in events:
            if event.start.date() != current_date:
                current_date = event.start.date()
                output += f"\n\n📆 {current_date.strftime('%A, %B %d')}"
            output += f"\n   {event}"
    
    return output


def delete_event(event_id: str) -> str:
    """Delete an event by ID."""
    cal = get_calendar()
    if cal.delete_event(event_id):
        return f"🗑️ Event {event_id} deleted"
    return f"❌ Event {event_id} not found"


def events_list() -> str:
    """List all events."""
    cal = get_calendar()
    
    if not cal.events:
        return "📅 No events in calendar."
    
    output = "📅 ALL EVENTS\n" + "="*50
    
    for event in sorted(cal.events, key=lambda e: e.start):
        date_str = event.start.strftime("%b %d, %Y")
        output += f"\n[{event.id}] {date_str} - {event.title}"
        if event.recurring:
            output += f" (🔄 {event.recurring})"
    
    return output


def parse_datetime(text: str) -> Optional[datetime]:
    """Parse datetime from natural language."""
    text = text.lower().strip()
    now = datetime.now()
    today_date = date.today()
    
    # Try standard formats first
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M",
        "%B %d %Y %I:%M %p",
        "%B %d, %Y %I:%M %p",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except:
            pass
    
    # Parse relative dates
    time_part = None
    date_part = today_date
    
    # Extract time
    import re
    time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2) or 0)
        ampm = time_match.group(3)
        
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        
        time_part = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0).time()
    
    # Parse date
    if "today" in text:
        date_part = today_date
    elif "tomorrow" in text:
        date_part = today_date + timedelta(days=1)
    elif "monday" in text:
        days_ahead = 0 - today_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        date_part = today_date + timedelta(days=days_ahead)
    elif "tuesday" in text:
        days_ahead = 1 - today_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        date_part = today_date + timedelta(days=days_ahead)
    elif "wednesday" in text:
        days_ahead = 2 - today_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        date_part = today_date + timedelta(days=days_ahead)
    elif "thursday" in text:
        days_ahead = 3 - today_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        date_part = today_date + timedelta(days=days_ahead)
    elif "friday" in text:
        days_ahead = 4 - today_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        date_part = today_date + timedelta(days=days_ahead)
    elif "saturday" in text:
        days_ahead = 5 - today_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        date_part = today_date + timedelta(days=days_ahead)
    elif "sunday" in text:
        days_ahead = 6 - today_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        date_part = today_date + timedelta(days=days_ahead)
    
    if time_part:
        return datetime.combine(date_part, time_part)
    else:
        return datetime.combine(date_part, datetime.now().replace(hour=9, minute=0).time())


def quick_add(text: str) -> str:
    """
    Quick add event from natural language.
    Examples:
        "Meeting tomorrow 3pm"
        "Lunch with John friday 12:30pm"
        "Doctor monday 10am"
    """
    parts = text.split()
    if len(parts) < 2:
        return "❌ Please provide event title and time"
    
    # Find where time starts
    time_words = ["today", "tomorrow", "monday", "tuesday", "wednesday", 
                  "thursday", "friday", "saturday", "sunday"]
    
    time_start = None
    for i, word in enumerate(parts):
        if word.lower() in time_words or re.match(r'\d{1,2}(:\d{2})?(am|pm)?', word.lower()):
            time_start = i
            break
    
    if time_start:
        title = " ".join(parts[:time_start])
        when = " ".join(parts[time_start:])
    else:
        title = text
        when = "today 9am"
    
    return add_event(title, when)


# Need re for quick_add
import re


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="BRO Calendar")
    parser.add_argument("command", nargs="?", default="today",
                       choices=["today", "tomorrow", "week", "upcoming", "list", "add"])
    parser.add_argument("args", nargs="*")
    
    args = parser.parse_args()
    
    if args.command == "today":
        print(today())
    elif args.command == "tomorrow":
        print(tomorrow())
    elif args.command == "week":
        print(week())
    elif args.command == "upcoming":
        print(upcoming())
    elif args.command == "list":
        print(events_list())
    elif args.command == "add" and args.args:
        print(quick_add(" ".join(args.args)))
