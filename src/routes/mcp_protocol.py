"""
MCP Protocol Routes - Simtheory.ai Integration.

Implements the MCP protocol for Simtheory.ai to query workout data.
This is a simplified REST-based MCP implementation.
"""

from fastapi import APIRouter
from datetime import datetime
from zoneinfo import ZoneInfo

from .storage import workout_storage

router = APIRouter()

DEFAULT_TIMEZONE = "America/Los_Angeles"


@router.get("")
@router.get("/")
async def mcp_root():
    """
    MCP service discovery endpoint.
    Returns available tools/capabilities.
    """
    return {
        "name": "healthkit-mcp",
        "version": "1.0.0",
        "description": "Apple HealthKit workout data from Timothy's iPhone/Apple Watch",
        "tools": [
            {
                "name": "get_workouts",
                "description": "Get workouts from the last N days, optionally filtered by type",
                "parameters": {
                    "days": {"type": "integer", "default": 7},
                    "workout_type": {"type": "string", "optional": True}
                }
            },
            {
                "name": "get_todays_workouts",
                "description": "Get all workouts logged today (Pacific time)",
                "parameters": {}
            },
            {
                "name": "get_workout_summary",
                "description": "Get workout statistics and summary for N days",
                "parameters": {
                    "days": {"type": "integer", "default": 7}
                }
            }
        ],
        "supported_workout_types": [
            "Functional Training",
            "Golf",
            "Yoga",
            "Running",
            "Rowing",
            "Walking",
            "Cycling",
            "Swimming",
            "HIIT",
            "Strength Training"
        ]
    }


@router.get("/tools/get_workouts")
async def mcp_get_workouts(days: int = 7, workout_type: str = None):
    """MCP tool: Get workouts."""
    if workout_type:
        workouts = workout_storage.get_by_type(workout_type)
    else:
        workouts = workout_storage.get_recent(days)
    
    return {
        "result": {
            "workouts": workouts,
            "count": len(workouts),
            "days": days,
            "filter": workout_type
        }
    }


@router.get("/tools/get_todays_workouts")
async def mcp_get_todays_workouts():
    """MCP tool: Get today's workouts."""
    pacific = ZoneInfo(DEFAULT_TIMEZONE)
    today = datetime.now(pacific).strftime("%Y-%m-%d")
    workouts = workout_storage.get_today()
    
    return {
        "result": {
            "date": today,
            "workouts": workouts,
            "count": len(workouts),
            "timezone": DEFAULT_TIMEZONE
        }
    }


@router.get("/tools/get_workout_summary")
async def mcp_get_workout_summary(days: int = 7):
    """MCP tool: Get workout summary."""
    summary = workout_storage.get_summary(days)
    
    return {
        "result": {
            "summary": summary
        }
    }
