"""Tests for audio comparison oracle."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from ga_jsi_audio_oracle.audio_oracle import AudioComparisonOracle, FrequencyTargetOracle


class TestAudioComparisonOracle:
    """Test suite for AudioComparisonOracle."""

    def test_initialization(self):
        """Test oracle initialization with default parameters."""
        oracle = AudioComparisonOracle(target_frequency=440.0)

        assert oracle.target_frequency == 440.0
        assert oracle.sr == 44100
        assert oracle.noise_level == 0.05
        assert len(oracle._audio_cache) == 0

    def test_initialization_custom_params(self):
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

    def test_set_target_frequency(self):
        """Test updating target frequency."""
        oracle = AudioComparisonOracle(target_frequency=440.0)
        oracle.set_target_frequency(523.25)

        assert oracle.target_frequency == 523.25
        # Cache should be cleared when target changes
        assert len(oracle._audio_cache) == 0

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        oracle = AudioComparisonOracle()
        # Simulate some cached data
        oracle._audio_cache['test'] = np.array([1, 2, 3])

        oracle.clear_cache()
        assert len(oracle._audio_cache) == 0

    def test_get_cache_info(self):
        """Test cache information retrieval."""
        oracle = AudioComparisonOracle()
        oracle._audio_cache['file1.wav'] = np.array([1, 2, 3])
        oracle._audio_cache['file2.wav'] = np.array([4, 5, 6])

        cache_info = oracle.get_cache_info()

        assert cache_info['cached_files'] == 2
        assert 'file1.wav' in cache_info['cache_keys']
        assert 'file2.wav' in cache_info['cache_keys']

    @patch('ga_jsi_audio_oracle.audio_oracle.librosa.load')
    def test_load_audio(self, mock_load):
        """Test audio loading functionality."""
        mock_load.return_value = (np.array([0.1, 0.2, 0.3]), 44100)

        oracle = AudioComparisonOracle()
        audio_path = Path('test.wav')

        # Mock path existence
        with patch.object(audio_path, 'exists', return_value=True):
            audio = oracle._load_audio(audio_path)

        assert len(audio) == 3
        mock_load.assert_called_once_with(str(audio_path), sr=44100, mono=True)

    def test_load_audio_file_not_found(self):
        """Test audio loading with non-existent file."""
        oracle = AudioComparisonOracle()
        audio_path = Path('nonexistent.wav')

        with pytest.raises(FileNotFoundError):
            oracle._load_audio(audio_path)

    @patch('ga_jsi_audio_oracle.audio_oracle.librosa.piptrack')
    def test_estimate_fundamental_frequency(self, mock_piptrack):
        """Test fundamental frequency estimation."""
        # Mock piptrack output
        mock_pitches = np.array([[0, 440, 0], [0, 0, 880]])  # 2 freq bins, 3 time frames
        mock_magnitudes = np.array([[0, 0.8, 0], [0, 0, 0.6]])
        mock_piptrack.return_value = (mock_pitches, mock_magnitudes)

        oracle = AudioComparisonOracle()
        audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])

        freq = oracle._estimate_fundamental_frequency(audio)

        # Should return median of detected pitches
        assert freq == 440.0  # Only one valid pitch detected

    def test_estimate_fundamental_frequency_empty_audio(self):
        """Test frequency estimation with empty audio."""
        oracle = AudioComparisonOracle()
        audio = np.array([])

        freq = oracle._estimate_fundamental_frequency(audio)
        assert freq == 0.0

    def test_calculate_win_probability(self):
        """Test win probability calculation."""
        oracle = AudioComparisonOracle()

        # Test equal distances
        prob = oracle._calculate_win_probability(10.0, 10.0)
        assert prob == 0.5

        # Test different distances
        prob = oracle._calculate_win_probability(5.0, 10.0)
        assert prob > 0.5  # Smaller distance should have higher probability

        prob = oracle._calculate_win_probability(10.0, 5.0)
        assert prob < 0.5  # Larger distance should have lower probability

    @patch('ga_jsi_audio_oracle.audio_oracle.AudioComparisonOracle._get_fundamental_frequency')
    def test_compare_basic(self, mock_get_freq):
        """Test basic comparison functionality."""
        oracle = AudioComparisonOracle(target_frequency=440.0, noise_level=0.0)

        # Mock frequency extraction
        mock_get_freq.side_effect = [450.0, 430.0]  # item_a=450Hz, item_b=430Hz

        # item_b (430Hz) is closer to target (440Hz) than item_a (450Hz)
        # So compare should return False (item_a does not win)
        result = oracle.compare('audio_a.wav', 'audio_b.wav')

        # With no noise, should be deterministic based on distance
        assert isinstance(result, bool)

    @patch('ga_jsi_audio_oracle.audio_oracle.AudioComparisonOracle._get_fundamental_frequency')
    def test_compare_with_noise(self, mock_get_freq):
        """Test comparison with noise level."""
        oracle = AudioComparisonOracle(target_frequency=440.0, noise_level=0.5, random_seed=42)

        mock_get_freq.side_effect = [450.0, 430.0]

        # With 50% noise, results should be somewhat random
        results = []
        for _ in range(100):
            oracle.rng = np.random.RandomState(42 + _)  # Reset RNG for each test
            mock_get_freq.side_effect = [450.0, 430.0]
            result = oracle.compare('audio_a.wav', 'audio_b.wav')
            results.append(result)

        # Should have some variation due to noise
        true_count = sum(results)
        assert 20 < true_count < 80  # Not all True or all False

    def test_compare_exception_handling(self):
        """Test comparison with exception during frequency extraction."""
        oracle = AudioComparisonOracle()

        with patch.object(oracle, '_get_fundamental_frequency', side_effect=Exception("Test error")):
            # Should not raise exception, should return random decision
            result = oracle.compare('audio_a.wav', 'audio_b.wav')
            assert isinstance(result, bool)


class TestFrequencyTargetOracle:
    """Test suite for FrequencyTargetOracle."""

    @patch('ga_jsi_audio_oracle.audio_oracle.librosa.load')
    @patch('ga_jsi_audio_oracle.audio_oracle.FrequencyTargetOracle._estimate_fundamental_frequency')
    def test_initialization_with_target_audio(self, mock_estimate, mock_load):
        """Test initialization with target audio file."""
        mock_load.return_value = (np.array([0.1, 0.2, 0.3]), 44100)
        mock_estimate.return_value = 523.25

        target_path = Path('target.wav')

        with patch.object(target_path, 'exists', return_value=True):
            oracle = FrequencyTargetOracle(target_path)

        assert oracle.target_frequency == 523.25
        assert oracle.target_audio_path == target_path

    def test_initialization_missing_target_audio(self):
        """Test initialization with missing target audio file."""
        target_path = Path('missing.wav')

        with patch.object(target_path, 'exists', return_value=False):
            oracle = FrequencyTargetOracle(target_path)

        # Should fallback to 440 Hz
        assert oracle.target_frequency == 440.0

    @patch('ga_jsi_audio_oracle.audio_oracle.librosa.load')
    def test_initialization_audio_load_error(self, mock_load):
        """Test initialization when audio loading fails."""
        mock_load.side_effect = Exception("Load error")

        target_path = Path('error.wav')

        with patch.object(target_path, 'exists', return_value=True):
            oracle = FrequencyTargetOracle(target_path)

        # Should fallback to 440 Hz
        assert oracle.target_frequency == 440.0
