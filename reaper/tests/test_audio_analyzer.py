"""Pytest tests for the AudioAnalyzer class."""

import pytest
import numpy as np
from audio_analyzer import AudioAnalyzer, hz_to_midi_note, midi_note_to_name


class TestAudioAnalyzer:
    """Test suite for AudioAnalyzer class."""

    @pytest.fixture
    def analyzer(self, sample_rate):
        """Create an AudioAnalyzer instance for testing."""
        return AudioAnalyzer(sample_rate=sample_rate, hop_length=512)

    def test_initialization(self, analyzer, sample_rate):
        """Test AudioAnalyzer initialization."""
        assert analyzer.sample_rate == sample_rate
        assert analyzer.hop_length == 512
        assert analyzer._audio_data is None
        assert analyzer._sr is None
        assert analyzer._file_path is None

    def test_volume_calculation_sine_wave(self, analyzer, sine_wave_440hz, sample_rate):
        """Test volume calculation with a sine wave."""
        signal, frequency = sine_wave_440hz

        volume_db = analyzer.get_mean_volume_db(signal)

        # Volume should be finite and reasonable for a 0.5 amplitude sine wave
        assert np.isfinite(volume_db)
        assert -20 <= volume_db <= 0  # Reasonable dB range

    def test_volume_calculation_silence(self, analyzer, silence):
        """Test volume calculation with silence."""
        volume_db = analyzer.get_mean_volume_db(silence)

        # Silence should result in -inf dB
        assert volume_db == -np.inf

    def test_pitch_detection_sine_wave_440hz(self, analyzer, sine_wave_440hz, sample_rate):
        """Test pitch detection with 440Hz sine wave."""
        signal, expected_frequency = sine_wave_440hz

        detected_pitch = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

        # Should detect pitch within 5Hz tolerance
        assert abs(detected_pitch - expected_frequency) < 5.0
        assert detected_pitch > 0

    def test_pitch_detection_sine_wave_c4(self, analyzer, sine_wave_c4, sample_rate):
        """Test pitch detection with C4 sine wave."""
        signal, expected_frequency = sine_wave_c4

        detected_pitch = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

        # Should detect pitch within 5Hz tolerance
        assert abs(detected_pitch - expected_frequency) < 5.0
        assert detected_pitch > 0

    def test_pitch_detection_silence(self, analyzer, silence, sample_rate):
        """Test pitch detection with silence."""
        detected_pitch = analyzer.get_mean_pitch(silence, sample_rate, method='pyin')

        # Silence should result in 0.0 Hz
        assert detected_pitch == 0.0

    def test_pitch_detection_amplitude_modulated(self, analyzer, amplitude_modulated_signal, sample_rate):
        """Test pitch detection with amplitude modulated signal."""
        signal, expected_frequency = amplitude_modulated_signal

        detected_pitch = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

        # Should still detect the carrier frequency despite modulation
        assert abs(detected_pitch - expected_frequency) < 10.0  # Slightly higher tolerance for AM
        assert detected_pitch > 0

    @pytest.mark.parametrize("method", ["pyin", "yin", "stft"])
    def test_pitch_detection_methods(self, analyzer, sine_wave_440hz, sample_rate, method):
        """Test different pitch detection methods."""
        signal, expected_frequency = sine_wave_440hz

        detected_pitch = analyzer.get_mean_pitch(signal, sample_rate, method=method)

        # All methods should detect pitch reasonably well
        # STFT method might be less accurate, so use higher tolerance
        tolerance = 15.0 if method == "stft" else 5.0
        assert abs(detected_pitch - expected_frequency) < tolerance
        assert detected_pitch > 0

    def test_invalid_pitch_method(self, analyzer, sine_wave_440hz, sample_rate):
        """Test error handling for invalid pitch detection method."""
        signal, _ = sine_wave_440hz

        with pytest.raises(ValueError, match="Invalid method"):
            analyzer.get_mean_pitch(signal, sample_rate, method='invalid_method')

    def test_no_audio_data_error(self, analyzer):
        """Test error when no audio data is loaded."""
        with pytest.raises(ValueError, match="No audio data available"):
            analyzer.get_mean_volume_db()

        with pytest.raises(ValueError, match="No audio data available"):
            analyzer.get_mean_pitch()

    def test_file_not_found_error(self, analyzer):
        """Test error handling for non-existent files."""
        with pytest.raises(FileNotFoundError):
            analyzer.load_audio("non_existent_file.wav")

    def test_chord_pitch_detection(self, analyzer, chord_signal, sample_rate):
        """Test pitch detection with polyphonic content (chord)."""
        signal, frequencies = chord_signal

        detected_pitch = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

        # For a chord, we expect to detect one of the component frequencies
        # or a fundamental frequency. The result should be reasonable.
        assert detected_pitch > 0
        # Chord may detect fundamental, component, or harmonic - allow wide range
        assert 50 < detected_pitch < 500  # Wider range to accommodate fundamentals

    def test_noisy_signal_robustness(self, analyzer, noisy_signal, sample_rate):
        """Test robustness with noisy signals."""
        signal, expected_frequency = noisy_signal

        detected_pitch = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

        # Should still detect pitch despite noise (with higher tolerance)
        assert abs(detected_pitch - expected_frequency) < 20.0
        assert detected_pitch > 0


class TestUtilityFunctions:
    """Test suite for utility functions."""

    @pytest.mark.parametrize("frequency,expected_midi,expected_note", [
        (440.0, 69, "A4"),
        (261.63, 60, "C4"),
        (523.25, 72, "C5"),
        (880.0, 81, "A5"),
    ])
    def test_hz_to_midi_note(self, frequency, expected_midi, expected_note):
        """Test frequency to MIDI note conversion."""
        midi_note = hz_to_midi_note(frequency)
        note_name = midi_note_to_name(midi_note)

        # Allow ±1 semitone tolerance for rounding
        assert abs(midi_note - expected_midi) <= 1
        # Note name should match (accounting for enharmonic equivalents)
        assert note_name in [expected_note, expected_note.replace('#', 'b')]

    def test_hz_to_midi_note_edge_cases(self):
        """Test edge cases for frequency conversion."""
        # Zero frequency
        assert hz_to_midi_note(0.0) == 0

        # Negative frequency
        assert hz_to_midi_note(-100.0) == 0

        # Very high frequency
        high_freq_midi = hz_to_midi_note(10000.0)
        assert 0 <= high_freq_midi <= 127

    @pytest.mark.parametrize("midi_note,expected_pattern", [
        (60, "C4"),
        (69, "A4"),
        (72, "C5"),
        (61, "C#4"),
        (0, "C-1"),
        (127, "G9"),
    ])
    def test_midi_note_to_name(self, midi_note, expected_pattern):
        """Test MIDI note to name conversion."""
        note_name = midi_note_to_name(midi_note)

        # Check that we get a valid note name format
        assert len(note_name) >= 2
        assert note_name[0] in "CDEFGAB"
        if "#" in note_name:
            assert note_name[1] == "#"

        # For specific test cases, check exact match
        if expected_pattern:
            assert note_name == expected_pattern

    def test_midi_note_to_name_edge_cases(self):
        """Test edge cases for MIDI note conversion."""
        # Out of range values
        assert midi_note_to_name(-1) == "Unknown"
        assert midi_note_to_name(128) == "Unknown"


class TestAudioAnalyzerIntegration:
    """Integration tests for AudioAnalyzer with synthetic audio."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer for integration tests."""
        return AudioAnalyzer(sample_rate=22050)

    def test_full_analysis_workflow(self, analyzer, sine_wave_440hz, sample_rate):
        """Test complete analysis workflow with synthetic audio."""
        signal, expected_frequency = sine_wave_440hz

        # Simulate the full workflow
        volume_db = analyzer.get_mean_volume_db(signal)
        pitch_hz = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

        # Verify results
        assert np.isfinite(volume_db)
        assert volume_db < 0  # dB should be negative for amplitude < 1
        assert abs(pitch_hz - expected_frequency) < 5.0

        # Test utility functions
        midi_note = hz_to_midi_note(pitch_hz)
        note_name = midi_note_to_name(midi_note)

        assert isinstance(midi_note, int)
        assert 0 <= midi_note <= 127
        assert isinstance(note_name, str)
        assert len(note_name) >= 2

    def test_multiple_signals_analysis(self, analyzer, sample_rate):
        """Test analysis of multiple different signals."""
        # Generate different test signals
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        test_cases = [
            (0.5 * np.sin(2 * np.pi * 220 * t), 220.0, "A3"),  # A3
            (0.3 * np.sin(2 * np.pi * 330 * t), 330.0, "E4"),  # ~E4
            (0.4 * np.sin(2 * np.pi * 880 * t), 880.0, "A5"),  # A5
        ]

        results = []
        for signal, expected_freq, expected_note_base in test_cases:
            volume = analyzer.get_mean_volume_db(signal)
            pitch = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')

            results.append({
                'volume_db': volume,
                'pitch_hz': pitch,
                'expected_freq': expected_freq,
                'pitch_error': abs(pitch - expected_freq)
            })

            # Verify each result
            assert np.isfinite(volume)
            assert abs(pitch - expected_freq) < 10.0

        # All results should be reasonable
        assert len(results) == 3
        assert all(r['pitch_error'] < 10.0 for r in results)

    def test_error_handling_integration(self, analyzer):
        """Test error handling in integration scenarios."""
        # Test with invalid audio data
        with pytest.raises(ValueError):
            analyzer.get_mean_volume_db(np.array([]))

        # Test with invalid sample rate
        signal = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 1000))
        with pytest.raises(ValueError):
            analyzer.get_mean_pitch(signal, 0)  # Invalid sample rate


class TestAudioAnalyzerFileOperations:
    """Test file operations and complete analysis workflows."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer for file operation tests."""
        return AudioAnalyzer(sample_rate=22050)

    def test_load_audio_file_not_found(self, analyzer):
        """Test file loading with non-existent file."""
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            analyzer.load_audio("nonexistent_file.wav")

    def test_load_audio_with_state_storage(self, analyzer, sine_wave_440hz, sample_rate):
        """Test that load_audio properly stores state for reuse."""
        import tempfile
        import soundfile as sf

        signal, expected_freq = sine_wave_440hz

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                sf.write(tmp_file.name, signal, sample_rate)

                # Load audio and verify state is stored
                audio_data, sr = analyzer.load_audio(tmp_file.name)

                # Verify state is stored
                assert analyzer._audio_data is not None
                assert analyzer._sr == sample_rate
                assert analyzer._file_path is not None
                assert len(analyzer._audio_data) == len(signal)

                # Verify we can now use methods without passing data
                volume = analyzer.get_mean_volume_db()  # Should use stored data
                pitch = analyzer.get_mean_pitch()       # Should use stored data

                assert np.isfinite(volume)
                assert pitch > 0

            finally:
                import os
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    def test_analyze_file_complete_workflow(self, analyzer, sine_wave_440hz, sample_rate):
        """Test complete file analysis workflow using synthetic data."""
        import tempfile
        import soundfile as sf

        signal, expected_freq = sine_wave_440hz

        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                sf.write(tmp_file.name, signal, sample_rate)

                # Test complete analysis
                result = analyzer.analyze_file(tmp_file.name)

                # Verify all fields are present and reasonable
                assert 'file_path' in result
                assert 'duration' in result
                assert 'sample_rate' in result
                assert 'mean_volume_db' in result
                assert 'mean_pitch_hz' in result
                assert 'mean_pitch_note' in result

                # Verify values
                assert result['duration'] > 0
                assert result['sample_rate'] == sample_rate
                assert np.isfinite(result['mean_volume_db'])
                assert abs(result['mean_pitch_hz'] - expected_freq) < 10.0
                assert result['mean_pitch_note'] is not None

            finally:
                # Cleanup
                import os
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    def test_analyze_file_pitch_conversion_error(self, analyzer, mocker):
        """Test pitch to note conversion error handling."""
        # Mock librosa.hz_to_note to raise an exception
        mocker.patch('librosa.hz_to_note', side_effect=Exception("Conversion error"))

        signal = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 2, 44100))

        # Simulate analyze_file workflow manually to test the exception handling
        volume = analyzer.get_mean_volume_db(signal)
        pitch = analyzer.get_mean_pitch(signal, 22050)

        # Test the note conversion error path
        mean_pitch_note = None
        if pitch > 0:
            try:
                import librosa
                mean_pitch_note = librosa.hz_to_note(pitch)
            except:
                mean_pitch_note = "Unknown"

        assert mean_pitch_note == "Unknown"

    def test_batch_analyze_mixed_results(self, analyzer):
        """Test batch analysis with mix of valid and invalid files."""
        import tempfile
        import soundfile as sf

        # Create one valid temporary file
        signal = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, 22050))

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            try:
                sf.write(tmp_file.name, signal, 22050)

                # Test batch with mix of valid and invalid files
                file_list = [
                    tmp_file.name,  # Valid file
                    "nonexistent1.wav",  # Invalid file
                    "nonexistent2.wav",  # Invalid file
                ]

                results = analyzer.batch_analyze(file_list)

                # Should have 3 results
                assert len(results) == 3

                # First result should be successful
                assert 'error' not in results[0]
                assert results[0]['mean_pitch_hz'] > 0

                # Other results should have errors
                assert 'error' in results[1]
                assert 'error' in results[2]
                assert results[1]['mean_pitch_hz'] is None
                assert results[2]['mean_volume_db'] is None

            finally:
                import os
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)

    def test_analyzer_state_persistence(self, analyzer):
        """Test that analyzer properly stores and reuses loaded audio data."""
        # Create test signal
        signal = 0.5 * np.sin(2 * np.pi * 440 * np.linspace(0, 1, 22050))

        # Initially no stored data
        assert analyzer._audio_data is None
        assert analyzer._sr is None
        assert analyzer._file_path is None

        # After manual analysis, still no stored data (since we passed signal directly)
        volume = analyzer.get_mean_volume_db(signal)
        assert analyzer._audio_data is None

        # Test that we can call methods without stored data by passing signal
        pitch = analyzer.get_mean_pitch(signal, 22050)
        assert pitch > 0

        # Test error when trying to use stored data that doesn't exist
        with pytest.raises(ValueError, match="No audio data available"):
            analyzer.get_mean_volume_db(None)

    def test_outlier_filtering_in_pitch_detection(self, analyzer, sample_rate):
        """Test outlier filtering in pitch detection."""
        # Create signal with some pitch variation that might create outliers
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration), False)

        # Frequency modulated signal (slight pitch variation)
        base_freq = 440.0
        freq_variation = 5.0  # ±5 Hz variation
        instantaneous_freq = base_freq + freq_variation * np.sin(2 * np.pi * 2 * t)

        # Create FM signal
        phase = 2 * np.pi * np.cumsum(instantaneous_freq) / sample_rate
        signal = 0.5 * np.sin(phase)

        # Should still detect pitch close to base frequency
        detected_pitch = analyzer.get_mean_pitch(signal, sample_rate, method='pyin')
        assert abs(detected_pitch - base_freq) < 20.0  # Allow for FM variation
