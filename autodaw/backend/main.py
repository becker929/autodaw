"""FastAPI backend for AutoDAW web application."""

from fastapi import FastAPI, HTTPException, File, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
import uuid
import os
import mimetypes

from ..core.database import Database
from ..core.ga_jsi_engine import WebGAJSIEngine
from ..core.constants import (
    MIN_POPULATION_SIZE, MAX_POPULATION_SIZE, DEFAULT_POPULATION_SIZE,
    MIN_TARGET_FREQUENCY, MAX_TARGET_FREQUENCY, DEFAULT_TARGET_FREQUENCY,
    MIN_SESSION_NAME_LENGTH, MAX_SESSION_NAME_LENGTH, MAX_NOTES_LENGTH
)

app = FastAPI(title="AutoDAW API", version="0.1.0",
              description="GA+JSI+Audio Oracle optimization for digital audio workstations")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and engine
db = Database()
reaper_project_path = Path(__file__).parent.parent.parent / "reaper"
engine = WebGAJSIEngine(database=db, reaper_project_path=reaper_project_path)

# Pydantic models with strict validation
class SessionCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=MIN_SESSION_NAME_LENGTH,
        max_length=MAX_SESSION_NAME_LENGTH,
        description=f"Session name (required, {MIN_SESSION_NAME_LENGTH}-{MAX_SESSION_NAME_LENGTH} characters)"
    )
    target_frequency: Optional[float] = Field(
        DEFAULT_TARGET_FREQUENCY,
        ge=MIN_TARGET_FREQUENCY,
        le=MAX_TARGET_FREQUENCY,
        description=f"Target frequency in Hz ({MIN_TARGET_FREQUENCY}-{MAX_TARGET_FREQUENCY}Hz)"
    )
    population_size: int = Field(
        DEFAULT_POPULATION_SIZE,
        ge=MIN_POPULATION_SIZE,
        le=MAX_POPULATION_SIZE,
        description=f"Population size ({MIN_POPULATION_SIZE}-{MAX_POPULATION_SIZE} individuals)"
    )
    config: Optional[Dict[str, Any]] = Field(None, description="Optional configuration parameters")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty_or_whitespace(cls, v):
        if not v or not v.strip():
            raise ValueError('Session name cannot be empty or only whitespace')
        return v.strip()

class PreferenceSubmission(BaseModel):
    preference: str = Field(..., pattern="^[ab]$", description="User preference: must be 'a' or 'b'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level (0.0 to 1.0)")
    notes: Optional[str] = Field(None, max_length=MAX_NOTES_LENGTH, description=f"Optional notes (max {MAX_NOTES_LENGTH} characters)")

    @field_validator('notes')
    @classmethod
    def notes_sanitize(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v

class PopulationInitialize(BaseModel):
    session_id: str = Field(..., min_length=1, description="Valid session ID (required)")

# Health check
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "AutoDAW API operational", "version": "0.1.0"}

# GA Session endpoints
@app.post("/api/sessions")
async def create_session(session_data: SessionCreate):
    """Create new GA optimization session."""
    try:
        session_id = engine.create_session(
            name=session_data.name,
            target_frequency=session_data.target_frequency,
            population_size=session_data.population_size,
            config=session_data.config
        )

        session = db.get_ga_session(session_id)
        return {"session_id": session_id, "session": session}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get GA session information."""
    session = db.get_ga_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/api/sessions")
async def list_sessions():
    """List all GA sessions."""
    with db.get_connection() as conn:
        rows = conn.execute("SELECT * FROM ga_sessions ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

# Population endpoints
@app.post("/api/populations/initialize")
async def initialize_population(init_data: PopulationInitialize):
    """Initialize first population for GA session."""
    try:
        result = engine.initialize_population(init_data.session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize population: {str(e)}")

@app.get("/api/sessions/{session_id}/populations")
async def get_session_populations(session_id: str):
    """Get all populations for a session."""
    try:
        populations = engine.get_session_populations(session_id)
        return populations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get populations: {str(e)}")

@app.get("/api/populations/{population_id}")
async def get_population_with_strengths(population_id: str):
    """Get population with Bradley-Terry strengths."""
    try:
        result = engine.get_population_with_strengths(population_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get population: {str(e)}")

# Comparison endpoints
@app.get("/api/comparisons/next")
async def get_next_comparison():
    """Get next comparison pair for user evaluation."""
    try:
        comparison = engine.get_next_comparison()
        if not comparison:
            return {"message": "No pending comparisons", "comparison": None}
        return {"comparison": comparison}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comparison: {str(e)}")

@app.post("/api/comparisons/{comparison_id}/preference")
async def submit_comparison_preference(comparison_id: str, submission: PreferenceSubmission):
    """Submit user preference for comparison."""
    if submission.preference not in ["a", "b"]:
        raise HTTPException(status_code=400, detail="Preference must be 'a' or 'b'")

    if not (0.0 <= submission.confidence <= 1.0):
        raise HTTPException(status_code=400, detail="Confidence must be between 0.0 and 1.0")

    try:
        success = engine.submit_comparison_preference(
            comparison_id=comparison_id,
            preference=submission.preference,
            confidence=submission.confidence,
            notes=submission.notes
        )

        if success:
            return {"message": "Preference recorded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to record preference")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit preference: {str(e)}")

@app.get("/api/comparisons/{comparison_id}")
async def get_comparison(comparison_id: str):
    """Get specific comparison information."""
    comparison = db.get_comparison(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comparison

# Audio file endpoints
@app.get("/api/audio/{file_id}/stream")
async def stream_audio_file(file_id: str):
    """Stream audio file for playback."""
    audio_file = db.get_audio_file(file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")

    file_path = Path(audio_file['filepath'])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    # Determine media type
    media_type, _ = mimetypes.guess_type(str(file_path))
    if not media_type:
        media_type = "audio/wav"  # Default for audio files

    # Get file size for proper headers
    file_size = file_path.stat().st_size

    # Stream the file with proper headers
    def iterfile():
        with open(file_path, mode="rb") as file_like:
            yield from file_like

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Cache-Control": "public, max-age=3600",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        "Access-Control-Allow-Headers": "Range, Content-Type",
    }

    return StreamingResponse(iterfile(), media_type=media_type, headers=headers)

@app.options("/api/audio/{file_id}/stream")
async def options_stream_audio_file(file_id: str):
    """Handle CORS preflight for audio streaming."""
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Range, Content-Type"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

@app.get("/api/audio/{file_id}")
async def get_audio_file_info(file_id: str):
    """Get audio file information."""
    audio_file = db.get_audio_file(file_id)
    if not audio_file:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return audio_file

@app.get("/api/audio-files")
async def list_audio_files():
    """List all audio files."""
    return db.list_audio_files()

# Statistics endpoints
@app.get("/api/stats")
async def get_stats():
    """Get comparison and optimization statistics."""
    try:
        stats = engine.get_comparison_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Static file serving for development
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Starting AutoDAW API server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")

    uvicorn.run(
        "autodaw.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
