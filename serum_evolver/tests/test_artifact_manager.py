"""Unit tests for refactored artifact manager."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from serum_evolver.src.experiments.artifact_manager import (
    ArtifactManager, create_mock_artifact_manager
)
from serum_evolver.src.experiments.directory_manager import MockDirectoryManager
from serum_evolver.src.experiments.data_persistence import MockDataPersistence


class TestArtifactManager:
    """Test cases for refactored ArtifactManager."""

    def test_initialization(self):
        """Test artifact manager initialization."""
        manager = create_mock_artifact_manager("test_experiment", Path("/tmp/test"))

        assert manager.experiment_name == "test_experiment"
        assert manager.directory_structure.experiment_name == "test_experiment"
        assert manager.directory_structure.target_dir.name == "target"

    def test_initialization_with_custom_base_dir(self):
        """Test initialization with custom base directory."""
        custom_base = Path("/custom/path")
        manager = create_mock_artifact_manager("test_experiment", custom_base)

        assert manager.directory_structure.base_dir == custom_base
        assert manager.directory_structure.experiment_dir == custom_base / "test_experiment"

    def test_set_target_audio_success(self):
        """Test setting target audio successfully."""
        manager = create_mock_artifact_manager("test_experiment")

        # Create a temporary file to simulate target audio
        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            target_path = Path(temp_file.name)

            # The temporary file exists, so we can call set_target_audio
            features = {"frequency": 440.0, "amplitude": 0.8}
            result_path = manager.set_target_audio(target_path, features)

            # Check that the mock directory manager was called
            assert len(manager.directory_manager.copied_files) == 1
            source, dest = manager.directory_manager.copied_files[0]
            assert source == target_path

    def test_set_target_audio_file_not_found(self):
        """Test setting target audio with non-existent file."""
        manager = create_mock_artifact_manager("test_experiment")

        non_existent_path = Path("/non/existent/file.wav")

        with pytest.raises(FileNotFoundError):
            manager.set_target_audio(non_existent_path)

    def test_create_generation_dir(self):
        """Test creating generation directory."""
        manager = create_mock_artifact_manager("test_experiment")

        gen_dir = manager.create_generation_dir(1)

        # Check that directory was created
        assert len(manager.directory_manager.created_directories) >= 1
        assert gen_dir.name == "generation_001"

    def test_collect_reaper_artifacts(self):
        """Test collecting REAPER artifacts."""
        manager = create_mock_artifact_manager("test_experiment")

        # Create temporary source directory
        with tempfile.TemporaryDirectory() as temp_dir:
            source_dir = Path(temp_dir)

            # The temporary directory exists by default
            fitness_data = [(0, 0.8, {"octave": 0.5, "fine": -0.3})]

            collected = manager.collect_reaper_artifacts(1, source_dir, fitness_data)

            # Should have attempted to collect artifacts
            assert isinstance(collected, list)

    def test_log_generation_fitness(self):
        """Test logging generation fitness data."""
        manager = create_mock_artifact_manager("test_experiment")

        fitness_data = [
            (0, 0.8, {"octave": 0.5, "fine": -0.3}),
            (1, 0.6, {"octave": -0.2, "fine": 0.7})
        ]

        manager.log_generation_fitness(1, fitness_data)

        # Check that CSV rows were logged
        assert len(manager.data_persistence.csv_rows) == 2

    def test_get_target_features(self):
        """Test getting target features."""
        manager = create_mock_artifact_manager("test_experiment")

        # Set some features first
        features = {"frequency": 440.0, "amplitude": 0.8}
        features_path = manager.directory_structure.get_target_features_path()
        manager.data_manager.save_target_features(features_path, features)

        # Now retrieve them
        retrieved_features = manager.get_target_features()
        assert retrieved_features == features

    def test_get_target_features_not_found(self):
        """Test getting target features when file doesn't exist."""
        manager = create_mock_artifact_manager("test_experiment")

        features = manager.get_target_features()
        assert features is None

    def test_get_generation_individuals(self):
        """Test getting generation individuals."""
        manager = create_mock_artifact_manager("test_experiment")

        # Mock the analyzer to return some individuals
        manager.analyzer.get_generation_individuals = Mock(return_value=[
            Path("/test/individual_001.wav"),
            Path("/test/individual_002.wav")
        ])

        individuals = manager.get_generation_individuals(1)
        assert len(individuals) == 2
        assert all(path.suffix == ".wav" for path in individuals)

    def test_list_experiment_structure(self):
        """Test listing experiment structure."""
        manager = create_mock_artifact_manager("test_experiment")

        # Mock the analyzer to return structure
        manager.analyzer.list_experiment_structure = Mock(return_value={
            'root': ['experiment_config.json', 'fitness_log.csv'],
            'generations': ['generation_001', 'generation_002'],
            'target': ['reference.wav', 'features.json']
        })

        structure = manager.list_experiment_structure()
        assert 'root' in structure
        assert 'generations' in structure
        assert 'target' in structure

    def test_cleanup_old_experiments(self):
        """Test cleaning up old experiments."""
        manager = create_mock_artifact_manager("test_experiment")

        # Mock the cleaner to return removed directories
        manager.cleaner.cleanup_old_experiments = Mock(return_value=[
            Path("/old/experiment1"),
            Path("/old/experiment2")
        ])

        removed = manager.cleanup_old_experiments(keep_latest=3)
        assert len(removed) == 2
