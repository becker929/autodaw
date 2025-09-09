"""Directory management for experiments."""

import shutil
from pathlib import Path
from typing import Optional, Protocol


class DirectoryManager(Protocol):
    """Protocol for managing experiment directories."""

    def ensure_directory(self, path: Path) -> Path:
        """Ensure directory exists, create if necessary."""
        ...

    def copy_file(self, source: Path, destination: Path) -> Path:
        """Copy file from source to destination."""
        ...

    def remove_directory(self, path: Path) -> None:
        """Remove directory and all contents."""
        ...


class FileSystemDirectoryManager:
    """Standard filesystem-based directory manager."""

    def ensure_directory(self, path: Path) -> Path:
        """Ensure directory exists, create if necessary."""
        path.mkdir(parents=True, exist_ok=True)
        return path

    def copy_file(self, source: Path, destination: Path) -> Path:
        """Copy file from source to destination."""
        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        return Path(shutil.copy2(source, destination))

    def remove_directory(self, path: Path) -> None:
        """Remove directory and all contents."""
        if path.exists():
            shutil.rmtree(path)


class MockDirectoryManager:
    """Mock directory manager for testing."""

    def __init__(self):
        self.created_directories = []
        self.copied_files = []
        self.removed_directories = []

    def ensure_directory(self, path: Path) -> Path:
        """Mock directory creation."""
        self.created_directories.append(path)
        return path

    def copy_file(self, source: Path, destination: Path) -> Path:
        """Mock file copying."""
        self.copied_files.append((source, destination))
        return destination

    def remove_directory(self, path: Path) -> None:
        """Mock directory removal."""
        self.removed_directories.append(path)


class ExperimentDirectoryStructure:
    """Manages the standard experiment directory structure."""

    def __init__(self, base_dir: Path, experiment_name: str, directory_manager: DirectoryManager):
        self.base_dir = base_dir
        self.experiment_name = experiment_name
        self.directory_manager = directory_manager

        # Define structure
        self.experiment_dir = base_dir / experiment_name
        self.target_dir = self.experiment_dir / "target"
        self.config_file = self.experiment_dir / "experiment_config.json"
        self.log_file = self.experiment_dir / "experiment_log.txt"
        self.fitness_log = self.experiment_dir / "fitness_log.csv"

    def initialize(self) -> None:
        """Initialize the experiment directory structure."""
        self.directory_manager.ensure_directory(self.experiment_dir)
        self.directory_manager.ensure_directory(self.target_dir)

    def get_generation_dir(self, generation: int) -> Path:
        """Get path to generation directory."""
        return self.experiment_dir / f"generation_{generation:03d}"

    def create_generation_dir(self, generation: int) -> Path:
        """Create and return generation directory."""
        gen_dir = self.get_generation_dir(generation)
        return self.directory_manager.ensure_directory(gen_dir)

    def get_target_audio_path(self) -> Path:
        """Get path for target audio file."""
        return self.target_dir / "reference.wav"

    def get_target_features_path(self) -> Path:
        """Get path for target features file."""
        return self.target_dir / "features.json"
