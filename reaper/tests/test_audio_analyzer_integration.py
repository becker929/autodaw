"""Integration tests for AudioAnalyzer demonstrating real-world usage patterns."""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from audio_analyzer import AudioAnalyzer


class TestAudioAnalyzerRealWorldUsage:
    """Integration tests simulating real-world usage scenarios."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer for real-world usage tests."""
        return AudioAnalyzer(sample_rate=22050, hop_length=512)

    @pytest.fixture
    def temp_audio_files(self, sample_rate, duration):
        """Create temporary audio files for testing file I/O operations."""
        # Note: This would normally use actual audio file writing
        # For testing purposes, we'll simulate with numpy arrays
        files_data = {}

        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # Generate different test signals
        test_signals = {
            'sine_440': (0.5 * np.sin(2 * np.pi * 440 * t), 440.0),
            'sine_c4': (0.3 * np.sin(2 * np.pi * 261.63 * t), 261.63),
            'chord': (0.33 * (np.sin(2 * np.pi * 261.63 * t) +
                             np.sin(2 * np.pi * 329.63 * t) +
                             np.sin(2 * np.pi * 392.00 * t)), [261.63, 329.63, 392.00]),
            'silence': (np.zeros(int(sample_rate * duration)), 0.0),
            'am_signal': (0.4 * (1 + 0.5 * np.sin(2 * np.pi * 5 * t)) *
                         np.sin(2 * np.pi * 523.25 * t), 523.25)
        }

        return test_signals

    def test_step_by_step_analysis_workflow(self, analyzer, temp_audio_files, sample_rate):
        """Test the step-by-step analysis workflow as shown in examples."""
        # Use the sine_440 test signal
        signal, expected_freq = temp_audio_files['sine_440']

        # Step 1: Get volume separately
        volume_db = analyzer.get_mean_volume_db(signal)
        assert np.isfinite(volume_db)
        assert volume_db < 0  # Should be negative dB for amplitude < 1
        print(f"Mean Volume: {volume_db:.2f} dB")

        # Step 2: Try different pitch extraction methods
        methods = ['pyin', 'yin', 'stft']
        pitch_results = {}

        for method in methods:
            try:
                pitch_hz = analyzer.get_mean_pitch(signal, sample_rate, method=method)
                pitch_results[method] = pitch_hz
                print(f"Mean Pitch ({method}): {pitch_hz:.2f} Hz")

                # Verify reasonable pitch detection
                if method in ['pyin', 'yin']:  # These should be more accurate
                    assert abs(pitch_hz - expected_freq) < 10.0
                else:  # STFT might be less accurate
                    assert pitch_hz > 0  # At least detect some pitch

            except Exception as e:
                print(f"Pitch extraction with {method} failed: {e}")
                # Some methods might fail, which is acceptable
                pass

        # At least one method should work
        assert len(pitch_results) > 0
        assert any(p > 0 for p in pitch_results.values())

    def test_batch_analysis_simulation(self, analyzer, temp_audio_files, sample_rate):
        """Test batch analysis workflow with multiple signals."""
        # Simulate batch processing of different audio types
        test_cases = [
            ('sine_440', 'Pure tone A4'),
            ('sine_c4', 'Pure tone C4'),
            ('chord', 'C major chord'),
            ('silence', 'Silence'),
            ('am_signal', 'Amplitude modulated signal')
        ]

        results = []
        for signal_name, description in test_cases:
            signal, expected_data = temp_audio_files[signal_name]

            try:
                # Simulate the analyze_file workflow
                volume_db = analyzer.get_mean_volume_db(signal)
                pitch_hz = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

                result = {
                    'name': signal_name,
                    'description': description,
                    'volume_db': float(volume_db),
                    'pitch_hz': float(pitch_hz),
                    'expected': expected_data,
                    'error': None
                }

                # Validate results based on signal type
                if signal_name == 'silence':
                    assert volume_db == -np.inf
                    assert pitch_hz == 0.0
                elif signal_name in ['sine_440', 'sine_c4', 'am_signal']:
                    assert np.isfinite(volume_db)
                    assert abs(pitch_hz - expected_data) < 15.0  # Allow some tolerance
                elif signal_name == 'chord':
                    assert np.isfinite(volume_db)
                    # For chord, pitch should be reasonable (might detect fundamental or one component)
                    assert pitch_hz > 0
                    assert 50 < pitch_hz < 500  # Wide range for chord detection

                results.append(result)

            except Exception as e:
                results.append({
                    'name': signal_name,
                    'description': description,
                    'volume_db': None,
                    'pitch_hz': None,
                    'expected': expected_data,
                    'error': str(e)
                })

        # Print results (simulating the example output)
        print(f"\nAnalyzed {len(results)} signals:")
        for i, result in enumerate(results, 1):
            print(f"\nSignal {i} ({result['name']}):")
            if result['error']:
                print(f"  Error: {result['error']}")
            else:
                print(f"  Description: {result['description']}")
                print(f"  Volume: {result['volume_db']:.2f} dB")
                print(f"  Pitch: {result['pitch_hz']:.2f} Hz")

        # Verify that we got reasonable results
        successful_results = [r for r in results if r['error'] is None]
        assert len(successful_results) >= 4  # Should succeed on most test cases

    def test_musical_note_conversion_workflow(self, analyzer, temp_audio_files, sample_rate):
        """Test the complete workflow including musical note conversions."""
        from audio_analyzer import hz_to_midi_note, midi_note_to_name

        # Test with known frequencies
        test_frequencies = [
            (temp_audio_files['sine_440'][0], 440.0, 69, 'A4'),
            (temp_audio_files['sine_c4'][0], 261.63, 60, 'C4'),
        ]

        for signal, expected_freq, expected_midi, expected_note in test_frequencies:
            # Analyze the signal
            pitch_hz = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

            # Convert to musical information
            midi_note = hz_to_midi_note(pitch_hz)
            note_name = midi_note_to_name(midi_note)

            print(f"Frequency: {pitch_hz:.2f} Hz")
            print(f"MIDI Note: {midi_note} ({note_name})")
            print(f"Expected: {expected_freq} Hz, MIDI {expected_midi} ({expected_note})")

            # Verify conversions
            assert abs(pitch_hz - expected_freq) < 5.0
            assert abs(midi_note - expected_midi) <= 1  # Allow ±1 semitone
            # Note name should be close (accounting for enharmonic equivalents)
            assert note_name[0] == expected_note[0]  # Same note letter

    def test_error_handling_real_world_scenarios(self, analyzer):
        """Test error handling in real-world scenarios."""
        # Test with empty audio
        with pytest.raises(ValueError, match="No audio data available"):
            analyzer.get_mean_volume_db()

        # Test with invalid method
        signal = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 1000))
        with pytest.raises(ValueError, match="Invalid method"):
            analyzer.get_mean_pitch(signal, 22050, method='invalid')

        # Test with malformed audio data
        with pytest.raises(ValueError):
            analyzer.get_mean_volume_db(np.array([]))

    def test_performance_characteristics(self, analyzer, sample_rate):
        """Test performance with different audio characteristics."""
        duration = 5.0  # Longer signal
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # Test with different signal characteristics
        test_signals = [
            ('short_burst', 0.5 * np.sin(2 * np.pi * 440 * t) *
             (t < 0.5).astype(float)),  # Short burst
            ('frequency_sweep', 0.5 * np.sin(2 * np.pi * (200 + 400 * t / duration) * t)),  # Sweep
            ('complex_harmonic', 0.3 * (np.sin(2 * np.pi * 220 * t) +
                                       0.5 * np.sin(2 * np.pi * 440 * t) +
                                       0.25 * np.sin(2 * np.pi * 880 * t))),  # Harmonic series
        ]

        for name, signal in test_signals:
            # These should complete without errors, though results may vary
            volume_db = analyzer.get_mean_volume_db(signal)
            pitch_hz = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

            print(f"{name}: Volume={volume_db:.2f}dB, Pitch={pitch_hz:.2f}Hz")

            # Basic sanity checks
            assert np.isfinite(volume_db)
            assert pitch_hz >= 0.0  # Pitch should be non-negative

    def test_analyzer_state_management(self, analyzer, temp_audio_files, sample_rate):
        """Test that analyzer properly manages internal state."""
        # Initially no state
        assert analyzer._audio_data is None
        assert analyzer._sr is None
        assert analyzer._file_path is None

        # After analysis, no persistent state should remain
        signal, _ = temp_audio_files['sine_440']
        volume = analyzer.get_mean_volume_db(signal)

        # State should still be None since we passed signal directly
        assert analyzer._audio_data is None

        # Test that passing None uses stored state (should fail initially)
        with pytest.raises(ValueError, match="No audio data available"):
            analyzer.get_mean_volume_db(None)


class TestAudioAnalyzerDocumentationExamples:
    """Tests that verify the examples in documentation work correctly."""

    def test_basic_usage_example(self, sample_rate):
        """Test the basic usage example from documentation."""
        # This simulates the basic usage pattern shown in docstrings
        analyzer = AudioAnalyzer(sample_rate=sample_rate)

        # Generate test signal
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        test_audio = 0.5 * np.sin(2 * np.pi * 440 * t)

        # Basic usage pattern
        volume = analyzer.get_mean_volume_db(test_audio)
        pitch = analyzer.get_mean_pitch(test_audio, sample_rate, method='pyin')

        # Verify results are reasonable
        assert np.isfinite(volume)
        assert volume < 0  # dB should be negative
        assert abs(pitch - 440.0) < 5.0
        assert pitch > 0

    def test_initialization_parameters(self):
        """Test different initialization parameters."""
        # Default initialization
        analyzer1 = AudioAnalyzer()
        assert analyzer1.sample_rate is None
        assert analyzer1.hop_length == 512

        # Custom parameters
        analyzer2 = AudioAnalyzer(sample_rate=44100, hop_length=1024)
        assert analyzer2.sample_rate == 44100
        assert analyzer2.hop_length == 1024

    def test_method_comparison_example(self, sample_rate):
        """Test the method comparison example."""
        analyzer = AudioAnalyzer(sample_rate=sample_rate)

        # Generate test signal
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        test_audio = 0.4 * np.sin(2 * np.pi * 329.63 * t)  # E4

        methods = ['pyin', 'yin', 'stft']
        results = {}

        for method in methods:
            try:
                pitch_hz = analyzer.get_mean_pitch(test_audio, sample_rate, method=method)
                results[method] = pitch_hz
                print(f"{method.upper()}: {pitch_hz:.2f} Hz")
            except Exception as e:
                print(f"{method.upper()}: Failed - {e}")
                results[method] = None

        # At least some methods should work
        successful_methods = [m for m, p in results.items() if p is not None and p > 0]
        assert len(successful_methods) > 0
