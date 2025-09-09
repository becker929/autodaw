"""Tests for src/genetics/config.py module."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

from serum_evolver.src.genetics.config import (
    FxConfig, TrackConfig, ParameterConfig, RenderOptions, RenderConfig, SessionConfig,
    create_basic_serum_session, create_basic_serum_render_config
)


class TestFxConfig:
    """Test cases for FxConfig dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        fx = FxConfig(name="Serum", plugin_name="Serum")
        assert fx.name == "Serum"
        assert fx.plugin_name == "Serum"

    def test_equality(self):
        """Test equality comparison."""
        fx1 = FxConfig(name="Serum", plugin_name="Serum")
        fx2 = FxConfig(name="Serum", plugin_name="Serum")
        fx3 = FxConfig(name="Diva", plugin_name="Diva")

        assert fx1 == fx2
        assert fx1 != fx3

    def test_as_dict(self):
        """Test conversion to dictionary."""
        fx = FxConfig(name="Serum", plugin_name="Serum")
        expected = {"name": "Serum", "plugin_name": "Serum"}
        assert fx.__dict__ == expected


class TestTrackConfig:
    """Test cases for TrackConfig dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        fx = FxConfig(name="Serum", plugin_name="Serum")
        track = TrackConfig(index=0, name="Track 1", fx_chain=[fx])

        assert track.index == 0
        assert track.name == "Track 1"
        assert len(track.fx_chain) == 1
        assert track.fx_chain[0] == fx

    def test_empty_fx_chain(self):
        """Test track with empty FX chain."""
        track = TrackConfig(index=1, name="Empty Track", fx_chain=[])
        assert track.index == 1
        assert track.name == "Empty Track"
        assert len(track.fx_chain) == 0

    def test_multiple_fx_chain(self):
        """Test track with multiple FX."""
        fx1 = FxConfig(name="Serum", plugin_name="Serum")
        fx2 = FxConfig(name="Reverb", plugin_name="ReaVerb")
        track = TrackConfig(index=0, name="Multi FX Track", fx_chain=[fx1, fx2])

        assert len(track.fx_chain) == 2
        assert track.fx_chain[0] == fx1
        assert track.fx_chain[1] == fx2


class TestParameterConfig:
    """Test cases for ParameterConfig dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        param = ParameterConfig(track="0", fx="Serum", param="Octave", value=0.5)

        assert param.track == "0"
        assert param.fx == "Serum"
        assert param.param == "Octave"
        assert param.value == 0.5

    def test_different_value_types(self):
        """Test with different value types."""
        param_int = ParameterConfig(track="1", fx="EQ", param="Gain", value=1)
        param_float = ParameterConfig(track="1", fx="EQ", param="Freq", value=440.0)
        param_negative = ParameterConfig(track="1", fx="EQ", param="Phase", value=-0.5)

        assert param_int.value == 1
        assert param_float.value == 440.0
        assert param_negative.value == -0.5


class TestRenderOptions:
    """Test cases for RenderOptions dataclass."""

    def test_initialization_defaults(self):
        """Test initialization with default values."""
        options = RenderOptions()
        assert options.sample_rate == 44100
        assert options.channels == 2
        assert options.render_format == ""

    def test_initialization_custom(self):
        """Test initialization with custom values."""
        options = RenderOptions(sample_rate=48000, channels=1, render_format="wav")
        assert options.sample_rate == 48000
        assert options.channels == 1
        assert options.render_format == "wav"

    def test_partial_custom_values(self):
        """Test initialization with partial custom values."""
        options = RenderOptions(sample_rate=96000)
        assert options.sample_rate == 96000
        assert options.channels == 2  # default
        assert options.render_format == ""  # default


class TestRenderConfig:
    """Test cases for RenderConfig dataclass."""

    def test_initialization(self):
        """Test basic initialization."""
        fx = FxConfig(name="Serum", plugin_name="Serum")
        track = TrackConfig(index=0, name="Track", fx_chain=[fx])
        param = ParameterConfig(track="0", fx="Serum", param="Octave", value=0.5)
        options = RenderOptions()

        config = RenderConfig(
            render_id="test_001",
            tracks=[track],
            parameters=[param],
            midi_files={"0": "test.mid"},
            render_options=options
        )

        assert config.render_id == "test_001"
        assert len(config.tracks) == 1
        assert config.tracks[0] == track
        assert len(config.parameters) == 1
        assert config.parameters[0] == param
        assert config.midi_files == {"0": "test.mid"}
        assert config.render_options == options

    def test_empty_collections(self):
        """Test with empty tracks and parameters."""
        config = RenderConfig(
            render_id="empty",
            tracks=[],
            parameters=[],
            midi_files={},
            render_options=RenderOptions()
        )

        assert len(config.tracks) == 0
        assert len(config.parameters) == 0
        assert config.midi_files == {}


class TestSessionConfig:
    """Test cases for SessionConfig dataclass."""

    def setup_method(self):
        """Set up test fixtures."""
        self.fx = FxConfig(name="Serum", plugin_name="Serum")
        self.track = TrackConfig(index=0, name="Track", fx_chain=[self.fx])
        self.param = ParameterConfig(track="0", fx="Serum", param="Octave", value=0.5)
        self.render_config = RenderConfig(
            render_id="test_001",
            tracks=[self.track],
            parameters=[self.param],
            midi_files={"0": "test.mid"},
            render_options=RenderOptions()
        )
        self.session = SessionConfig(
            session_name="test_session",
            render_configs=[self.render_config]
        )

    def test_initialization(self):
        """Test basic initialization."""
        assert self.session.session_name == "test_session"
        assert len(self.session.render_configs) == 1
        assert self.session.render_configs[0] == self.render_config

    def test_to_json(self):
        """Test JSON serialization."""
        json_str = self.session.to_json()

        # Should be valid JSON
        data = json.loads(json_str)

        # Check structure
        assert data["session_name"] == "test_session"
        assert len(data["render_configs"]) == 1

        render_config = data["render_configs"][0]
        assert render_config["render_id"] == "test_001"
        assert len(render_config["tracks"]) == 1
        assert len(render_config["parameters"]) == 1

    def test_from_dict(self):
        """Test loading from dictionary."""
        data = {
            "session_name": "loaded_session",
            "render_configs": [{
                "render_id": "loaded_001",
                "tracks": [{
                    "index": 1,
                    "name": "Loaded Track",
                    "fx_chain": [{"name": "Loaded FX", "plugin_name": "LoadedPlugin"}]
                }],
                "parameters": [{
                    "track": "1",
                    "fx": "Loaded FX",
                    "param": "LoadedParam",
                    "value": 0.75
                }],
                "midi_files": {"1": "loaded.mid"},
                "render_options": {
                    "sample_rate": 48000,
                    "channels": 1,
                    "render_format": "wav"
                }
            }]
        }

        session = SessionConfig.from_dict(data)

        assert session.session_name == "loaded_session"
        assert len(session.render_configs) == 1

        rc = session.render_configs[0]
        assert rc.render_id == "loaded_001"
        assert len(rc.tracks) == 1
        assert rc.tracks[0].name == "Loaded Track"
        assert rc.tracks[0].index == 1
        assert len(rc.tracks[0].fx_chain) == 1
        assert rc.tracks[0].fx_chain[0].name == "Loaded FX"

        assert len(rc.parameters) == 1
        assert rc.parameters[0].value == 0.75

        assert rc.midi_files == {"1": "loaded.mid"}
        assert rc.render_options.sample_rate == 48000

    def test_from_dict_default_render_options(self):
        """Test loading from dictionary with missing render_options."""
        data = {
            "session_name": "minimal_session",
            "render_configs": [{
                "render_id": "minimal_001",
                "tracks": [],
                "parameters": [],
                "midi_files": {}
            }]
        }

        session = SessionConfig.from_dict(data)
        rc = session.render_configs[0]

        # Should use default render options
        assert rc.render_options.sample_rate == 44100
        assert rc.render_options.channels == 2
        assert rc.render_options.render_format == ""

    def test_from_json(self):
        """Test loading from JSON string."""
        json_str = self.session.to_json()
        loaded_session = SessionConfig.from_json(json_str)

        assert loaded_session.session_name == self.session.session_name
        assert len(loaded_session.render_configs) == len(self.session.render_configs)

    def test_round_trip_serialization(self):
        """Test that serialization and deserialization preserve data."""
        json_str = self.session.to_json()
        loaded_session = SessionConfig.from_json(json_str)

        # Should be equivalent (though not necessarily identical due to object instances)
        assert loaded_session.session_name == self.session.session_name
        assert len(loaded_session.render_configs) == len(self.session.render_configs)

        original_rc = self.session.render_configs[0]
        loaded_rc = loaded_session.render_configs[0]

        assert loaded_rc.render_id == original_rc.render_id
        assert len(loaded_rc.tracks) == len(original_rc.tracks)
        assert len(loaded_rc.parameters) == len(original_rc.parameters)

    def test_save_to_file(self):
        """Test saving to file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            self.session.save_to_file(temp_path)

            # File should exist and contain valid JSON
            assert temp_path.exists()

            with open(temp_path, 'r') as f:
                content = f.read()
                data = json.loads(content)
                assert data["session_name"] == "test_session"
        finally:
            temp_path.unlink(missing_ok=True)

    def test_load_from_file(self):
        """Test loading from file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Save first
            self.session.save_to_file(temp_path)

            # Load back
            loaded_session = SessionConfig.load_from_file(temp_path)

            assert loaded_session.session_name == self.session.session_name
            assert len(loaded_session.render_configs) == len(self.session.render_configs)
        finally:
            temp_path.unlink(missing_ok=True)

    @patch("builtins.open", new_callable=mock_open, read_data='{"invalid": "json"}')
    def test_from_json_invalid_structure(self, mock_file):
        """Test loading from JSON with invalid structure."""
        with pytest.raises(KeyError):
            SessionConfig.from_json('{"invalid": "json"}')

    def test_from_json_malformed(self):
        """Test loading from malformed JSON."""
        with pytest.raises(json.JSONDecodeError):
            SessionConfig.from_json('{"invalid": json}')


class TestHelperFunctions:
    """Test cases for helper functions."""

    def test_create_basic_serum_session(self):
        """Test create_basic_serum_session function."""
        render_config = create_basic_serum_render_config("test_001", 0.5, -0.3)
        session = create_basic_serum_session("test_session", [render_config])

        assert session.session_name == "test_session"
        assert len(session.render_configs) == 1
        assert session.render_configs[0] == render_config

    def test_create_basic_serum_render_config_defaults(self):
        """Test create_basic_serum_render_config with default values."""
        config = create_basic_serum_render_config("test_001", 0.5, -0.3)

        assert config.render_id == "test_001"
        assert len(config.tracks) == 1

        track = config.tracks[0]
        assert track.index == 0
        assert track.name == "Serum Track"
        assert len(track.fx_chain) == 1
        assert track.fx_chain[0].name == "Serum"

        assert len(config.parameters) == 2
        octave_param = next(p for p in config.parameters if p.param == "A Octave")
        fine_param = next(p for p in config.parameters if p.param == "A Fine")

        assert octave_param.value == 0.5
        assert fine_param.value == -0.3

        assert config.midi_files == {"0": "test_melody.mid"}
        assert config.render_options.sample_rate == 44100

    def test_create_basic_serum_render_config_custom_midi(self):
        """Test create_basic_serum_render_config with custom MIDI file."""
        config = create_basic_serum_render_config("test_002", 1.0, 0.0, "custom.mid")

        assert config.midi_files == {"0": "custom.mid"}

    def test_create_basic_serum_render_config_parameter_values(self):
        """Test create_basic_serum_render_config with various parameter values."""
        test_cases = [
            (0.0, 0.0),
            (-1.0, -1.0),
            (1.0, 1.0),
            (0.5, -0.5),
            (2.0, -2.0)
        ]

        for octave, fine in test_cases:
            config = create_basic_serum_render_config("test", octave, fine)

            octave_param = next(p for p in config.parameters if p.param == "A Octave")
            fine_param = next(p for p in config.parameters if p.param == "A Fine")

            assert octave_param.value == octave
            assert fine_param.value == fine

    def test_integration_workflow(self):
        """Test a complete workflow using all components."""
        # Create multiple render configs
        configs = [
            create_basic_serum_render_config("config_1", 0.0, 0.0),
            create_basic_serum_render_config("config_2", 1.0, 0.5, "melody2.mid"),
            create_basic_serum_render_config("config_3", -1.0, -0.5, "melody3.mid")
        ]

        # Create session
        session = create_basic_serum_session("integration_test", configs)

        # Serialize and deserialize
        json_str = session.to_json()
        loaded_session = SessionConfig.from_json(json_str)

        # Verify integrity
        assert loaded_session.session_name == "integration_test"
        assert len(loaded_session.render_configs) == 3

        # Check specific values
        config_2 = next(rc for rc in loaded_session.render_configs if rc.render_id == "config_2")
        octave_param = next(p for p in config_2.parameters if p.param == "A Octave")
        assert octave_param.value == 1.0
        assert config_2.midi_files == {"0": "melody2.mid"}
