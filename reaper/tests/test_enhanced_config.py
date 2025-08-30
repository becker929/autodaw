"""Tests for enhanced configuration system with JSON-based session management."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from config import (
    MIDIConfig, ParameterConfig, RenderConfig, SessionConfig, ConfigManager,
    DualOutputLogger, REAPERConsoleHandler, SERUM_PARAMETERS,
    create_serum_parameter_sweep
)


class TestMIDIConfig:
    """Test MIDI configuration functionality."""

    def test_midi_config_initialization(self):
        """Test MIDI config initialization with defaults."""
        config = MIDIConfig()

        assert config.midi_files == []
        assert config.track_index == 0
        assert config.clear_existing is True

    def test_add_midi_file(self, tmp_path):
        """Test adding MIDI files to configuration."""
        config = MIDIConfig()

        # Create mock MIDI files
        midi_file1 = tmp_path / "test1.mid"
        midi_file2 = tmp_path / "test2.mid"
        midi_file1.write_bytes(b"mock midi content")
        midi_file2.write_bytes(b"mock midi content")

        config.add_midi_file(str(midi_file1))
        config.add_midi_file(str(midi_file2))

        assert len(config.midi_files) == 2
        assert str(midi_file1) in config.midi_files
        assert str(midi_file2) in config.midi_files

    def test_add_midi_file_validation(self, tmp_path):
        """Test MIDI file validation."""
        config = MIDIConfig()

        # Create a mock MIDI file
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"mock midi content")

        # Should work with existing file
        config.add_midi_file(str(midi_file))
        assert len(config.midi_files) == 1

        # Should fail with non-existent file
        with pytest.raises(FileNotFoundError):
            config.add_midi_file("nonexistent.mid")

    def test_midi_config_validate(self, tmp_path):
        """Test MIDI config validation."""
        config = MIDIConfig()

        # Create mock MIDI file
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"mock midi content")

        config.add_midi_file(str(midi_file))
        config.validate()  # Should not raise

        # Add non-existent file and validate should fail
        config.midi_files.append("nonexistent.mid")
        with pytest.raises(FileNotFoundError):
            config.validate()


class TestParameterConfig:
    """Test parameter configuration functionality."""

    def test_parameter_config_creation(self):
        """Test parameter config creation."""
        param = ParameterConfig("octave", 1.0)

        assert param.name == "octave"
        assert param.value == 1.0

    def test_parameter_validation_success(self):
        """Test successful parameter validation."""
        param = ParameterConfig("cutoff", 0.5)
        param.validate()  # Should not raise

    def test_parameter_validation_failure(self):
        """Test parameter validation failure."""
        param = ParameterConfig("octave", "invalid_value")  # Non-numeric value

        with pytest.raises(ValueError, match="must be a number"):
            param.validate()


class TestRenderConfig:
    """Test render configuration functionality."""

    def test_render_config_creation(self):
        """Test render config creation."""
        render = RenderConfig("test_render")

        assert render.name == "test_render"
        assert render.parameters == {}
        assert render.midi_config is None
        assert render.output_filename is None
        assert render.render_length == 30.0
        assert render.render_quality == "high"

    def test_add_parameter(self):
        """Test adding parameters to render config."""
        render = RenderConfig("test")
        render.add_parameter("octave", 1.0)
        render.add_parameter("cutoff", 0.5)

        assert len(render.parameters) == 2
        assert "octave" in render.parameters
        assert "cutoff" in render.parameters
        assert render.parameters["octave"].value == 1.0
        assert render.parameters["cutoff"].value == 0.5

    def test_set_midi_config(self, tmp_path):
        """Test setting MIDI configuration."""
        render = RenderConfig("test")
        midi_config = MIDIConfig()

        # Create mock MIDI file
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"mock midi content")
        midi_config.add_midi_file(str(midi_file))

        render.set_midi_config(midi_config)
        assert render.midi_config is not None
        assert len(render.midi_config.midi_files) == 1

    def test_render_validation_success(self):
        """Test successful render validation."""
        render = RenderConfig("test")
        render.add_parameter("octave", 0.0)
        render.validate()  # Should not raise

    def test_render_validation_invalid_length(self):
        """Test render validation with invalid length."""
        render = RenderConfig("test", render_length=-1.0)

        with pytest.raises(ValueError, match="Render length must be positive"):
            render.validate()

    def test_render_validation_invalid_quality(self):
        """Test render validation with invalid quality."""
        render = RenderConfig("test", render_quality="invalid")

        with pytest.raises(ValueError, match="Invalid render quality"):
            render.validate()


class TestSessionConfig:
    """Test session configuration functionality."""

    def test_session_config_creation(self):
        """Test session config creation."""
        config = SessionConfig("test_session")

        assert config.session_name == "test_session"
        assert len(config.session_id) == 8  # UUID truncated to 8 chars
        assert config.project_file is None
        assert config.renders == []
        assert config.global_midi_config is None
        assert config.output_directory == "./outputs"
        assert config.metadata == {}

    def test_add_render(self):
        """Test adding renders to session."""
        config = SessionConfig("test")
        render1 = RenderConfig("render1")
        render2 = RenderConfig("render2")

        config.add_render(render1)
        config.add_render(render2)

        assert len(config.renders) == 2
        assert config.renders[0].name == "render1"
        assert config.renders[1].name == "render2"

    def test_set_global_midi(self, tmp_path):
        """Test setting global MIDI configuration."""
        config = SessionConfig("test")
        midi_config = MIDIConfig()

        # Create mock MIDI file
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"mock midi content")
        midi_config.add_midi_file(str(midi_file))

        config.set_global_midi(midi_config)
        assert config.global_midi_config is not None
        assert len(config.global_midi_config.midi_files) == 1

    def test_session_validation_success(self):
        """Test successful session validation."""
        config = SessionConfig("test_session")
        render = RenderConfig("test_render")
        config.add_render(render)

        config.validate()  # Should not raise

    def test_session_validation_no_name(self):
        """Test session validation failure with no name."""
        config = SessionConfig("")

        with pytest.raises(ValueError, match="Session name is required"):
            config.validate()

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = SessionConfig("test")
        render = RenderConfig("render1")
        render.add_parameter("octave", 0.0)
        config.add_render(render)

        data = config.to_dict()

        assert isinstance(data, dict)
        assert data['session_name'] == "test"
        assert len(data['renders']) == 1
        assert data['renders'][0]['name'] == "render1"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'session_name': 'test_session',
            'session_id': 'test123',
            'renders': [{
                'name': 'render1',
                'parameters': {
                                    'octave': {
                    'name': 'octave',
                    'value': 1.0
                }
                },
                'render_length': 30.0,
                'render_quality': 'high'
            }]
        }

        config = SessionConfig.from_dict(data)

        assert config.session_name == 'test_session'
        assert config.session_id == 'test123'
        assert len(config.renders) == 1
        assert config.renders[0].name == 'render1'
        assert 'octave' in config.renders[0].parameters


class TestConfigManager:
    """Test configuration manager functionality."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_config_manager_initialization(self, temp_config_dir):
        """Test config manager initialization."""
        manager = ConfigManager(temp_config_dir)

        assert manager.base_config_dir == temp_config_dir
        assert temp_config_dir.exists()

    def test_save_and_load_session_config(self, temp_config_dir):
        """Test saving and loading session configuration."""
        manager = ConfigManager(temp_config_dir)

        # Create config
        config = SessionConfig("test_session")
        render = RenderConfig("test_render")
        render.add_parameter("octave", 1.0)
        config.add_render(render)

        # Save config
        config_file = manager.save_session_config(config)
        assert config_file.exists()

        # Load config
        loaded_config = manager.load_session_config("test_session")
        assert loaded_config.session_name == "test_session"
        assert len(loaded_config.renders) == 1
        assert loaded_config.renders[0].name == "test_render"

    def test_list_session_configs(self, temp_config_dir):
        """Test listing session configurations."""
        manager = ConfigManager(temp_config_dir)

        # Create and save configs
        config1 = SessionConfig("session1")
        config2 = SessionConfig("session2")
        manager.save_session_config(config1)
        manager.save_session_config(config2)

        # List configs
        configs = manager.list_session_configs()
        assert len(configs) == 2
        assert "session1" in configs
        assert "session2" in configs

    def test_delete_session_config(self, temp_config_dir):
        """Test deleting session configuration."""
        manager = ConfigManager(temp_config_dir)

        # Create and save config
        config = SessionConfig("test_session")
        manager.save_session_config(config)

        # Verify exists
        assert len(manager.list_session_configs()) == 1

        # Delete config
        result = manager.delete_session_config("test_session")
        assert result is True
        assert len(manager.list_session_configs()) == 0

        # Try to delete non-existent
        result = manager.delete_session_config("nonexistent")
        assert result is False

    def test_create_template_config(self, temp_config_dir):
        """Test creating template configuration."""
        manager = ConfigManager(temp_config_dir)

        config = manager.create_template_config("template_session", "project.rpp")

        assert config.session_name == "template_session"
        assert config.project_file == "project.rpp"
        assert config.global_midi_config is not None
        assert len(config.global_midi_config.midi_files) == 0  # Empty by default
        assert len(config.renders) == 2  # Default renders


class TestDualOutputLogger:
    """Test dual output logging functionality."""

    def test_logger_creation(self):
        """Test logger creation without file."""
        logger = DualOutputLogger("test_logger")

        assert logger.name == "test_logger"
        assert logger.log_file is None
        assert logger.logger is not None

    def test_logger_with_file(self):
        """Test logger creation with file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = DualOutputLogger("test_logger", log_file)

            assert logger.log_file == log_file
            logger.info("Test message")

            # Check file was created and has content
            assert log_file.exists()
            content = log_file.read_text()
            assert "Test message" in content

    def test_structured_logging(self):
        """Test structured data logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            logger = DualOutputLogger("test_logger", log_file)

            logger.info("Test message", extra_data={'key': 'value', 'number': 42})

            # Check structured log file exists
            structured_file = log_file.with_suffix('.jsonl')
            assert structured_file.exists()

            # Check structured content
            content = structured_file.read_text()
            data = json.loads(content.strip())
            assert data['message'] == "Test message"
            assert data['data']['key'] == 'value'
            assert data['data']['number'] == 42


class TestSerumParameters:
    """Test Serum parameter definitions and sweep generation."""

    def test_serum_parameters_exist(self):
        """Test that Serum parameters are defined."""
        assert isinstance(SERUM_PARAMETERS, dict)
        assert len(SERUM_PARAMETERS) > 0

        # Check some expected parameters
        assert "osc_a_octave" in SERUM_PARAMETERS
        assert "filter_cutoff" in SERUM_PARAMETERS
        assert "amp_attack" in SERUM_PARAMETERS

    def test_serum_parameter_structure(self):
        """Test Serum parameter structure."""
        for param_name, param_spec in SERUM_PARAMETERS.items():
            assert isinstance(param_spec, dict)
            assert "min" in param_spec
            assert "max" in param_spec
            assert "default" in param_spec
            assert param_spec["min"] <= param_spec["default"] <= param_spec["max"]

    def test_create_serum_parameter_sweep(self):
        """Test creating Serum parameter sweep."""
        parameters = ["osc_a_octave", "filter_cutoff"]
        config = create_serum_parameter_sweep("test_sweep", parameters, 3)

        assert config.session_name == "test_sweep"
        assert len(config.renders) == 9  # 3 x 3 combinations

        # Check that all renders have the correct parameters
        for render in config.renders:
            assert "osc_a_octave" in render.parameters
            assert "filter_cutoff" in render.parameters

    def test_serum_sweep_invalid_parameter(self):
        """Test error handling for invalid Serum parameter."""
        with pytest.raises(ValueError, match="Unknown Serum parameter"):
            create_serum_parameter_sweep("test", ["invalid_param"])

    def test_serum_sweep_no_parameters(self):
        """Test error handling for no parameters."""
        with pytest.raises(ValueError, match="At least one parameter must be specified"):
            create_serum_parameter_sweep("test", [])


class TestREAPERConsoleHandler:
    """Test REAPER console handler."""

    def test_console_handler_creation(self):
        """Test console handler creation."""
        handler = REAPERConsoleHandler()
        assert handler.console_func == print

    def test_console_handler_custom_function(self):
        """Test console handler with custom function."""
        messages = []
        def custom_print(msg):
            messages.append(msg)

        handler = REAPERConsoleHandler(custom_print)
        assert handler.console_func == custom_print

        # Test emit (requires a proper log record)
        import logging
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        handler.emit(record)

        assert len(messages) == 1
        assert "Test message" in messages[0]


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features."""

    def test_complete_session_workflow(self, tmp_path):
        """Test complete session configuration workflow."""
        # Create config manager
        manager = ConfigManager(tmp_path)

        # Create a mock project file
        project_file = tmp_path / "test_project.rpp"
        project_file.write_text("mock project content")

        # Create session with MIDI and multiple renders
        session = SessionConfig("integration_test")
        session.project_file = str(project_file)

        # Add MIDI configuration
        midi_config = MIDIConfig()
        midi_file = tmp_path / "test.mid"
        midi_file.write_bytes(b"mock midi content")
        midi_config.add_midi_file(str(midi_file))
        session.set_global_midi(midi_config)

        # Add multiple renders with different parameters
        for i in range(3):
            render = RenderConfig(f"render_{i}")
            render.add_parameter("octave", i - 1.0)
            render.add_parameter("filter_cutoff", 0.5 + i * 0.2)
            session.add_render(render)

        # Save configuration
        config_file = manager.save_session_config(session)
        assert config_file.exists()

        # Load and verify
        loaded_session = manager.load_session_config("integration_test")
        assert loaded_session.session_name == "integration_test"
        assert loaded_session.project_file == str(project_file)
        assert len(loaded_session.renders) == 3
        assert loaded_session.global_midi_config is not None
        assert len(loaded_session.global_midi_config.midi_files) == 1

        # Verify parameter values
        for i, render in enumerate(loaded_session.renders):
            assert render.parameters["octave"].value == i - 1.0
            expected_cutoff = 0.5 + i * 0.2
            assert abs(render.parameters["filter_cutoff"].value - expected_cutoff) < 0.001

    def test_serum_sweep_with_midi(self):
        """Test Serum parameter sweep with MIDI configuration."""
        # Create parameter sweep
        config = create_serum_parameter_sweep("serum_test", ["osc_a_octave", "amp_attack"], 2)

                # Add MIDI configuration
        midi_config = MIDIConfig()
        # Note: In real usage, user would add actual MIDI files
        config.set_global_midi(midi_config)

        # Verify structure
        assert len(config.renders) == 4  # 2 x 2 combinations
        assert config.global_midi_config is not None

                # Verify each render has correct parameters
        for render in config.renders:
            assert "osc_a_octave" in render.parameters
            assert "amp_attack" in render.parameters

            # Check parameter values are reasonable
            osc_param = render.parameters["osc_a_octave"]
            assert isinstance(osc_param.value, (int, float))

            amp_param = render.parameters["amp_attack"]
            assert isinstance(amp_param.value, (int, float))
