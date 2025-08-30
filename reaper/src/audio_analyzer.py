"""
Audio analysis utilities using librosa for extracting volume and pitch information.
"""

import librosa
import numpy as np
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import warnings
from config import get_logger

# Set up module logger
logger = get_logger(__name__)


class AudioAnalyzer:
    """
    A librosa-powered class for analyzing audio files to extract mean volume (dB) and mean pitch.

    This class provides methods to:
    - Load audio files in various formats
    - Calculate mean volume in decibels using RMS energy
    - Extract mean pitch using librosa's pitch tracking algorithms
    - Handle common audio analysis edge cases
    """

    def __init__(self, sample_rate: Optional[int] = None, hop_length: int = 512):
        """
        Initialize the AudioAnalyzer.

        Args:
            sample_rate: Target sample rate for audio loading. If None, uses original sample rate.
            hop_length: Number of samples between successive frames for pitch analysis.
        """
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self._audio_data: Optional[np.ndarray] = None
        self._sr: Optional[int] = None
        self._file_path: Optional[Path] = None

        logger.info(f"AudioAnalyzer initialized: sample_rate={sample_rate}, hop_length={hop_length}")

    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load an audio file using librosa.

        Args:
            file_path: Path to the audio file

        Returns:
            Tuple of (audio_data, sample_rate)

        Raises:
            FileNotFoundError: If the audio file doesn't exist
            ValueError: If the audio file cannot be loaded
        """
        logger.debug(f"Loading audio file: {file_path}")
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            # Load audio file
            logger.debug(f"Loading with librosa: target_sr={self.sample_rate}, mono=True")
            audio_data, sr = librosa.load(
                str(path),
                sr=self.sample_rate,
                mono=True  # Convert to mono for consistent analysis
            )

            logger.debug(f"Audio loaded: duration={len(audio_data)/sr:.2f}s, sample_rate={sr}, samples={len(audio_data)}")

            if len(audio_data) == 0:
                logger.error(f"Audio file appears to be empty: {file_path}")
                raise ValueError(f"Audio file appears to be empty: {file_path}")

            # Store for reuse
            self._audio_data = audio_data
            self._sr = sr
            self._file_path = path

            logger.info(f"Successfully loaded audio: {path.name}, {len(audio_data)} samples at {sr}Hz")
            return audio_data, sr

        except Exception as e:
            logger.exception(f"Failed to load audio file {file_path}: {e}")
            raise ValueError(f"Failed to load audio file {file_path}: {str(e)}")

    def get_mean_volume_db(self, audio_data: Optional[np.ndarray] = None) -> float:
        """
        Calculate the mean volume in decibels using RMS energy.

        Args:
            audio_data: Audio data array. If None, uses last loaded audio.

        Returns:
            Mean volume in dB

        Raises:
            ValueError: If no audio data is available
        """
        if audio_data is None:
            if self._audio_data is None:
                raise ValueError("No audio data available. Load an audio file first.")
            audio_data = self._audio_data

        # Check for empty audio data
        if len(audio_data) == 0:
            raise ValueError("Audio data is empty")

        # Calculate RMS energy
        rms_energy = librosa.feature.rms(y=audio_data, hop_length=self.hop_length)[0]

        # Check for complete silence
        if np.all(rms_energy == 0):
            return -np.inf

        # Convert to dB, handling silence
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            # Use a fixed reference to avoid issues with silence
            rms_db = librosa.amplitude_to_db(rms_energy, ref=1.0)

        # Calculate mean, filtering out -inf values (silence)
        valid_db = rms_db[np.isfinite(rms_db)]
        if len(valid_db) == 0:
            return -np.inf  # Complete silence

        return float(np.mean(valid_db))

    def get_mean_pitch(self, audio_data: Optional[np.ndarray] = None,
                      sr: Optional[int] = None, method: str = 'pyin') -> float:
        """
        Extract mean pitch from audio using librosa pitch tracking.

        Args:
            audio_data: Audio data array. If None, uses last loaded audio.
            sr: Sample rate. If None, uses sample rate from last loaded audio.
            method: Pitch extraction method ('pyin', 'yin', or 'stft')

        Returns:
            Mean pitch in Hz (returns 0.0 if no pitch detected)

        Raises:
            ValueError: If no audio data is available or invalid method specified
        """
        if audio_data is None:
            if self._audio_data is None:
                raise ValueError("No audio data available. Load an audio file first.")
            audio_data = self._audio_data

        if sr is None:
            if self._sr is None:
                raise ValueError("No sample rate available. Load an audio file first.")
            sr = self._sr

        # Check for empty audio data
        if len(audio_data) == 0:
            raise ValueError("Audio data is empty")

        # Check for valid sample rate
        if sr <= 0:
            raise ValueError("Sample rate must be positive")

        valid_methods = ['pyin', 'yin', 'stft']
        if method not in valid_methods:
            raise ValueError(f"Invalid method '{method}'. Must be one of: {valid_methods}")

        try:
            if method == 'pyin':
                # PYIN algorithm - good for monophonic sources
                pitches, voiced_flag, voiced_probs = librosa.pyin(
                    audio_data,
                    fmin=librosa.note_to_hz('C2'),  # ~65 Hz
                    fmax=librosa.note_to_hz('C7'),  # ~2093 Hz
                    sr=sr,
                    hop_length=self.hop_length
                )
                # Filter out unvoiced segments
                voiced_pitches = pitches[voiced_flag]

            elif method == 'yin':
                # YIN algorithm
                pitches = librosa.yin(
                    audio_data,
                    fmin=librosa.note_to_hz('C2'),
                    fmax=librosa.note_to_hz('C7'),
                    sr=sr,
                    hop_length=self.hop_length
                )
                # Filter out NaN values
                voiced_pitches = pitches[~np.isnan(pitches)]

            else:  # stft
                # STFT-based pitch tracking
                pitches, magnitudes = librosa.piptrack(
                    y=audio_data,
                    sr=sr,
                    hop_length=self.hop_length,
                    fmin=librosa.note_to_hz('C2'),
                    fmax=librosa.note_to_hz('C7')
                )

                # Extract most prominent pitch at each time frame
                pitch_values = []
                for t in range(pitches.shape[1]):
                    index = magnitudes[:, t].argmax()
                    pitch = pitches[index, t]
                    if pitch > 0:
                        pitch_values.append(pitch)

                voiced_pitches = np.array(pitch_values)

            # Calculate mean pitch from voiced segments
            if len(voiced_pitches) == 0:
                return 0.0  # No pitch detected

            # Remove outliers (beyond 3 standard deviations)
            mean_pitch = np.mean(voiced_pitches)
            std_pitch = np.std(voiced_pitches)
            if std_pitch > 0:
                mask = np.abs(voiced_pitches - mean_pitch) <= 3 * std_pitch
                voiced_pitches = voiced_pitches[mask]

            return float(np.mean(voiced_pitches)) if len(voiced_pitches) > 0 else 0.0

        except Exception as e:
            raise ValueError(f"Pitch extraction failed: {str(e)}")

    def analyze_file(self, file_path: str, pitch_method: str = 'pyin') -> Dict[str, Any]:
        """
        Perform complete analysis of an audio file.

        Args:
            file_path: Path to the audio file
            pitch_method: Method for pitch extraction ('pyin', 'yin', or 'stft')

        Returns:
            Dictionary containing analysis results:
            - file_path: Path to analyzed file
            - duration: Duration in seconds
            - sample_rate: Sample rate
            - mean_volume_db: Mean volume in dB
            - mean_pitch_hz: Mean pitch in Hz
            - mean_pitch_note: Closest musical note (if pitch detected)
        """
        logger.info(f"Analyzing audio file: {file_path} with method: {pitch_method}")

        # Load the audio file
        audio_data, sr = self.load_audio(file_path)

        # Calculate duration
        duration = len(audio_data) / sr
        logger.debug(f"Audio duration: {duration:.2f} seconds")

        # Analyze volume
        logger.debug("Analyzing volume")
        mean_volume = self.get_mean_volume_db(audio_data)
        logger.debug(f"Mean volume: {mean_volume:.2f} dB")

        # Analyze pitch
        logger.debug(f"Analyzing pitch with method: {pitch_method}")
        mean_pitch = self.get_mean_pitch(audio_data, sr, pitch_method)
        logger.debug(f"Mean pitch: {mean_pitch:.2f} Hz")

        # Convert pitch to musical note if detected
        mean_pitch_note = None
        if mean_pitch > 0:
            try:
                mean_pitch_note = librosa.hz_to_note(mean_pitch)
                logger.debug(f"Pitch as note: {mean_pitch_note}")
            except:
                mean_pitch_note = "Unknown"
                logger.warning("Could not convert pitch to note")

        result = {
            'file_path': str(self._file_path),
            'duration': float(duration),
            'sample_rate': int(sr),
            'mean_volume_db': float(mean_volume),
            'mean_pitch_hz': float(mean_pitch),
            'mean_pitch_note': mean_pitch_note
        }

        logger.info(f"Analysis complete: volume={mean_volume:.1f}dB, pitch={mean_pitch:.1f}Hz ({mean_pitch_note})")
        return result

    def batch_analyze(self, file_paths: list, pitch_method: str = 'pyin') -> list:
        """
        Analyze multiple audio files.

        Args:
            file_paths: List of paths to audio files
            pitch_method: Method for pitch extraction

        Returns:
            List of analysis results dictionaries
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.analyze_file(file_path, pitch_method)
                results.append(result)
            except Exception as e:
                # Add error information to results
                results.append({
                    'file_path': str(file_path),
                    'error': str(e),
                    'duration': None,
                    'sample_rate': None,
                    'mean_volume_db': None,
                    'mean_pitch_hz': None,
                    'mean_pitch_note': None
                })
        return results


def hz_to_midi_note(frequency: float) -> int:
    """
    Convert frequency in Hz to MIDI note number.

    Args:
        frequency: Frequency in Hz

    Returns:
        MIDI note number (0-127)
    """
    if frequency <= 0:
        return 0

    # A4 = 440 Hz = MIDI note 69
    midi_note = 69 + 12 * np.log2(frequency / 440.0)
    return int(round(midi_note))


def midi_note_to_name(midi_note: int) -> str:
    """
    Convert MIDI note number to note name.

    Args:
        midi_note: MIDI note number (0-127)

    Returns:
        Note name (e.g., 'C4', 'F#5')
    """
    if midi_note < 0 or midi_note > 127:
        return "Unknown"

    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (midi_note // 12) - 1
    note = note_names[midi_note % 12]
    return f"{note}{octave}"
