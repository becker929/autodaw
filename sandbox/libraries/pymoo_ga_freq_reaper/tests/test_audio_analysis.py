"""
Unit tests for audio analysis module.
"""

import pytest
import numpy as np
import tempfile
import soundfile as sf
from pathlib import Path
from ga_frequency_demo.audio_analysis import (
    FrequencyDistanceCalculator, create_target_audio_generator
)


@pytest.fixture
def sample_audio():
    """Create a sample audio signal for testing"""
    sr = 44100
    duration = 1.0  # 1 second
    t = np.linspace(0, duration, int(sr * duration), False)

    # Create a simple sine wave at 440 Hz
    frequency = 440.0
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    return audio, sr


@pytest.fixture
def temp_audio_file(sample_audio):
    """Create a temporary audio file for testing"""
    audio, sr = sample_audio

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = Path(f.name)

    # Write audio to file
    sf.write(temp_path, audio, sr)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestFrequencyDistanceCalculator:
    def test_calculator_initialization(self):
        calc = FrequencyDistanceCalculator()

        assert calc.sr == 44100
        assert calc.n_fft == 2048
        assert calc.hop_length == 512

        # Test custom parameters
        calc_custom = FrequencyDistanceCalculator(sr=48000, n_fft=1024, hop_length=256)
        assert calc_custom.sr == 48000
        assert calc_custom.n_fft == 1024
        assert calc_custom.hop_length == 256

    def test_load_audio(self, temp_audio_file):
        calc = FrequencyDistanceCalculator()

        audio = calc.load_audio(temp_audio_file)

        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0
        assert audio.dtype == np.float32

    def test_load_audio_nonexistent_file(self):
        calc = FrequencyDistanceCalculator()

        with pytest.raises(FileNotFoundError):
            calc.load_audio(Path("nonexistent_file.wav"))

    def test_compute_spectral_features(self, sample_audio):
        calc = FrequencyDistanceCalculator()
        audio, _ = sample_audio

        features = calc.compute_spectral_features(audio)

        # Check that all expected features are present
        expected_features = [
            'spectral_centroid', 'spectral_bandwidth', 'spectral_rolloff',
            'mfccs', 'chroma', 'magnitude_spectrum'
        ]

        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], np.ndarray)
            assert features[feature].size > 0

        # Check feature dimensions
        assert features['spectral_centroid'].ndim == 1
        assert features['spectral_bandwidth'].ndim == 1
        assert features['spectral_rolloff'].ndim == 1
        assert features['mfccs'].ndim == 2
        assert features['chroma'].ndim == 2
        assert features['magnitude_spectrum'].ndim == 2

    def test_compute_frequency_distance_same_audio(self, sample_audio):
        calc = FrequencyDistanceCalculator()
        audio, _ = sample_audio

        # Distance between identical audio should be very small
        distance = calc.compute_frequency_distance(audio, audio)

        assert distance >= 0
        assert distance < 1e-6  # Should be nearly zero

    def test_compute_frequency_distance_different_audio(self, sample_audio):
        calc = FrequencyDistanceCalculator()
        audio1, sr = sample_audio

        # Create a different audio signal (different frequency)
        t = np.linspace(0, 1.0, len(audio1), False)
        audio2 = 0.5 * np.sin(2 * np.pi * 880.0 * t)  # 880 Hz instead of 440 Hz

        distance = calc.compute_frequency_distance(audio1, audio2)

        assert distance > 0
        assert isinstance(distance, float)

    def test_compute_frequency_distance_custom_weights(self, sample_audio):
        calc = FrequencyDistanceCalculator()
        audio1, sr = sample_audio

        # Create different audio
        t = np.linspace(0, 1.0, len(audio1), False)
        audio2 = 0.5 * np.sin(2 * np.pi * 880.0 * t)

        # Test with custom weights
        custom_weights = {
            'spectral_centroid': 2.0,
            'spectral_bandwidth': 0.1,
            'spectral_rolloff': 0.1,
            'mfcc': 0.1,
            'chroma': 0.1,
            'magnitude': 0.1
        }

        distance = calc.compute_frequency_distance(audio1, audio2, weights=custom_weights)

        assert distance > 0
        assert isinstance(distance, float)

    def test_spectral_convergence(self, sample_audio):
        calc = FrequencyDistanceCalculator()
        audio, _ = sample_audio

        features = calc.compute_spectral_features(audio)
        magnitude = features['magnitude_spectrum']

        # Test spectral convergence with itself (should be 0)
        convergence = calc._spectral_convergence(magnitude, magnitude)
        assert abs(convergence) < 1e-6

        # Test with different magnitude spectrum
        magnitude2 = magnitude * 0.5  # Scale by 0.5
        convergence = calc._spectral_convergence(magnitude, magnitude2)
        assert convergence > 0

    def test_calculate_distance_from_files(self, temp_audio_file, sample_audio):
        calc = FrequencyDistanceCalculator()

        # Create second temporary file with different audio
        audio1, sr = sample_audio
        t = np.linspace(0, 1.0, len(audio1), False)
        audio2 = 0.5 * np.sin(2 * np.pi * 880.0 * t)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path2 = Path(f.name)

        try:
            sf.write(temp_path2, audio2, sr)

            distance = calc.calculate_distance_from_files(temp_audio_file, temp_path2)

            assert distance > 0
            assert isinstance(distance, float)

        finally:
            if temp_path2.exists():
                temp_path2.unlink()

    def test_analyze_fundamental_frequency(self, sample_audio):
        calc = FrequencyDistanceCalculator()
        audio, _ = sample_audio

        f0_mean, f0_std = calc.analyze_fundamental_frequency(audio)

        assert isinstance(f0_mean, float)
        assert isinstance(f0_std, float)
        assert f0_mean >= 0
        assert f0_std >= 0

        # For a pure sine wave at 440 Hz, f0 should be close to 440
        # (though librosa's pitch detection might not be perfect)
        if f0_mean > 0:  # Only check if pitch was detected
            assert 200 < f0_mean < 800  # Reasonable range around 440 Hz


class TestTargetAudioGenerator:
    def test_create_target_audio_generator_no_shift(self, temp_audio_file):
        # Test with no frequency shift
        target_audio = create_target_audio_generator(temp_audio_file, 0.0)

        assert isinstance(target_audio, np.ndarray)
        assert len(target_audio) > 0

    def test_create_target_audio_generator_with_shift(self, temp_audio_file):
        # Test with frequency shift
        target_audio = create_target_audio_generator(temp_audio_file, 100.0)  # +100 Hz

        assert isinstance(target_audio, np.ndarray)
        assert len(target_audio) > 0

    def test_create_target_audio_generator_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            create_target_audio_generator(Path("nonexistent.wav"), 0.0)


class TestIntegration:
    def test_full_audio_analysis_pipeline(self, sample_audio):
        """Test the complete audio analysis pipeline"""
        calc = FrequencyDistanceCalculator()
        audio1, sr = sample_audio

        # Create a slightly different audio signal
        t = np.linspace(0, 1.0, len(audio1), False)
        audio2 = 0.4 * np.sin(2 * np.pi * 450.0 * t)  # Different amplitude and frequency

        # Compute features for both
        features1 = calc.compute_spectral_features(audio1)
        features2 = calc.compute_spectral_features(audio2)

        # Verify features are different
        centroid_diff = np.mean(np.abs(
            features1['spectral_centroid'] - features2['spectral_centroid']
        ))
        assert centroid_diff > 0

        # Compute distance
        distance = calc.compute_frequency_distance(audio1, audio2)
        assert distance > 0

        # Analyze fundamental frequencies
        f0_1, _ = calc.analyze_fundamental_frequency(audio1)
        f0_2, _ = calc.analyze_fundamental_frequency(audio2)

        if f0_1 > 0 and f0_2 > 0:
            # Frequencies should be different
            assert abs(f0_1 - f0_2) > 5  # At least 5 Hz difference
