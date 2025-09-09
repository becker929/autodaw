"""
REAPER integration for genetic algorithm optimization.
Handles session execution, audio rendering, and result collection.
"""

import subprocess
import os
import signal
from pathlib import Path
from typing import Dict
from .config import SessionConfig


class ReaperExecutor:
    """Execute REAPER sessions and collect rendered audio"""

    def __init__(
        self,
        reaper_project_path: Path,
        session_configs_dir: Path = None,
        renders_dir: Path = None,
        timeout: int = 120
    ):
        """Initialize REAPER executor with project paths"""
        self.reaper_project_path = reaper_project_path
        self.session_configs_dir = session_configs_dir or reaper_project_path / "session-configs"
        self.renders_dir = renders_dir or reaper_project_path / "renders"
        self.timeout = timeout

        # Ensure directories exist
        self.session_configs_dir.mkdir(exist_ok=True)
        self.renders_dir.mkdir(exist_ok=True)

    def execute_session(self, session_config: SessionConfig) -> Dict[str, Path]:
        """Execute REAPER session and return paths to rendered audio files"""
        # Save session config to file
        session_file = self.session_configs_dir / f"{session_config.session_name}.json"
        session_config.save_to_file(session_file)

        # Execute REAPER with session
        render_paths = self._run_reaper_session(session_config.session_name)

        return render_paths

    def _run_reaper_session(self, session_name: str) -> Dict[str, Path]:
        """Run REAPER with the specified session configuration"""
        # Change to REAPER project directory
        original_cwd = os.getcwd()

        try:
            os.chdir(self.reaper_project_path)

            # Start REAPER in background
            cmd = ["uv", "run", "python", "main.py"]

            print(f"Executing REAPER session: {session_name}")
            print(f"Command: {' '.join(cmd)}")
            print(f"Working directory: {self.reaper_project_path}")

            # Run the process and wait for completion
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Create new process group for clean termination
            )

            try:
                stdout, stderr = process.communicate(timeout=self.timeout)

                if process.returncode != 0:
                    raise RuntimeError(f"REAPER execution failed with code {process.returncode}:\n{stderr}")

                print(f"REAPER session completed successfully")
                if stdout.strip():
                    print(f"STDOUT: {stdout}")

            except subprocess.TimeoutExpired:
                # Kill the entire process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                raise RuntimeError(f"REAPER session timed out after {self.timeout} seconds")

            # Collect rendered audio files
            render_paths = self._collect_rendered_files(session_name)
            return render_paths

        finally:
            os.chdir(original_cwd)

    def _collect_rendered_files(self, session_name: str) -> Dict[str, Path]:
        """Collect rendered audio files from the renders directory"""
        render_paths = {}

        # Look for directories matching the session pattern
        for render_dir in self.renders_dir.iterdir():
            if render_dir.is_dir() and session_name in render_dir.name:
                # Look for audio files in the render directory
                for audio_file in render_dir.glob("*.wav"):
                    # Extract render_id from directory name
                    render_id = self._extract_render_id(render_dir.name, session_name)
                    render_paths[render_id] = audio_file
                    print(f"Found rendered audio: {render_id} -> {audio_file}")

        return render_paths

    def _extract_render_id(self, dir_name: str, session_name: str) -> str:
        """Extract render ID from directory name"""
        # Directory format: session_name_render_id_timestamp_params
        parts = dir_name.split('_')
        if len(parts) >= 2:
            # Find session_name in parts and get the next part as render_id
            try:
                session_idx = parts.index(session_name.replace('_', ''))
                if session_idx + 1 < len(parts):
                    return parts[session_idx + 1]
            except ValueError:
                pass

        # Fallback: use the directory name
        return dir_name
