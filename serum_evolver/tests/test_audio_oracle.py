"""Unit tests for audio oracle components."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from serum_evolver.src.audio.oracle import AudioComparisonOracle, FrequencyTargetOracle


class TestAudioComparisonOracle:
    """Test cases for AudioComparisonOracle."""

    def test_initialization(self):
        """Test oracle initialization with default parameters."""
        oracle = AudioComparisonOracle(target_frequency=440.0)

        assert oracle.target_frequency == 440.0
        assert oracle.sr == 44100
        assert oracle.noise_level == 0.05
        assert isinstance(oracle.rng, np.random.RandomState)
        assert oracle._audio_cache == {}

    def test_initialization_with_custom_params(self):
        """Test oracle initialization with custom parameters."""
        oracle = AudioComparisonOracle(
            target_frequency=523.25,
            sr=48000,
            noise_level=0.1,
            random_seed=123
        )

        assert oracle.target_frequency == 523.25
        assert oracle.sr == 48000
        assert oracle.noise_level == 0.1
        assert oracle.rng.get_state()[1][0] == 123  # Check seed was set

    def test_set_target_frequency(self):
        """Test updating target frequency."""
        oracle = AudioComparisonOracle(target_frequency=440.0)
        oracle._audio_cache = {"test": "data"}  # Add some cache data

        oracle.set_target_frequency(523.25)

        assert oracle.target_frequency == 523.25
        assert oracle._audio_cache == {}  # Cache should be cleared

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        oracle = AudioComparisonOracle()
        oracle._audio_cache = {"file1": "data1", "file2": "data2"}

        oracle.clear_cache()

        assert oracle._audio_cache == {}

    def test_get_cache_info(self):
        """Test cache information retrieval."""
        oracle = AudioComparisonOracle()
        oracle._audio_cache = {"file1.wav": "data1", "file2.wav": "data2"}

        cache_info = oracle.get_cache_info()

        assert cache_info["cached_files"] == 2
        assert "file1.wav" in cache_info["cache_keys"]
        assert "file2.wav" in cache_info["cache_keys"]

    def test_calculate_win_probability_equal_distances(self):
        """Test win probability calculation with equal distances."""
        oracle = AudioComparisonOracle()

        prob = oracle._calculate_win_probability(100.0, 100.0)

        assert prob == 0.5

    def test_calculate_win_probability_different_distances(self):
        """Test win probability calculation with different distances."""
        oracle = AudioComparisonOracle()

        # Item A is closer (smaller distance should have higher probability)
        prob_a_closer = oracle._calculate_win_probability(50.0, 100.0)
        assert prob_a_closer > 0.5

        # Item B is closer
        prob_b_closer = oracle._calculate_win_probability(100.0, 50.0)
        assert prob_b_closer < 0.5

    @patch('serum_evolver.src.audio.oracle.librosa')
    def test_load_audio_success(self, mock_librosa):
        """Test successful audio loading."""
        mock_librosa.load.return_value = (np.array([1, 2, 3]), 44100)
        oracle = AudioComparisonOracle()

        # Create a mock Path that exists
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.__str__ = Mock(return_value="test.wav")

        result = oracle._load_audio(mock_path)

        np.testing.assert_array_equal(result, np.array([1, 2, 3]))
        mock_librosa.load.assert_called_once_with("test.wav", sr=44100, mono=True)

    def test_load_audio_file_not_found(self):
        """Test audio loading with non-existent file."""
        oracle = AudioComparisonOracle()

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = False

        with pytest.raises(FileNotFoundError):
            oracle._load_audio(mock_path)

    @patch('serum_evolver.src.audio.oracle.librosa')
    def test_estimate_fundamental_frequency_empty_audio(self, mock_librosa):
        """Test frequency estimation with empty audio."""
        oracle = AudioComparisonOracle()

        result = oracle._estimate_fundamental_frequency(np.array([]))

        assert result == 0.0

    @patch('serum_evolver.src.audio.oracle.librosa')
    def test_estimate_fundamental_frequency_with_pitches(self, mock_librosa):
        """Test frequency estimation with detected pitches."""
        oracle = AudioComparisonOracle()

        # Mock piptrack to return some pitch data
        mock_pitches = np.array([[0, 440, 0], [0, 0, 880]])  # 2 freq bins, 3 time frames
        mock_magnitudes = np.array([[0, 0.8, 0], [0, 0, 0.6]])
        mock_librosa.piptrack.return_value = (mock_pitches, mock_magnitudes)

        result = oracle._estimate_fundamental_frequency(np.array([1.0, 2.0, 3.0, 4.0, 5.0]))

        # Should return median of detected pitches (440 and 880)
        assert result == 660.0  # median of [440, 880]


class TestFrequencyTargetOracle:
    """Test cases for FrequencyTargetOracle."""

    @patch('serum_evolver.src.audio.oracle.librosa')
    def test_initialization_success(self, mock_librosa):
        """Test successful initialization with target audio file."""
        mock_librosa.load.return_value = (np.array([1, 2, 3]), 44100)

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.__str__ = Mock(return_value="target.wav")

        with patch.object(FrequencyTargetOracle, '_estimate_fundamental_frequency', return_value=440.0):
            oracle = FrequencyTargetOracle(target_audio_path=mock_path)

        assert oracle.target_frequency == 440.0
        assert oracle.target_audio_path == mock_path

    def test_initialization_file_not_found(self):
        """Test initialization with non-existent target file."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = False

        with patch('warnings.warn') as mock_warn:
            oracle = FrequencyTargetOracle(target_audio_path=mock_path)

        assert oracle.target_frequency == 440.0  # Should fallback to default
        mock_warn.assert_called()

    @patch('serum_evolver.src.audio.oracle.librosa')
    def test_initialization_load_error(self, mock_librosa):
        """Test initialization with audio loading error."""
        mock_librosa.load.side_effect = Exception("Load failed")

        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True

        with patch('warnings.warn') as mock_warn:
            oracle = FrequencyTargetOracle(target_audio_path=mock_path)

        assert oracle.target_frequency == 440.0  # Should fallback to default
        mock_warn.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
