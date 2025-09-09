"""Refactored ArtifactManager using composition and dependency injection."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .directory_manager import (
    DirectoryManager, FileSystemDirectoryManager, ExperimentDirectoryStructure
)
from .data_persistence import (
    DataPersistence, StandardDataPersistence, FitnessLogger, ExperimentDataManager
)
from .artifact_collector import (
    ArtifactCollector, ReaperArtifactCollector, ExperimentCleaner, ExperimentAnalyzer
)

logger = logging.getLogger(__name__)


class ArtifactManager:
    """
    Manages experiment artifacts with proper directory structure using composition.

    This refactored version uses dependency injection and separates concerns into
    specialized components for directory management, data persistence, and artifact collection.
    """

    def __init__(
        self,
        experiment_name: str,
        base_dir: Optional[Path] = None,
        directory_manager: DirectoryManager = None,
        data_persistence: DataPersistence = None
    ):
        """Initialize ArtifactManager with injected dependencies.

        Args:
            experiment_name: Name of the experiment
            base_dir: Base directory for experiments (defaults to autodaw/experiment_results)
            directory_manager: Component for managing directories
            data_persistence: Component for data persistence
        """
        self.experiment_name = experiment_name

        # Set up default base directory
        if base_dir is None:
            base_dir = Path.cwd().parent / "experiment_results"

        # Inject dependencies with defaults
        self.directory_manager = directory_manager or FileSystemDirectoryManager()
        self.data_persistence = data_persistence or StandardDataPersistence()

        # Create composed components
        self.directory_structure = ExperimentDirectoryStructure(
            base_dir, experiment_name, self.directory_manager
        )
        self.data_manager = ExperimentDataManager(self.data_persistence)
        self.fitness_logger = FitnessLogger(self.data_persistence)
        self.artifact_collector = ReaperArtifactCollector(
            self.directory_manager, self.data_manager
        )
        self.cleaner = ExperimentCleaner(self.directory_manager)
        self.analyzer = ExperimentAnalyzer(self.data_manager)

        # Initialize directory structure
        self.directory_structure.initialize()

        logger.info(f"ArtifactManager initialized for experiment: {experiment_name}")
        logger.info(f"Experiment directory: {self.directory_structure.experiment_dir}")

    def set_target_audio(
        self,
        target_audio_path: Path,
        target_features: Optional[Dict] = None
    ) -> Path:
        """Set target audio file and optional features.

        Args:
            target_audio_path: Path to the target audio file
            target_features: Optional dictionary of audio features

        Returns:
            Path where the target audio was copied
        """
        if not target_audio_path.exists():
            raise FileNotFoundError(f"Target audio file not found: {target_audio_path}")

        # Copy target audio to target directory
        dest_audio_path = self.directory_structure.get_target_audio_path()
        copied_path = self.directory_manager.copy_file(target_audio_path, dest_audio_path)

        # Save features if provided
        if target_features:
            features_path = self.directory_structure.get_target_features_path()
            self.data_manager.save_target_features(features_path, target_features)

        logger.info(f"Target audio set: {target_audio_path} -> {copied_path}")
        return copied_path

    def create_generation_dir(self, generation: int) -> Path:
        """Create directory for a specific generation.

        Args:
            generation: Generation number

        Returns:
            Path to the created generation directory
        """
        gen_dir = self.directory_structure.create_generation_dir(generation)
        logger.info(f"Created generation directory: {gen_dir}")
        return gen_dir

    def collect_reaper_artifacts(
        self,
        generation: int,
        reaper_renders_dir: Path,
        individual_fitness: Optional[List[Tuple[int, float, Dict]]] = None
    ) -> List[Path]:
        """Collect artifacts from REAPER render directory.

        Args:
            generation: Generation number
            reaper_renders_dir: Directory containing REAPER renders
            individual_fitness: Optional fitness data for individuals

        Returns:
            List of collected artifact paths
        """
        generation_dir = self.directory_structure.get_generation_dir(generation)

        # Collect artifacts
        collected_files = self.artifact_collector.collect_artifacts(
            reaper_renders_dir, generation_dir, generation
        )

        # Log fitness data if provided
        if individual_fitness:
            self.log_generation_fitness(generation, individual_fitness)

        return collected_files

    def log_generation_fitness(
        self,
        generation: int,
        individual_fitness: List[Tuple[int, float, Dict]]
    ) -> None:
        """Log fitness data for a generation.

        Args:
            generation: Generation number
            individual_fitness: List of (individual_id, fitness, solution_data) tuples
        """
        self.fitness_logger.log_generation_fitness(
            self.directory_structure.fitness_log,
            generation,
            individual_fitness
        )
        logger.info(f"Logged fitness data for generation {generation}: {len(individual_fitness)} individuals")

    def get_target_audio(self) -> Optional[Path]:
        """Get path to target audio file if it exists."""
        target_path = self.directory_structure.get_target_audio_path()
        return target_path if target_path.exists() else None

    def get_target_features(self) -> Optional[Dict]:
        """Get target audio features if available."""
        features_path = self.directory_structure.get_target_features_path()
        return self.data_manager.load_target_features(features_path)

    def get_generation_individuals(self, generation: int) -> List[Path]:
        """Get list of individual files for a generation."""
        generation_dir = self.directory_structure.get_generation_dir(generation)
        return self.analyzer.get_generation_individuals(generation_dir)

    def get_generation_stats(self, generation: int) -> Optional[Dict]:
        """Get generation statistics if available."""
        generation_dir = self.directory_structure.get_generation_dir(generation)
        stats_path = generation_dir / "generation_metadata.json"
        return self.data_manager.load_generation_stats(stats_path)

    def list_experiment_structure(self) -> Dict[str, List[str]]:
        """List the structure of the experiment directory."""
        return self.analyzer.list_experiment_structure(
            self.directory_structure.experiment_dir
        )

    def cleanup_old_experiments(self, keep_latest: int = 5) -> List[Path]:
        """Clean up old experiment directories.

        Args:
            keep_latest: Number of latest experiments to keep

        Returns:
            List of removed experiment directories
        """
        return self.cleaner.cleanup_old_experiments(
            self.directory_structure.base_dir, keep_latest
        )


# Factory function for easy creation with standard dependencies
def create_standard_artifact_manager(
    experiment_name: str,
    base_dir: Optional[Path] = None
) -> ArtifactManager:
    """Create an ArtifactManager with standard dependencies."""
    return ArtifactManager(
        experiment_name=experiment_name,
        base_dir=base_dir,
        directory_manager=FileSystemDirectoryManager(),
        data_persistence=StandardDataPersistence()
    )


# Factory function for testing with mock dependencies
def create_mock_artifact_manager(
    experiment_name: str,
    base_dir: Optional[Path] = None
) -> ArtifactManager:
    """Create an ArtifactManager with mock dependencies for testing."""
    from .directory_manager import MockDirectoryManager
    from .data_persistence import MockDataPersistence

    return ArtifactManager(
        experiment_name=experiment_name,
        base_dir=base_dir or Path("/tmp/test_experiments"),
        directory_manager=MockDirectoryManager(),
        data_persistence=MockDataPersistence()
    )
