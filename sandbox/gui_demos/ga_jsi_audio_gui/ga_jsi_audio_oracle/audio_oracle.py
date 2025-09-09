"""Audio comparison oracle using librosa for frequency-based comparisons."""

import librosa
import numpy as np
from pathlib import Path
from typing import Any, Optional, Tuple
import warnings

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "choix_active_online"))
from choix_active_online_demo.comparison_oracle import ComparisonOracle


class AudioComparisonOracle(ComparisonOracle):
    """Oracle that compares audio files based on their proximity to a target frequency."""

    def __init__(
        self,
        target_frequency: float = 440.0,
        sr: int = 44100,
        noise_level: float = 0.05,
        random_seed: int = 42,
    ):
        """Initialize audio comparison oracle.

        Args:
            target_frequency: Target frequency in Hz to compare against
            sr: Sample rate for audio processing
            noise_level: Amount of noise to add to decisions (0.0 = perfect, 1.0 = random)
            random_seed: Random seed for reproducibility
        """
        self.target_frequency = target_frequency
        self.sr = sr
        self.noise_level = noise_level
        self.rng = np.random.RandomState(random_seed)

        # Cache for loaded audio to avoid repeated I/O
        self._audio_cache = {}

    def compare(self, item_a: Any, item_b: Any) -> bool:
        """Compare two audio items based on proximity to target frequency.

        Args:
            item_a: Path to first audio file or audio data
            item_b: Path to second audio file or audio data

        Returns:
            True if item_a is closer to target frequency than item_b
        """
        # Extract fundamental frequencies
        freq_a = self._get_fundamental_frequency(item_a)
        freq_b = self._get_fundamental_frequency(item_b)

        # Calculate distances from target
        dist_a = abs(freq_a - self.target_frequency)
        dist_b = abs(freq_b - self.target_frequency)

        # Determine which is closer (lower distance is better)
        prob_a_wins = self._calculate_win_probability(dist_a, dist_b)

        # Add noise
        noisy_prob = (1 - self.noise_level) * prob_a_wins + self.noise_level * 0.5

        return self.rng.random() < noisy_prob

    def _get_fundamental_frequency(self, item: Any) -> float:
        """Extract fundamental frequency from audio item.

        Args:
            item: Audio file path or audio data

        Returns:
            Estimated fundamental frequency in Hz
        """
        if isinstance(item, (str, Path)):
            audio_path = Path(item)

            # Use cache to avoid repeated loading
            if audio_path in self._audio_cache:
                audio = self._audio_cache[audio_path]
            else:
                audio = self._load_audio(audio_path)
                self._audio_cache[audio_path] = audio
        else:
            # Assume it's already audio data
            audio = item

        return self._estimate_fundamental_frequency(audio)

    def _load_audio(self, audio_path: Path) -> np.ndarray:
        """Load audio file using librosa.

        Args:
            audio_path: Path to audio file

        Returns:
            Audio time series
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        audio, _ = librosa.load(str(audio_path), sr=self.sr, mono=True)
        return audio

    def _estimate_fundamental_frequency(self, audio: np.ndarray) -> float:
        """Estimate fundamental frequency using librosa.

        Args:
            audio: Audio time series

        Returns:
            Estimated fundamental frequency in Hz
        """
        if len(audio) == 0:
            return 0.0

        # Use piptrack for pitch estimation
        pitches, magnitudes = librosa.piptrack(y=audio, sr=self.sr, threshold=0.1)

        # Extract pitch values weighted by magnitude
        f0_values = []
        for t in range(pitches.shape[1]):
            # Get indices of non-zero pitches
            pitch_indices = np.where(pitches[:, t] > 0)[0]
            if len(pitch_indices) > 0:
                # Weight by magnitude and take strongest
                mag_weights = magnitudes[pitch_indices, t]
                if np.sum(mag_weights) > 0:
                    weighted_pitch = np.average(
                        pitches[pitch_indices, t], weights=mag_weights
                    )
                    f0_values.append(weighted_pitch)

        if not f0_values:
            # Fallback: use spectral centroid as frequency proxy
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=self.sr)[
                0
            ]
            return np.mean(spectral_centroid) if len(spectral_centroid) > 0 else 440.0

        return np.median(f0_values)  # Use median for robustness

    def _calculate_win_probability(self, dist_a: float, dist_b: float) -> float:
        """Calculate probability that item A wins based on distances from target.

        Args:
            dist_a: Distance of item A from target frequency
            dist_b: Distance of item B from target frequency

        Returns:
            Probability that item A wins (is closer to target)
        """
        if dist_a == dist_b:
            return 0.5

        # Use exponential decay: closer distances have higher strength
        # Add small epsilon to avoid division by zero
        epsilon = 1e-6
        strength_a = 1.0 / (dist_a + epsilon)
        strength_b = 1.0 / (dist_b + epsilon)

        # Bradley-Terry probability
        return strength_a / (strength_a + strength_b)

    def set_target_frequency(self, frequency: float) -> None:
        """Update the target frequency for comparisons.

        Args:
            frequency: New target frequency in Hz
        """
        self.target_frequency = frequency
        # Clear cache since target changed
        self._audio_cache.clear()

    def clear_cache(self) -> None:
        """Clear the audio cache to free memory."""
        self._audio_cache.clear()

    def get_cache_info(self) -> dict:
        """Get information about the current audio cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_files": len(self._audio_cache),
            "cache_keys": list(self._audio_cache.keys()),
        }


class FrequencyTargetOracle(AudioComparisonOracle):
    """Specialized oracle that compares audio files against a target audio file."""

    def __init__(
        self,
        target_audio_path: Path,
        sr: int = 44100,
        noise_level: float = 0.05,
        random_seed: int = 42,
    ):
        """Initialize with target audio file.

        Args:
            target_audio_path: Path to target audio file
            sr: Sample rate for audio processing
            noise_level: Amount of noise to add to decisions
            random_seed: Random seed for reproducibility
        """
        # Extract target frequency from audio file
        target_freq = self._extract_target_frequency(target_audio_path, sr)

        super().__init__(
            target_frequency=target_freq,
            sr=sr,
            noise_level=noise_level,
            random_seed=random_seed,
        )

        self.target_audio_path = target_audio_path

    def _extract_target_frequency(self, audio_path: Path, sr: int) -> float:
        """Extract fundamental frequency from target audio file.

        Args:
            audio_path: Path to target audio file
            sr: Sample rate

        Returns:
            Fundamental frequency of target audio
        """
        if not audio_path.exists():
            warnings.warn(f"Target audio file not found: {audio_path}, using 440 Hz")
            return 440.0

        try:
            audio, _ = librosa.load(str(audio_path), sr=sr, mono=True)
            return self._estimate_fundamental_frequency(audio)
        except Exception as e:
            warnings.warn(f"Error loading target audio: {e}, using 440 Hz")
            return 440.0
