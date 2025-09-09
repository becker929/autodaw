"""
FastAPI backend for audio comparison interface.
Provides REST endpoints for managing audio file comparisons and preferences.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
import uuid
import json
from pathlib import Path

app = FastAPI(title="Audio Comparison API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class AudioFile(BaseModel):
    id: str
    filename: str
    filepath: str
    duration: Optional[float] = None
    metadata: Dict[str, Any] = {}

class ComparisonPair(BaseModel):
    id: str
    audio_a: AudioFile
    audio_b: AudioFile
    preference: Optional[str] = None  # "a", "b", or None
    confidence: Optional[float] = None
    notes: Optional[str] = None

class PreferenceSubmission(BaseModel):
    comparison_id: str
    preference: str  # "a" or "b"
    confidence: float
    notes: Optional[str] = None

# In-memory storage (replace with database in production)
audio_files: Dict[str, AudioFile] = {}
comparison_pairs: Dict[str, ComparisonPair] = {}
comparison_queue: List[str] = []

# Initialize with sample data
def initialize_sample_data():
    """Initialize with sample audio files for demonstration."""
    sample_files = [
        {"filename": "sample_1.wav", "filepath": "/samples/sample_1.wav"},
        {"filename": "sample_2.wav", "filepath": "/samples/sample_2.wav"},
        {"filename": "sample_3.wav", "filepath": "/samples/sample_3.wav"},
        {"filename": "sample_4.wav", "filepath": "/samples/sample_4.wav"},
    ]

    for file_data in sample_files:
        file_id = str(uuid.uuid4())
        audio_files[file_id] = AudioFile(
            id=file_id,
            filename=file_data["filename"],
            filepath=file_data["filepath"],
            duration=3.5,  # Stub duration
            metadata={"format": "wav", "sample_rate": 44100}
        )

    # Create comparison pairs
    file_ids = list(audio_files.keys())
    for i in range(0, len(file_ids), 2):
        if i + 1 < len(file_ids):
            pair_id = str(uuid.uuid4())
            comparison_pairs[pair_id] = ComparisonPair(
                id=pair_id,
                audio_a=audio_files[file_ids[i]],
                audio_b=audio_files[file_ids[i + 1]]
            )
            comparison_queue.append(pair_id)

# Initialize on startup
initialize_sample_data()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Audio Comparison API operational", "version": "1.0.0"}

@app.get("/api/audio-files", response_model=List[AudioFile])
async def get_audio_files():
    """Get all available audio files."""
    return list(audio_files.values())

@app.post("/api/audio-files/upload")
async def upload_audio_file(file: UploadFile = File(...)):
    """Upload a new audio file for comparison."""
    # Stub implementation - in production, save file and extract metadata
    file_id = str(uuid.uuid4())

    # Simulate file processing
    audio_file = AudioFile(
        id=file_id,
        filename=file.filename,
        filepath=f"/uploads/{file_id}_{file.filename}",
        duration=None,  # Would extract with librosa
        metadata={"format": "unknown", "uploaded": True}
    )

    audio_files[file_id] = audio_file
    return {"message": "File uploaded successfully", "file_id": file_id}

@app.get("/api/comparisons/next", response_model=Optional[ComparisonPair])
async def get_next_comparison():
    """Get the next comparison pair in the queue."""
    if not comparison_queue:
        return None

    # Find first unrated comparison
    for pair_id in comparison_queue:
        pair = comparison_pairs.get(pair_id)
        if pair and pair.preference is None:
            return pair

    return None

@app.get("/api/comparisons", response_model=List[ComparisonPair])
async def get_all_comparisons():
    """Get all comparison pairs with their current status."""
    return list(comparison_pairs.values())

@app.get("/api/comparisons/{comparison_id}", response_model=ComparisonPair)
async def get_comparison(comparison_id: str):
    """Get a specific comparison pair."""
    if comparison_id not in comparison_pairs:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comparison_pairs[comparison_id]

@app.post("/api/comparisons/{comparison_id}/preference")
async def submit_preference(comparison_id: str, submission: PreferenceSubmission):
    """Submit a preference for a comparison pair."""
    if comparison_id not in comparison_pairs:
        raise HTTPException(status_code=404, detail="Comparison not found")

    if submission.preference not in ["a", "b"]:
        raise HTTPException(status_code=400, detail="Preference must be 'a' or 'b'")

    pair = comparison_pairs[comparison_id]
    pair.preference = submission.preference
    pair.confidence = submission.confidence
    pair.notes = submission.notes

    return {"message": "Preference recorded successfully"}

@app.get("/api/audio/{file_id}/stream")
async def stream_audio(file_id: str):
    """Stream audio file for playback."""
    if file_id not in audio_files:
        raise HTTPException(status_code=404, detail="Audio file not found")

    audio_file = audio_files[file_id]

    # Stub implementation - in production, return actual file
    # For now, return a placeholder response
    return {"message": f"Streaming {audio_file.filename}", "url": f"/static/audio/{file_id}"}

@app.get("/api/stats")
async def get_comparison_stats():
    """Get statistics about comparisons completed."""
    total_comparisons = len(comparison_pairs)
    completed_comparisons = sum(1 for pair in comparison_pairs.values() if pair.preference is not None)

    preferences = {"a": 0, "b": 0}
    confidences = []

    for pair in comparison_pairs.values():
        if pair.preference:
            preferences[pair.preference] += 1
        if pair.confidence:
            confidences.append(pair.confidence)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    return {
        "total_comparisons": total_comparisons,
        "completed_comparisons": completed_comparisons,
        "remaining_comparisons": total_comparisons - completed_comparisons,
        "preference_distribution": preferences,
        "average_confidence": round(avg_confidence, 2)
    }

@app.post("/api/comparisons/generate")
async def generate_new_comparisons():
    """Generate new comparison pairs from available audio files."""
    file_list = list(audio_files.values())

    if len(file_list) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 audio files")

    new_pairs = 0
    # Simple round-robin pairing (in production, use more sophisticated algorithms)
    for i in range(0, len(file_list), 2):
        if i + 1 < len(file_list):
            pair_id = str(uuid.uuid4())
            comparison_pairs[pair_id] = ComparisonPair(
                id=pair_id,
                audio_a=file_list[i],
                audio_b=file_list[i + 1]
            )
            comparison_queue.append(pair_id)
            new_pairs += 1

    return {"message": f"Generated {new_pairs} new comparison pairs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
