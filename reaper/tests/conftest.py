"""Pytest configuration and shared fixtures for audio analysis tests."""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_rate():
    """Standard sample rate for test audio."""
    return 22050


@pytest.fixture
def duration():
    """Standard duration for test audio in seconds."""
    return 2.0


@pytest.fixture
def time_vector(sample_rate, duration):
    """Generate time vector for test signals."""
    return np.linspace(0, duration, int(sample_rate * duration), False)


@pytest.fixture
def sine_wave_440hz(time_vector):
    """Generate a 440Hz sine wave (A4) for testing."""
    frequency = 440.0
    amplitude = 0.5
    return amplitude * np.sin(2 * np.pi * frequency * time_vector), frequency


@pytest.fixture
def sine_wave_c4(time_vector):
    """Generate a C4 sine wave (261.63Hz) for testing."""
    frequency = 261.63
    amplitude = 0.3
    return amplitude * np.sin(2 * np.pi * frequency * time_vector), frequency


@pytest.fixture
def silence(sample_rate, duration):
    """Generate silence for testing."""
    return np.zeros(int(sample_rate * duration))


@pytest.fixture
def amplitude_modulated_signal(time_vector):
    """Generate an amplitude modulated signal for testing."""
    carrier_freq = 523.25  # C5
    mod_freq = 5.0  # 5 Hz modulation
    amplitude = 0.4 * (1 + 0.5 * np.sin(2 * np.pi * mod_freq * time_vector))
    signal = amplitude * np.sin(2 * np.pi * carrier_freq * time_vector)
    return signal, carrier_freq


@pytest.fixture
def chord_signal(time_vector):
    """Generate a C major triad chord for testing polyphonic content."""
    frequencies = [261.63, 329.63, 392.00]  # C4, E4, G4
    amplitude = 0.33
    signal = sum(amplitude * np.sin(2 * np.pi * f * time_vector) for f in frequencies)
    return signal, frequencies


@pytest.fixture
def noisy_signal(sine_wave_440hz, sample_rate):
    """Generate a noisy signal for robustness testing."""
    signal, frequency = sine_wave_440hz
    # Add white noise at -20dB relative to signal
    noise_amplitude = 0.1 * np.max(np.abs(signal))
    noise = noise_amplitude * np.random.randn(len(signal))
    return signal + noise, frequency
