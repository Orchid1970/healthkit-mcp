"""
HealthKit MCP - Apple HealthKit Workout Integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

from src.routes import ingest, data, mcp_protocol

app = FastAPI(
    title="HealthKit MCP",
    description="Apple HealthKit workout integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["Ingest"])
app.include_router(data.router, prefix="/data", tags=["Data"])
app.include_router(mcp_protocol.router, prefix="/mcp", tags=["MCP Protocol"])


@app.get("/")
async def root():
    return {
        "service": "healthkit-mcp",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
