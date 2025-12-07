"""
Ingest routes for HealthKit MCP.

Handles incoming workout data from iOS Shortcuts.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from .storage import workout_storage

# No prefix here - main.py adds /ingest prefix when including this router
router = APIRouter(tags=["ingest"])

DEFAULT_TIMEZONE = "America/Los_Angeles"


class WorkoutData(BaseModel):
    """Workout data model matching iOS Shortcuts output."""
    type: str = Field(..., description="Workout type (e.g., 'Functional Training', 'Golf', 'Yoga')")
    start: str = Field(..., description="Start time in ISO format")
    end: Optional[str] = Field(None, description="End time in ISO format")
    duration_minutes: Optional[float] = Field(None, description="Duration in minutes")
    calories: Optional[float] = Field(None, description="Active calories burned")
    distance_km: Optional[float] = Field(None, description="Distance in kilometers")
    avg_heart_rate: Optional[int] = Field(None, description="Average heart rate")
    source: Optional[str] = Field("Apple Health", description="Data source")


class WorkoutBatch(BaseModel):
    """Batch of workouts for bulk ingestion."""
    workouts: List[WorkoutData]


def get_api_key():
    """Get API key from environment."""
    return os.getenv("HEALTHKIT_API_KEY", "")


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify the API key from request header."""
    expected_key = get_api_key()
    if not expected_key:
        # No key configured = allow all (dev mode)
        return True
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.post("/workout")
async def ingest_workout(workout: WorkoutData, x_api_key: str = Header(None, alias="X-API-Key")):
    """
    Ingest a single workout from iOS Shortcuts.
    
    Requires X-API-Key header if HEALTHKIT_API_KEY is configured.
    """
    # Check API key if configured
    expected_key = get_api_key()
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    workout_dict = workout.model_dump()
    workout_dict["ingested_at"] = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).isoformat()
    
    is_new = workout_storage.add_workout(workout_dict)
    
    return {
        "status": "ok",
        "message": "Workout ingested" if is_new else "Workout updated (duplicate)",
        "workout_type": workout.type,
        "start": workout.start,
        "is_new": is_new
    }


@router.post("/workouts")
async def ingest_workouts_batch(batch: WorkoutBatch, x_api_key: str = Header(None, alias="X-API-Key")):
    """
    Ingest multiple workouts at once.
    
    Useful for syncing historical data or batch uploads from iOS Shortcuts.
    """
    expected_key = get_api_key()
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    results = []
    new_count = 0
    
    for workout in batch.workouts:
        workout_dict = workout.model_dump()
        workout_dict["ingested_at"] = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).isoformat()
        
        is_new = workout_storage.add_workout(workout_dict)
        if is_new:
            new_count += 1
        
        results.append({
            "type": workout.type,
            "start": workout.start,
            "is_new": is_new
        })
    
    return {
        "status": "ok",
        "message": f"Processed {len(results)} workouts ({new_count} new)",
        "total": len(results),
        "new": new_count,
        "updated": len(results) - new_count,
        "results": results
    }


@router.delete("/workouts")
async def clear_workouts(x_api_key: str = Header(None, alias="X-API-Key")):
    """
    Clear all stored workouts.
    
    Use with caution - this deletes all workout data.
    """
    expected_key = get_api_key()
    if expected_key and x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    count = workout_storage.clear()
    
    return {
        "status": "ok",
        "message": f"Cleared {count} workouts",
        "cleared": count
    }
