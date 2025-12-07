"""
Data Routes - Query stored workout data.

Endpoints for retrieving workout data with filtering options.
All times are in Pacific timezone (America/Los_Angeles).
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from .storage import workout_storage

router = APIRouter()

DEFAULT_TIMEZONE = "America/Los_Angeles"


@router.get("/workouts")
async def get_workouts(
    days: Optional[int] = Query(7, ge=1, le=365, description="Number of days of history"),
    workout_type: Optional[str] = Query(None, description="Filter by workout type")
):
    """
    Get all workouts from the last N days.
    Optionally filter by workout type.
    """
    if workout_type:
        workouts = workout_storage.get_by_type(workout_type)
    else:
        workouts = workout_storage.get_recent(days)
    
    return {
        "status": "ok",
        "workouts": workouts,
        "count": len(workouts),
        "days": days,
        "filter": workout_type
    }


@router.get("/workouts/today")
async def get_todays_workouts():
    """Get today's workouts (Pacific time)."""
    pacific = ZoneInfo(DEFAULT_TIMEZONE)
    today = datetime.now(pacific).strftime("%Y-%m-%d")
    workouts = workout_storage.get_today()
    
    return {
        "status": "ok",
        "date": today,
        "workouts": workouts,
        "count": len(workouts),
        "timezone": DEFAULT_TIMEZONE
    }


@router.get("/workouts/date/{date}")
async def get_workouts_by_date(date: str):
    """Get workouts for a specific date (YYYY-MM-DD)."""
    workouts = workout_storage.get_by_date(date)
    
    return {
        "status": "ok",
        "date": date,
        "workouts": workouts,
        "count": len(workouts)
    }


@router.get("/workouts/type/{workout_type}")
async def get_workouts_by_type(workout_type: str):
    """
    Get all workouts of a specific type.
    Examples: Functional Training, Golf, Yoga, Running
    """
    workouts = workout_storage.get_by_type(workout_type)
    
    return {
        "status": "ok",
        "workout_type": workout_type,
        "workouts": workouts,
        "count": len(workouts)
    }


@router.get("/workouts/summary")
async def get_workout_summary(
    days: Optional[int] = Query(7, ge=1, le=365, description="Number of days for summary")
):
    """
    Get workout summary for the last N days.
    Returns total workouts, duration, calories by type.
    """
    summary = workout_storage.get_summary(days)
    pacific = ZoneInfo(DEFAULT_TIMEZONE)
    
    return {
        "status": "ok",
        "summary": summary,
        "generated_at": datetime.now(pacific).isoformat(),
        "timezone": DEFAULT_TIMEZONE
    }


@router.get("/stats")
async def get_stats():
    """Get basic storage statistics."""
    return {
        "status": "ok",
        "total_workouts_stored": workout_storage.count(),
        "storage_type": "in-memory with file persistence"
    }
