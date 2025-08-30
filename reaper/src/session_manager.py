"""Session and artifact management."""

from pathlib import Path
from typing import Dict, Any
import json
import shutil
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from config import AutomationConfig, get_logger

# Set up module logger
logger = get_logger(__name__)


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

    def __init__(self, base_output_dir: Path = Path("./outputs")):
        self.base_output_dir = base_output_dir
        logger.info(f"SessionManager initialized with base_output_dir: {base_output_dir}")
        logger.debug(f"Base output directory exists: {base_output_dir.exists()}")

    def create_session_directory(self, session_id: str) -> Path:
        """Create and return session directory."""
        logger.debug(f"Creating session directory for session_id: {session_id}")
        session_dir = self.base_output_dir / f"session_{session_id}"

        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Session directory created: {session_dir}")
            logger.debug(f"Session directory permissions: {oct(session_dir.stat().st_mode)[-3:]}")
        except Exception as e:
            logger.error(f"Failed to create session directory {session_dir}: {e}")
            raise

        return session_dir

    def get_session_directory(self, session_id: str) -> Path:
        """Get session directory path."""
        session_dir = self.base_output_dir / f"session_{session_id}"
        logger.debug(f"Getting session directory for {session_id}: {session_dir}")
        return session_dir

    def create_session_config(self, session_id: str, config: AutomationConfig) -> Path:
        """Create session-specific config and return session directory."""
        logger.debug(f"Creating session config for session_id: {session_id}")
        logger.debug(f"Input config: workflow_mode={config.workflow_mode}, target_parameter={config.target_parameter}")

        session_dir = self.create_session_directory(session_id)

        # Update config with session directory
        config.session_id = session_id
        config.output_dir = session_dir

        logger.info(f"Session config created for {session_id}, output_dir: {session_dir}")
        return session_dir

    def save_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> Path:
        """Save session metadata to JSON file."""
        logger.debug(f"Saving session metadata for {session_id}")
        session_dir = self.get_session_directory(session_id)
        metadata_file = session_dir / "session_metadata.json"

        # Add timestamp
        metadata['created_at'] = datetime.now().isoformat()
        metadata['session_id'] = session_id

        logger.debug(f"Metadata keys: {list(metadata.keys())}")

        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Session metadata saved to: {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save session metadata to {metadata_file}: {e}")
            raise

        return metadata_file

    def load_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """Load session metadata from JSON file."""
        logger.debug(f"Loading session metadata for {session_id}")
        session_dir = self.get_session_directory(session_id)
        metadata_file = session_dir / "session_metadata.json"

        if not metadata_file.exists():
            logger.warning(f"Session metadata file not found: {metadata_file}")
            return {}

        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            logger.debug(f"Loaded metadata with {len(metadata)} keys")
            return metadata
        except Exception as e:
            logger.error(f"Failed to load session metadata from {metadata_file}: {e}")
            return {}

    def collect_session_artifacts(self, session_id: str) -> SessionArtifacts:
        """Collect all artifacts from a session directory."""
        logger.debug(f"Collecting artifacts for session {session_id}")
        session_dir = self.get_session_directory(session_id)

        if not session_dir.exists():
            logger.error(f"Session directory not found: {session_dir}")
            raise FileNotFoundError(f"Session directory not found: {session_dir}")

        # Collect different types of files
        logger.debug("Scanning for parameter files")
        parameter_files = list(session_dir.glob("params_*.txt")) + list(session_dir.glob("octave_change_*.txt"))
        logger.debug(f"Found {len(parameter_files)} parameter files")

        logger.debug("Scanning for MIDI files")
        midi_files = list(session_dir.glob("midi_notes_*.txt"))
        logger.debug(f"Found {len(midi_files)} MIDI files")

        logger.debug("Scanning for render files")
        render_files = list(session_dir.glob("render_log_*.txt"))
        logger.debug(f"Found {len(render_files)} render files")

        audio_files = []
        logger.debug("Scanning for log files")
        log_files = list(session_dir.glob("*.log"))
        logger.debug(f"Found {len(log_files)} log files")

        # Find audio files (they're in subdirectories)
        logger.debug("Scanning for audio files in subdirectories")
        for audio_dir in session_dir.glob("rendered_audio_*"):
            if audio_dir.is_dir():
                audio_files_in_dir = list(audio_dir.glob("*.wav"))
                logger.debug(f"Found {len(audio_files_in_dir)} audio files in {audio_dir.name}")
                audio_files.extend(audio_files_in_dir)

        total_artifacts = len(parameter_files) + len(midi_files) + len(render_files) + len(audio_files) + len(log_files)
        logger.info(f"Collected {total_artifacts} total artifacts for session {session_id}")

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
        logger.info(f"Cleaning up session {session_id}, keep_audio={keep_audio}")
        session_dir = self.get_session_directory(session_id)

        if not session_dir.exists():
            logger.warning(f"Session directory does not exist for cleanup: {session_dir}")
            return

        try:
            if keep_audio:
                # Remove only non-audio files
                logger.debug("Collecting artifacts for selective cleanup")
                artifacts = self.collect_session_artifacts(session_id)
                files_removed = 0
                for file_list in [artifacts.parameter_files, artifacts.midi_files,
                                 artifacts.render_files, artifacts.log_files]:
                    for file_path in file_list:
                        if file_path.exists():
                            logger.debug(f"Removing file: {file_path}")
                            file_path.unlink()
                            files_removed += 1
                logger.info(f"Removed {files_removed} non-audio files from session {session_id}")
            else:
                # Remove entire session directory
                logger.debug(f"Removing entire session directory: {session_dir}")
                shutil.rmtree(session_dir)
                logger.info(f"Completely removed session directory for {session_id}")
        except Exception as e:
            logger.error(f"Error during cleanup of session {session_id}: {e}")
            raise

    def list_sessions(self) -> list[str]:
        """List all available session IDs."""
        logger.debug(f"Listing sessions in {self.base_output_dir}")

        if not self.base_output_dir.exists():
            logger.warning(f"Base output directory does not exist: {self.base_output_dir}")
            return []

        sessions = []
        try:
            for session_dir in self.base_output_dir.iterdir():
                if session_dir.is_dir() and session_dir.name.startswith("session_"):
                    session_id = session_dir.name.replace("session_", "")
                    sessions.append(session_id)
                    logger.debug(f"Found session: {session_id}")
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

        logger.info(f"Found {len(sessions)} sessions")
        return sorted(sessions)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary information about a session."""
        logger.debug(f"Getting session summary for {session_id}")

        try:
            artifacts = self.collect_session_artifacts(session_id)
            metadata = self.load_session_metadata(session_id)

            summary = {
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

            logger.info(f"Session {session_id} summary: {summary['total_files']} total files, {summary['audio_count']} audio files")
            return summary

        except Exception as e:
            logger.error(f"Error getting session summary for {session_id}: {e}")
            return {
                'session_id': session_id,
                'error': str(e)
            }
