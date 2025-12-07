"""
Workout Storage - In-memory storage with file persistence.

For production, this could be replaced with:
- SQLite
- PostgreSQL (Railway addon)
- Redis
- JSON file on persistent volume
"""

from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo
import json
import os

DEFAULT_TIMEZONE = "America/Los_Angeles"


class WorkoutStorage:
    """
    In-memory workout storage with deduplication.
    Workouts are keyed by (type, start_time) to prevent duplicates.
    """
    
    def __init__(self):
        self.workouts = {}  # key: (type, start) -> workout data
        self._load_from_file()
    
    def _get_key(self, workout: dict) -> str:
        """Generate unique key for workout."""
        return f"{workout.get('type')}_{workout.get('start')}"
    
    def add_workout(self, workout: dict) -> bool:
        """
        Add a workout, returns True if new, False if duplicate/updated.
        """
        key = self._get_key(workout)
        is_new = key not in self.workouts
        self.workouts[key] = workout
        self._save_to_file()
        return is_new
    
    def get_all(self) -> List[dict]:
        """Get all workouts sorted by start time (most recent first)."""
        workouts = list(self.workouts.values())
        workouts.sort(key=lambda w: w.get("start", ""), reverse=True)
        return workouts
    
    def get_by_date(self, date_str: str) -> List[dict]:
        """
        Get workouts for a specific date (YYYY-MM-DD in Pacific time).
        """
        result = []
        for workout in self.workouts.values():
            start = workout.get("start", "")
            if start.startswith(date_str):
                result.append(workout)
        result.sort(key=lambda w: w.get("start", ""))
        return result
    
    def get_by_type(self, workout_type: str) -> List[dict]:
        """Get all workouts of a specific type."""
        result = []
        for workout in self.workouts.values():
            if workout.get("type", "").lower() == workout_type.lower():
                result.append(workout)
        result.sort(key=lambda w: w.get("start", ""), reverse=True)
        return result
    
    def get_recent(self, days: int = 7) -> List[dict]:
        """Get workouts from the last N days."""
        pacific = ZoneInfo(DEFAULT_TIMEZONE)
        now = datetime.now(pacific)
        cutoff = now - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        
        result = []
        for workout in self.workouts.values():
            start = workout.get("start", "")
            # Extract date portion for comparison
            start_date = start[:10] if len(start) >= 10 else ""
            if start_date >= cutoff_str:
                result.append(workout)
        
        result.sort(key=lambda w: w.get("start", ""), reverse=True)
        return result
    
    def get_today(self) -> List[dict]:
        """Get today's workouts (Pacific time)."""
        pacific = ZoneInfo(DEFAULT_TIMEZONE)
        today = datetime.now(pacific).strftime("%Y-%m-%d")
        return self.get_by_date(today)
    
    def get_summary(self, days: int = 7) -> dict:
        """
        Get workout summary for the last N days.
        Returns counts by type, total duration, total calories.
        """
        workouts = self.get_recent(days)
        
        summary = {
            "period_days": days,
            "total_workouts": len(workouts),
            "total_duration_minutes": 0,
            "total_calories": 0,
            "by_type": {},
            "workouts_by_date": {}
        }
        
        for w in workouts:
            # Count by type
            wtype = w.get("type", "Unknown")
            if wtype not in summary["by_type"]:
                summary["by_type"][wtype] = {
                    "count": 0,
                    "total_duration": 0,
                    "total_calories": 0
                }
            summary["by_type"][wtype]["count"] += 1
            
            # Duration
            duration = w.get("duration_minutes") or 0
            summary["total_duration_minutes"] += duration
            summary["by_type"][wtype]["total_duration"] += duration
            
            # Calories
            calories = w.get("calories") or 0
            summary["total_calories"] += calories
            summary["by_type"][wtype]["total_calories"] += calories
            
            # By date
            start = w.get("start", "")
            date = start[:10] if len(start) >= 10 else "unknown"
            if date not in summary["workouts_by_date"]:
                summary["workouts_by_date"][date] = []
            summary["workouts_by_date"][date].append({
                "type": wtype,
                "duration": duration,
                "calories": calories
            })
        
        return summary
    
    def count(self) -> int:
        """Get total workout count."""
        return len(self.workouts)
    
    def clear(self) -> int:
        """Clear all workouts, returns count cleared."""
        count = len(self.workouts)
        self.workouts = {}
        self._save_to_file()
        return count
    
    def _get_storage_path(self) -> str:
        """Get path for persistent storage file."""
        return os.getenv("WORKOUT_STORAGE_PATH", "/tmp/workouts.json")
    
    def _save_to_file(self):
        """Save workouts to file for persistence across restarts."""
        try:
            path = self._get_storage_path()
            with open(path, "w") as f:
                json.dump(list(self.workouts.values()), f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save workouts to file: {e}")
    
    def _load_from_file(self):
        """Load workouts from file on startup."""
        try:
            path = self._get_storage_path()
            if os.path.exists(path):
                with open(path, "r") as f:
                    workouts = json.load(f)
                    for w in workouts:
                        key = self._get_key(w)
                        self.workouts[key] = w
                print(f"Loaded {len(self.workouts)} workouts from storage")
        except Exception as e:
            print(f"Warning: Could not load workouts from file: {e}")


# Singleton instance
workout_storage = WorkoutStorage()
