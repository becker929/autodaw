"""Unit tests for artifact manager."""

import pytest
import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from serum_evolver.src.experiments.artifact_manager import ArtifactManager


class TestArtifactManager:
    """Test cases for ArtifactManager."""

    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_initialization(self, mock_file, mock_mkdir):
        """Test artifact manager initialization."""
        with patch('serum_evolver.src.experiments.artifact_manager.Path.exists', return_value=False):
            manager = ArtifactManager("test_experiment")

        assert manager.experiment_name == "test_experiment"
        assert manager.experiment_dir.name == "test_experiment"
        assert manager.target_dir.name == "target"
        mock_mkdir.assert_called()
        # Should create fitness_log.csv
        mock_file.assert_called()

    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    @patch('serum_evolver.src.experiments.artifact_manager.Path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    def test_initialization_with_custom_base_dir(self, mock_file, mock_exists, mock_mkdir):
        """Test initialization with custom base directory."""
        custom_base = Path("/custom/path")
        manager = ArtifactManager("test_experiment", base_dir=custom_base)

        assert manager.base_dir == custom_base
        assert manager.experiment_dir == custom_base / "test_experiment"

    @patch('serum_evolver.src.experiments.artifact_manager.Path.exists')
    @patch('serum_evolver.src.experiments.artifact_manager.shutil.copy2')
    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_set_target_audio_success(self, mock_mkdir, mock_file, mock_copy, mock_exists):
        """Test setting target audio successfully."""
        mock_exists.return_value = True

        manager = ArtifactManager("test_experiment")

        target_path = Path("source_audio.wav")
        target_features = {"spectral_centroid": 2000.0}

        result = manager.set_target_audio(target_path, target_features)

        expected_dest = manager.target_dir / "reference.wav"
        assert result == expected_dest
        mock_copy.assert_called_once_with(target_path, expected_dest)

        # Check that features were saved - should be called at least once for features
        assert mock_file.call_count >= 1

    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_set_target_audio_file_not_found(self, mock_mkdir, mock_file):
        """Test setting target audio with non-existent file."""
        manager = ArtifactManager("test_experiment")

        non_existent_path = Path("non_existent.wav")

        with pytest.raises(FileNotFoundError):
            manager.set_target_audio(non_existent_path)

    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_create_generation_dir(self, mock_mkdir, mock_file):
        """Test creating generation directory."""
        manager = ArtifactManager("test_experiment")

        gen_dir = manager.create_generation_dir(5)

        expected_dir = manager.experiment_dir / "generation_005"
        assert gen_dir == expected_dir
        # mkdir should be called for experiment, target, generation, and individuals dirs
        assert mock_mkdir.call_count >= 2

    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    @patch('serum_evolver.src.experiments.artifact_manager.Path.glob')
    @patch('serum_evolver.src.experiments.artifact_manager.shutil.copy2')
    @patch('serum_evolver.src.experiments.artifact_manager.time.time', return_value=1000.0)
    def test_collect_reaper_artifacts(self, mock_time, mock_copy, mock_glob, mock_mkdir, mock_file):
        """Test collecting artifacts from REAPER renders directory."""
        manager = ArtifactManager("test_experiment")

        # Mock WAV files with recent timestamps
        mock_wav1 = Mock()
        mock_wav1.stat.return_value.st_mtime = 999.0  # 1 second ago
        mock_wav2 = Mock()
        mock_wav2.stat.return_value.st_mtime = 998.0  # 2 seconds ago

        mock_glob.return_value = [mock_wav1, mock_wav2]

        session_config_path = Mock()
        session_config_path.exists.return_value = True

        count, audio_paths = manager.collect_reaper_artifacts(
            generation=1,
            reaper_renders_dir=Path("renders"),
            session_config_path=session_config_path
        )

        assert count == 2
        assert len(audio_paths) == 2
        assert mock_copy.call_count >= 2  # Should copy session config + audio files

    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_log_generation_fitness(self, mock_mkdir, mock_file):
        """Test logging generation fitness results."""
        manager = ArtifactManager("test_experiment")

        fitness_data = [
            (0, 0.8, {"param1": 0.5}),
            (1, 0.6, {"param1": 0.7})
        ]

        with patch('serum_evolver.src.experiments.artifact_manager.Path.exists', return_value=True):
            manager.log_generation_fitness(1, fitness_data)

        # Should write to both CSV and JSON files
        assert mock_file.call_count >= 2

    @patch('serum_evolver.src.experiments.artifact_manager.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='{"spectral_centroid": 2000.0}')
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_get_target_features(self, mock_mkdir, mock_file, mock_exists):
        """Test retrieving target features."""
        manager = ArtifactManager("test_experiment")

        features = manager.get_target_features()

        assert features is not None
        assert features["spectral_centroid"] == 2000.0

    @patch('serum_evolver.src.experiments.artifact_manager.Path.exists', return_value=False)
    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_get_target_features_not_found(self, mock_mkdir, mock_file, mock_exists):
        """Test retrieving target features when file doesn't exist."""
        manager = ArtifactManager("test_experiment")

        features = manager.get_target_features()

        assert features is None

    @patch('serum_evolver.src.experiments.artifact_manager.Path.glob')
    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_get_generation_individuals(self, mock_mkdir, mock_file, mock_glob):
        """Test retrieving individual audio files for a generation."""
        manager = ArtifactManager("test_experiment")

        mock_files = [Path("individual_000.wav"), Path("individual_001.wav")]
        mock_glob.return_value = mock_files

        with patch('serum_evolver.src.experiments.artifact_manager.Path.exists', return_value=True):
            individuals = manager.get_generation_individuals(1)

        assert len(individuals) == 2
        assert all(isinstance(path, Path) for path in individuals)

    @patch('serum_evolver.src.experiments.artifact_manager.Path.iterdir')
    @patch('serum_evolver.src.experiments.artifact_manager.Path.exists')
    @patch('serum_evolver.src.experiments.artifact_manager.Path.glob')
    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_list_experiment_structure(self, mock_mkdir, mock_file, mock_glob, mock_exists, mock_iterdir):
        """Test listing experiment directory structure."""
        manager = ArtifactManager("test_experiment")

        # Mock directory structure
        mock_target_file = Mock()
        mock_target_file.relative_to.return_value = Path("target/reference.wav")
        mock_target_file.is_file.return_value = True

        mock_gen_dir = Mock()
        mock_gen_dir.name = "generation_001"
        mock_gen_dir.is_dir.return_value = True
        # Mock the path operations for generation directory
        mock_individuals_dir = Mock()
        mock_individuals_dir.exists.return_value = True
        mock_individuals_dir.glob.return_value = [Path("file1.wav")]
        mock_gen_dir.__truediv__ = Mock(return_value=mock_individuals_dir)

        mock_exists.return_value = True
        mock_iterdir.side_effect = [
            [mock_target_file],  # target_dir contents
        ]
        mock_glob.return_value = [mock_gen_dir]

        structure = manager.list_experiment_structure()

        assert "target" in structure
        assert "generations" in structure
        assert "logs" in structure

    @patch('serum_evolver.src.experiments.artifact_manager.Path.iterdir')
    @patch('serum_evolver.src.experiments.artifact_manager.shutil.rmtree')
    @patch('builtins.open', new_callable=mock_open)
    @patch('serum_evolver.src.experiments.artifact_manager.Path.mkdir')
    def test_cleanup_old_experiments(self, mock_mkdir, mock_file, mock_rmtree, mock_iterdir):
        """Test cleaning up old experiment directories."""
        manager = ArtifactManager("test_experiment")

        # Mock old experiment directories
        old_exp1 = Mock()
        old_exp1.is_dir.return_value = True
        old_exp1.stat.return_value.st_ctime = 100

        old_exp2 = Mock()
        old_exp2.is_dir.return_value = True
        old_exp2.stat.return_value.st_ctime = 200

        current_exp = Mock()
        current_exp.is_dir.return_value = True
        current_exp.stat.return_value.st_ctime = 300

        mock_iterdir.return_value = [old_exp1, old_exp2, current_exp]

        with patch('serum_evolver.src.experiments.artifact_manager.Path.exists', return_value=True):
            manager.cleanup_old_experiments(keep_latest=2)

        # Should remove the oldest experiment
        mock_rmtree.assert_called_once_with(old_exp1)


if __name__ == "__main__":
    pytest.main([__file__])
