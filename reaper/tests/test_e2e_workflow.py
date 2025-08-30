"""
End-to-end tests for the complete automation workflow.
Tests MIDI generation, session configuration, and system integration.
"""

import pytest
import tempfile
import subprocess
from pathlib import Path
import json
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import ConfigManager, SessionConfig, MIDIConfig


class TestEndToEndWorkflow:
    """Test the complete automation workflow from MIDI generation to session config."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create necessary directories
            (workspace / "configs").mkdir()
            (workspace / "midi").mkdir()
            (workspace / "outputs").mkdir()

            yield workspace

    def test_midi_generation(self, temp_workspace):
        """Test MIDI file generation with different parameters."""
        midi_file = temp_workspace / "test_melody.mid"

        # Test the MIDI generator script
        cmd = [
            "uv", "run", "python", "generate_random_midi.py",
            "--output", str(midi_file),
            "--pattern", "melody",
            "--key", "C",
            "--scale", "major",
            "--tempo", "120",
            "--seed", "123"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)

        assert result.returncode == 0, f"MIDI generation failed: {result.stderr}"
        assert midi_file.exists(), "MIDI file was not created"
        assert midi_file.stat().st_size > 0, "MIDI file is empty"

        # Test different pattern types
        patterns = ["chords", "bass", "drums"]
        for pattern in patterns:
            pattern_file = temp_workspace / f"test_{pattern}.mid"
            cmd[5] = str(pattern_file)  # Update output path
            cmd[7] = pattern  # Update pattern type

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            assert result.returncode == 0, f"Failed to generate {pattern} pattern: {result.stderr}"
            assert pattern_file.exists(), f"{pattern} MIDI file was not created"

    def test_session_config_creation_and_loading(self, temp_workspace):
        """Test creating and loading session configurations."""
        # Create config manager with temp workspace
        config_manager = ConfigManager(temp_workspace / "configs")

        # Create a mock project file
        project_file = temp_workspace / "test_project.rpp"
        project_file.write_text("mock project content")

        # Create a session config
        session = SessionConfig("test_e2e_session")
        session.project_file = str(project_file)

        # Add MIDI config (without actual files for this test)
        midi_config = MIDIConfig()
        session.set_global_midi(midi_config)

        # Add some renders with parameters
        from config import RenderConfig
        for i in range(3):
            render = RenderConfig(f"render_{i+1}")
            render.add_parameter("osc_a_octave", i - 1.0)
            render.add_parameter("filter_cutoff", 0.5 + i * 0.1)
            session.add_render(render)

        # Save configuration
        config_file = config_manager.save_session_config(session)
        assert config_file.exists(), "Config file was not saved"

        # Load configuration
        loaded_session = config_manager.load_session_config("test_e2e_session")
        assert loaded_session.session_name == "test_e2e_session"
        assert len(loaded_session.renders) == 3
        assert loaded_session.project_file == str(project_file)

        # Verify parameter values
        for i, render in enumerate(loaded_session.renders):
            expected_octave = i - 1.0
            expected_cutoff = 0.5 + i * 0.1

            assert abs(render.parameters["osc_a_octave"].value - expected_octave) < 0.001
            assert abs(render.parameters["filter_cutoff"].value - expected_cutoff) < 0.001

    def test_complete_workflow_with_midi(self, temp_workspace):
        """Test complete workflow: generate MIDI, create session, save config."""
        # 1. Generate MIDI files
        midi_dir = temp_workspace / "midi" / "e2e_test"
        midi_dir.mkdir(parents=True)

        midi_files = []
        patterns = [("melody", "C", "major"), ("chords", "Am", "minor")]

        for pattern_type, key, scale in patterns:
            midi_file = midi_dir / f"e2e_{pattern_type}_{key}_{scale}.mid"

            cmd = [
                "uv", "run", "python", "generate_random_midi.py",
                "--output", str(midi_file),
                "--pattern", pattern_type,
                "--key", key.replace("m", ""),
                "--scale", "minor" if "m" in key else scale,
                "--seed", "456"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
            assert result.returncode == 0, f"MIDI generation failed: {result.stderr}"
            midi_files.append(str(midi_file))

        # 2. Create session with MIDI files
        config_manager = ConfigManager(temp_workspace / "configs")
        session = SessionConfig("e2e_complete_test")
        session.output_directory = str(temp_workspace / "outputs" / "e2e_test")

        # Add MIDI configuration
        midi_config = MIDIConfig()
        for midi_file in midi_files:
            midi_config.add_midi_file(midi_file)
        session.set_global_midi(midi_config)

        # Add renders with randomized parameters
        from config import SERUM_PARAMETERS, RenderConfig
        import random
        random.seed(789)

        key_params = ["osc_a_octave", "filter_cutoff", "amp_attack", "amp_release"]

        for i in range(2):
            render = RenderConfig(f"e2e_render_{i+1}")

            for param_name in key_params:
                param_spec = SERUM_PARAMETERS[param_name]
                value = random.uniform(param_spec["min"], param_spec["max"])
                render.add_parameter(param_name, value)

            session.add_render(render)

        # 3. Save and verify session
        config_file = config_manager.save_session_config(session)
        assert config_file.exists()

        # 4. Load and verify
        loaded_session = config_manager.load_session_config("e2e_complete_test")
        assert loaded_session.session_name == "e2e_complete_test"
        assert len(loaded_session.renders) == 2
        assert loaded_session.global_midi_config is not None
        assert len(loaded_session.global_midi_config.midi_files) == 2

        # 5. Verify JSON structure
        with open(config_file, 'r') as f:
            config_data = json.load(f)

        assert "session_name" in config_data
        assert "renders" in config_data
        assert "global_midi_config" in config_data
        assert len(config_data["renders"]) == 2
        assert len(config_data["global_midi_config"]["midi_files"]) == 2

        # Verify parameter structure
        for render_data in config_data["renders"]:
            assert "parameters" in render_data
            assert len(render_data["parameters"]) == len(key_params)

            for param_name in key_params:
                assert param_name in render_data["parameters"]
                param_data = render_data["parameters"][param_name]
                assert "name" in param_data
                assert "value" in param_data
                assert isinstance(param_data["value"], (int, float))

    def test_serum_parameter_sweep_integration(self, temp_workspace):
        """Test Serum parameter sweep generation and configuration."""
        from config import create_serum_parameter_sweep

        # Create parameter sweep
        parameters = ["osc_a_octave", "filter_cutoff"]
        config = create_serum_parameter_sweep("serum_sweep_test", parameters, 2)

        # Should create 2x2 = 4 renders
        assert len(config.renders) == 4

        # Verify each render has the correct parameters
        for render in config.renders:
            assert "osc_a_octave" in render.parameters
            assert "filter_cutoff" in render.parameters

            # Verify parameter ranges
            osc_param = render.parameters["osc_a_octave"]
            assert -3.0 <= osc_param.value <= 3.0

            cutoff_param = render.parameters["filter_cutoff"]
            assert 0.0 <= cutoff_param.value <= 1.0

        # Save and reload
        config_manager = ConfigManager(temp_workspace / "configs")
        config_file = config_manager.save_session_config(config)

        loaded_config = config_manager.load_session_config("serum_sweep_test")
        assert len(loaded_config.renders) == 4

        # Verify parameter values are preserved
        for i, render in enumerate(loaded_config.renders):
            original_render = config.renders[i]

            for param_name in ["osc_a_octave", "filter_cutoff"]:
                original_value = original_render.parameters[param_name].value
                loaded_value = render.parameters[param_name].value
                assert abs(original_value - loaded_value) < 0.001

    def test_logging_system_integration(self, temp_workspace):
        """Test the dual output logging system."""
        from config import DualOutputLogger

        log_file = temp_workspace / "test.log"
        messages = []

        def mock_console_func(msg):
            messages.append(msg)

        # Create logger with file and console output
        logger = DualOutputLogger("test_logger", log_file, mock_console_func)

        # Test different log levels
        logger.info("Test info message", extra_data={"test": "data"})
        logger.warning("Test warning message")
        logger.error("Test error message", extra_data={"error_code": 500})

        # Verify console output
        assert len(messages) == 3
        assert "Test info message" in messages[0]
        assert "Test warning message" in messages[1]
        assert "Test error message" in messages[2]

        # Verify file output
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Test info message" in log_content
        assert "Test warning message" in log_content
        assert "Test error message" in log_content

        # Verify structured log file
        structured_log_file = log_file.with_suffix('.jsonl')
        assert structured_log_file.exists()

        structured_content = structured_log_file.read_text().strip()
        lines = structured_content.split('\n')
        assert len(lines) == 2  # Only info and error have extra_data

        # Parse first structured log entry
        log_entry = json.loads(lines[0])
        assert log_entry['level'] == 'INFO'
        assert log_entry['message'] == 'Test info message'
        assert log_entry['data']['test'] == 'data'


class TestSystemRobustness:
    """Test system robustness and error handling."""

    def test_invalid_midi_file_handling(self, tmp_path):
        """Test handling of invalid MIDI files."""
        from config import MIDIConfig

        config = MIDIConfig()

        # Should raise error for non-existent file
        with pytest.raises(FileNotFoundError):
            config.add_midi_file("nonexistent.mid")

        # Create invalid file (not actually MIDI)
        invalid_file = tmp_path / "invalid.mid"
        invalid_file.write_text("not a midi file")

        # Should accept file that exists (validation happens at REAPER level)
        config.add_midi_file(str(invalid_file))
        assert len(config.midi_files) == 1

    def test_parameter_validation_edge_cases(self):
        """Test parameter validation with edge cases."""
        from config import ParameterConfig

        # Test valid numeric values
        param = ParameterConfig("test", 0.0)
        param.validate()  # Should not raise

        param = ParameterConfig("test", 1.0)
        param.validate()  # Should not raise

        param = ParameterConfig("test", -0.1)
        param.validate()  # Should not raise (no range checking now)

        # Test invalid type
        param = ParameterConfig("test", "not_a_number")
        with pytest.raises(ValueError, match="must be a number"):
            param.validate()

    def test_session_config_validation(self, tmp_path):
        """Test session configuration validation."""
        from config import SessionConfig, RenderConfig

        # Test empty session name
        config = SessionConfig("")
        with pytest.raises(ValueError, match="Session name is required"):
            config.validate()

        # Test non-existent project file
        config = SessionConfig("test")
        config.project_file = "nonexistent.rpp"
        with pytest.raises(ValueError, match="Project file not found"):
            config.validate()

        # Test valid configuration
        project_file = tmp_path / "test.rpp"
        project_file.write_text("mock project")

        config = SessionConfig("test")
        config.project_file = str(project_file)

        render = RenderConfig("test_render")
        render.add_parameter("test_param", 0.5)
        config.add_render(render)

        config.validate()  # Should not raise


class TestPerformanceAndScalability:
    """Test system performance with larger datasets."""

    def test_large_parameter_sweep(self):
        """Test creating large parameter sweeps."""
        from config import create_serum_parameter_sweep

        # Create a 3x3x3 = 27 render sweep
        parameters = ["osc_a_octave", "filter_cutoff", "amp_attack"]
        config = create_serum_parameter_sweep("large_sweep", parameters, 3)

        assert len(config.renders) == 27

        # Verify all combinations are unique
        param_combinations = set()
        for render in config.renders:
            combo = tuple(
                render.parameters[param].value
                for param in parameters
            )
            assert combo not in param_combinations, "Duplicate parameter combination found"
            param_combinations.add(combo)

        assert len(param_combinations) == 27

    def test_multiple_midi_files(self, tmp_path):
        """Test handling multiple MIDI files."""
        from config import MIDIConfig

        config = MIDIConfig()

        # Create multiple MIDI files
        midi_files = []
        for i in range(10):
            midi_file = tmp_path / f"test_{i}.mid"
            midi_file.write_bytes(b"mock midi content")
            config.add_midi_file(str(midi_file))
            midi_files.append(str(midi_file))

        assert len(config.midi_files) == 10

        # Verify all files are present
        for midi_file in midi_files:
            assert midi_file in config.midi_files

        # Test validation
        config.validate()  # Should not raise
