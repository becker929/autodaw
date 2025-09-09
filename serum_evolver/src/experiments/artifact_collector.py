"""Artifact collection and organization utilities."""

from pathlib import Path
from typing import List, Dict, Any, Protocol
import logging

logger = logging.getLogger(__name__)


class ArtifactCollector(Protocol):
    """Protocol for collecting artifacts from REAPER renders."""

    def collect_artifacts(
        self,
        source_dir: Path,
        destination_dir: Path,
        generation: int
    ) -> List[Path]:
        """Collect artifacts from source to destination."""
        ...


class ReaperArtifactCollector:
    """Collects artifacts from REAPER render directory."""

    def __init__(self, directory_manager, data_manager):
        self.directory_manager = directory_manager
        self.data_manager = data_manager

    def collect_artifacts(
        self,
        source_dir: Path,
        destination_dir: Path,
        generation: int
    ) -> List[Path]:
        """Collect REAPER artifacts and organize them."""
        if not source_dir.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            return []

        # Ensure destination exists
        self.directory_manager.ensure_directory(destination_dir)

        collected_files = []

        # Collect WAV files
        for wav_file in source_dir.glob("*.wav"):
            dest_path = destination_dir / wav_file.name
            copied_path = self.directory_manager.copy_file(wav_file, dest_path)
            collected_files.append(copied_path)
            logger.info(f"Collected audio: {wav_file.name}")

        # Collect RPP files (REAPER project files)
        for rpp_file in source_dir.glob("*.rpp"):
            dest_path = destination_dir / rpp_file.name
            copied_path = self.directory_manager.copy_file(rpp_file, dest_path)
            collected_files.append(copied_path)
            logger.info(f"Collected project: {rpp_file.name}")

        # Create generation metadata
        metadata = {
            'generation': generation,
            'collected_files': [str(f) for f in collected_files],
            'source_directory': str(source_dir),
            'collection_timestamp': str(Path().cwd())  # Simplified timestamp
        }

        metadata_path = destination_dir / "generation_metadata.json"
        self.data_manager.save_generation_stats(metadata_path, metadata)

        return collected_files


class ExperimentCleaner:
    """Handles cleanup of old experiments."""

    def __init__(self, directory_manager):
        self.directory_manager = directory_manager

    def cleanup_old_experiments(self, base_dir: Path, keep_latest: int = 5) -> List[Path]:
        """Clean up old experiment directories, keeping only the latest N."""
        if not base_dir.exists():
            return []

        # Get all experiment directories
        experiment_dirs = [d for d in base_dir.iterdir() if d.is_dir()]

        if len(experiment_dirs) <= keep_latest:
            return []

        # Sort by modification time (newest first)
        experiment_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Remove oldest directories
        to_remove = experiment_dirs[keep_latest:]
        removed_dirs = []

        for old_dir in to_remove:
            logger.info(f"Removing old experiment: {old_dir}")
            self.directory_manager.remove_directory(old_dir)
            removed_dirs.append(old_dir)

        return removed_dirs


class ExperimentAnalyzer:
    """Analyzes experiment structure and provides insights."""

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def list_experiment_structure(self, experiment_dir: Path) -> Dict[str, List[str]]:
        """List the structure of an experiment directory."""
        if not experiment_dir.exists():
            return {}

        structure = {}

        # List top-level contents
        structure['root'] = [item.name for item in experiment_dir.iterdir()]

        # List generation directories
        generation_dirs = [d for d in experiment_dir.iterdir()
                          if d.is_dir() and d.name.startswith('generation_')]
        structure['generations'] = [d.name for d in generation_dirs]

        # List target files
        target_dir = experiment_dir / "target"
        if target_dir.exists():
            structure['target'] = [item.name for item in target_dir.iterdir()]

        return structure

    def get_generation_individuals(self, generation_dir: Path) -> List[Path]:
        """Get list of individual files in a generation directory."""
        if not generation_dir.exists():
            return []

        # Look for audio files (individuals)
        audio_files = list(generation_dir.glob("*.wav"))
        return sorted(audio_files)

    def analyze_experiment_progress(self, experiment_dir: Path) -> Dict[str, Any]:
        """Analyze the progress of an experiment."""
        structure = self.list_experiment_structure(experiment_dir)

        analysis = {
            'total_generations': len(structure.get('generations', [])),
            'has_target': 'target' in structure,
            'has_config': 'experiment_config.json' in structure.get('root', []),
            'has_fitness_log': 'fitness_log.csv' in structure.get('root', [])
        }

        return analysis
