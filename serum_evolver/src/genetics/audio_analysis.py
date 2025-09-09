"""
Audio analysis tools for frequency domain comparisons using librosa.
"""

import librosa
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import soundfile as sf


class FrequencyDistanceCalculator:
    """Calculate frequency-domain distance between audio files"""

    def __init__(self, sr: int = 44100, n_fft: int = 2048, hop_length: int = 512):
        """Initialize with audio processing parameters"""
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length

    def load_audio(self, file_path: Path) -> np.ndarray:
        """Load audio file and return time-domain signal"""
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Load audio with librosa
        y, sr = librosa.load(str(file_path), sr=self.sr, mono=True)
        return y

    def compute_spectral_features(self, audio: np.ndarray) -> dict:
        """Compute spectral features from audio signal"""
        # Compute STFT
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        magnitude = np.abs(stft)

        # Compute spectral features
        spectral_centroid = librosa.feature.spectral_centroid(
            S=magnitude, sr=self.sr, hop_length=self.hop_length
        )[0]

        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            S=magnitude, sr=self.sr, hop_length=self.hop_length
        )[0]

        spectral_rolloff = librosa.feature.spectral_rolloff(
            S=magnitude, sr=self.sr, hop_length=self.hop_length
        )[0]

        # Compute MFCCs
        mfccs = librosa.feature.mfcc(
            y=audio, sr=self.sr, n_mfcc=13, hop_length=self.hop_length
        )

        # Compute chroma features
        chroma = librosa.feature.chroma_stft(
            S=magnitude, sr=self.sr, hop_length=self.hop_length
        )

        return {
            'spectral_centroid': spectral_centroid,
            'spectral_bandwidth': spectral_bandwidth,
            'spectral_rolloff': spectral_rolloff,
            'mfccs': mfccs,
            'chroma': chroma,
            'magnitude_spectrum': magnitude
        }

    def compute_frequency_distance(
        self,
        audio1: np.ndarray,
        audio2: np.ndarray,
        weights: Optional[dict] = None
    ) -> float:
        """Compute frequency-domain distance between two audio signals"""
        if weights is None:
            weights = {
                'spectral_centroid': 1.0,
                'spectral_bandwidth': 0.5,
                'spectral_rolloff': 0.5,
                'mfcc': 1.0,
                'chroma': 0.8,
                'magnitude': 0.3
            }

        features1 = self.compute_spectral_features(audio1)
        features2 = self.compute_spectral_features(audio2)

        total_distance = 0.0

        # Spectral centroid distance
        centroid_dist = np.mean(np.abs(
            features1['spectral_centroid'] - features2['spectral_centroid']
        ))
        total_distance += weights['spectral_centroid'] * centroid_dist

        # Spectral bandwidth distance
        bandwidth_dist = np.mean(np.abs(
            features1['spectral_bandwidth'] - features2['spectral_bandwidth']
        ))
        total_distance += weights['spectral_bandwidth'] * bandwidth_dist

        # Spectral rolloff distance
        rolloff_dist = np.mean(np.abs(
            features1['spectral_rolloff'] - features2['spectral_rolloff']
        ))
        total_distance += weights['spectral_rolloff'] * rolloff_dist

        # MFCC distance
        mfcc_dist = np.mean(np.sqrt(np.sum(
            (features1['mfccs'] - features2['mfccs']) ** 2, axis=0
        )))
        total_distance += weights['mfcc'] * mfcc_dist

        # Chroma distance
        chroma_dist = np.mean(np.sqrt(np.sum(
            (features1['chroma'] - features2['chroma']) ** 2, axis=0
        )))
        total_distance += weights['chroma'] * chroma_dist

        # Magnitude spectrum distance (using spectral convergence)
        mag_dist = self._spectral_convergence(
            features1['magnitude_spectrum'],
            features2['magnitude_spectrum']
        )
        total_distance += weights['magnitude'] * mag_dist

        return total_distance

    def _spectral_convergence(self, X: np.ndarray, Y: np.ndarray) -> float:
        """Compute spectral convergence between two magnitude spectrograms"""
        # Ensure same shape by taking minimum dimensions
        min_frames = min(X.shape[1], Y.shape[1])
        X = X[:, :min_frames]
        Y = Y[:, :min_frames]

        numerator = np.sum((X - Y) ** 2)
        denominator = np.sum(X ** 2)

        if denominator == 0:
            return 0.0

        return np.sqrt(numerator / denominator)

    def calculate_distance_from_files(
        self,
        file1: Path,
        file2: Path,
        weights: Optional[dict] = None
    ) -> float:
        """Calculate frequency distance between two audio files"""
        audio1 = self.load_audio(file1)
        audio2 = self.load_audio(file2)

        return self.compute_frequency_distance(audio1, audio2, weights)

    def analyze_fundamental_frequency(self, audio: np.ndarray) -> Tuple[float, float]:
        """Analyze fundamental frequency characteristics"""
        # Use librosa to estimate pitch
        pitches, magnitudes = librosa.piptrack(
            y=audio, sr=self.sr, hop_length=self.hop_length
        )

        # Extract fundamental frequency
        f0_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                f0_values.append(pitch)

        if not f0_values:
            return 0.0, 0.0

        f0_mean = np.mean(f0_values)
        f0_std = np.std(f0_values)

        return f0_mean, f0_std


def create_target_audio_generator(
    base_audio_path: Path,
    target_frequency_shift: float = 0.0
) -> np.ndarray:
    """Generate target audio with specified frequency characteristics"""
    calculator = FrequencyDistanceCalculator()
    base_audio = calculator.load_audio(base_audio_path)

    # Simple pitch shifting using librosa
    if target_frequency_shift != 0.0:
        # Convert frequency shift to semitones (approximate)
        semitones = 12 * np.log2(1 + target_frequency_shift / 440.0)
        shifted_audio = librosa.effects.pitch_shift(
            base_audio, sr=calculator.sr, n_steps=semitones
        )
        return shifted_audio

    return base_audio
