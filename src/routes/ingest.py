"""
Ingest routes for HealthKit MCP.

Handles incoming workout data from iOS Shortcuts.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import json

router = APIRouter(prefix="/ingest", tags=["ingest"])

# In-memory storage (will reset on restart)
workouts_store: List[dict] = []

# Optional file persistence
PERSISTENCE_FILE = "/tmp/workouts.json"


def load_workouts():
    """Load workouts from persistence file if it exists."""
    global workouts_store
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r") as f:
                workouts_store = json.load(f)
        except Exception:
            workouts_store = []


def save_workouts():
    """Save workouts to persistence file."""
    try:
        with open(PERSISTENCE_FILE, "w") as f:
            json.dump(workouts_store, f)
    except Exception:
        pass


# Load existing workouts on module import
load_workouts()


class WorkoutData(BaseModel):
    """Schema for incoming workout data from iOS Shortcuts."""
    workout_type: str = Field(..., description="Type of workout (e.g., Running, Cycling, Yoga)")
    start_date: str = Field(..., description="ISO 8601 start datetime")
    end_date: str = Field(..., description="ISO 8601 end datetime")
    duration_minutes: float = Field(..., description="Duration in minutes")
    calories: Optional[float] = Field(None, description="Active calories burned")
    distance_miles: Optional[float] = Field(None, description="Distance in miles (if applicable)")
    heart_rate_avg: Optional[int] = Field(None, description="Average heart rate")
    heart_rate_max: Optional[int] = Field(None, description="Maximum heart rate")
    source: str = Field(default="Apple Watch", description="Data source device")


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify the API key from request header."""
    expected_key = os.getenv("HEALTHKIT_API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@router.post("/workout")
async def ingest_workout(workout: WorkoutData, authorized: bool = Depends(verify_api_key)):
    """
    Ingest a single workout from iOS Shortcuts.
    
    Requires X-API-Key header for authentication.
    """
    workout_record = {
        "id": len(workouts_store) + 1,
        "ingested_at": datetime.utcnow().isoformat() + "Z",
        **workout.model_dump()
    }
    
    workouts_store.append(workout_record)
    save_workouts()
    
    return {
        "status": "success",
        "message": f"Workout '{workout.workout_type}' ingested successfully",
        "workout_id": workout_record["id"]
    }


@router.get("/workouts")
async def get_workouts(
    limit: int = 10,
    workout_type: Optional[str] = None,
    authorized: bool = Depends(verify_api_key)
):
    """
    Retrieve ingested workouts.
    
    Optionally filter by workout_type and limit results.
    """
    results = workouts_store
    
    if workout_type:
        results = [w for w in results if w.get("workout_type", "").lower() == workout_type.lower()]
    
    # Return most recent first
    results = sorted(results, key=lambda x: x.get("ingested_at", ""), reverse=True)
    
    return {
        "count": len(results[:limit]),
        "total": len(workouts_store),
        "workouts": results[:limit]
    }


@router.delete("/workouts")
async def clear_workouts(authorized: bool = Depends(verify_api_key)):
    """Clear all stored workouts. Use with caution."""
    global workouts_store
    count = len(workouts_store)
    workouts_store = []
    save_workouts()
    
    return {
        "status": "success",
        "message": f"Cleared {count} workouts"
    }
