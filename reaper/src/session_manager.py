"""Session and artifact management."""

from pathlib import Path
from typing import Dict, Any
import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from config import AutomationConfig


@dataclass
class SessionArtifacts:
    """Tracks artifacts created during a session."""
    session_id: str
    session_dir: Path
    parameter_files: list[Path]
    midi_files: list[Path]
    render_files: list[Path]
    audio_files: list[Path]
    log_files: list[Path]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Path objects as strings."""
        return {
            'session_id': self.session_id,
            'session_dir': str(self.session_dir),
            'parameter_files': [str(p) for p in self.parameter_files],
            'midi_files': [str(p) for p in self.midi_files],
            'render_files': [str(p) for p in self.render_files],
            'audio_files': [str(p) for p in self.audio_files],
            'log_files': [str(p) for p in self.log_files]
        }


class SessionManager:
    """Manages automation sessions and their artifacts."""

    def __init__(self, base_output_dir: Path = Path("/Users/anthonybecker/Desktop/evolver_sessions")):
        self.base_output_dir = base_output_dir

    def create_session_directory(self, session_id: str) -> Path:
        """Create and return session directory."""
        session_dir = self.base_output_dir / f"session_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def get_session_directory(self, session_id: str) -> Path:
        """Get session directory path."""
        return self.base_output_dir / f"session_{session_id}"

    def create_session_config(self, session_id: str, config: AutomationConfig) -> Path:
        """Create session-specific config and return session directory."""
        session_dir = self.create_session_directory(session_id)

        # Update config with session directory
        config.session_id = session_id
        config.output_dir = session_dir

        return session_dir

    def save_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> Path:
        """Save session metadata to JSON file."""
        session_dir = self.get_session_directory(session_id)
        metadata_file = session_dir / "session_metadata.json"

        # Add timestamp
        metadata['created_at'] = datetime.now().isoformat()
        metadata['session_id'] = session_id

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        return metadata_file

    def load_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """Load session metadata from JSON file."""
        session_dir = self.get_session_directory(session_id)
        metadata_file = session_dir / "session_metadata.json"

        if not metadata_file.exists():
            return {}

        with open(metadata_file, 'r') as f:
            return json.load(f)

    def collect_session_artifacts(self, session_id: str) -> SessionArtifacts:
        """Collect all artifacts from a session directory."""
        session_dir = self.get_session_directory(session_id)

        if not session_dir.exists():
            raise FileNotFoundError(f"Session directory not found: {session_dir}")

        # Collect different types of files
        parameter_files = list(session_dir.glob("params_*.txt")) + list(session_dir.glob("octave_change_*.txt"))
        midi_files = list(session_dir.glob("midi_notes_*.txt"))
        render_files = list(session_dir.glob("render_log_*.txt"))
        audio_files = []
        log_files = list(session_dir.glob("*.log"))

        # Find audio files (they're in subdirectories)
        for audio_dir in session_dir.glob("rendered_audio_*"):
            if audio_dir.is_dir():
                audio_files.extend(audio_dir.glob("*.wav"))

        return SessionArtifacts(
            session_id=session_id,
            session_dir=session_dir,
            parameter_files=parameter_files,
            midi_files=midi_files,
            render_files=render_files,
            audio_files=audio_files,
            log_files=log_files
        )

    def cleanup_session(self, session_id: str, keep_audio: bool = True) -> None:
        """Clean up session artifacts, optionally keeping audio files."""
        session_dir = self.get_session_directory(session_id)

        if not session_dir.exists():
            return

        if keep_audio:
            # Remove only non-audio files
            artifacts = self.collect_session_artifacts(session_id)
            for file_list in [artifacts.parameter_files, artifacts.midi_files,
                             artifacts.render_files, artifacts.log_files]:
                for file_path in file_list:
                    if file_path.exists():
                        file_path.unlink()
        else:
            # Remove entire session directory
            shutil.rmtree(session_dir)

    def list_sessions(self) -> list[str]:
        """List all available session IDs."""
        if not self.base_output_dir.exists():
            return []

        sessions = []
        for session_dir in self.base_output_dir.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("session_"):
                session_id = session_dir.name.replace("session_", "")
                sessions.append(session_id)

        return sorted(sessions)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary information about a session."""
        try:
            artifacts = self.collect_session_artifacts(session_id)
            metadata = self.load_session_metadata(session_id)

            return {
                'session_id': session_id,
                'session_dir': str(artifacts.session_dir),
                'created_at': metadata.get('created_at'),
                'parameter_count': len(artifacts.parameter_files),
                'midi_count': len(artifacts.midi_files),
                'audio_count': len(artifacts.audio_files),
                'total_files': (len(artifacts.parameter_files) + len(artifacts.midi_files) +
                               len(artifacts.render_files) + len(artifacts.audio_files) +
                               len(artifacts.log_files)),
                'metadata': metadata
            }
        except Exception as e:
            return {
                'session_id': session_id,
                'error': str(e)
            }
