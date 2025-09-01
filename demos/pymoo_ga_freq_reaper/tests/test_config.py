"""
Unit tests for configuration classes.
"""

import pytest
import json
from pathlib import Path
import tempfile
from ga_frequency_demo.config import (
    FxConfig, TrackConfig, ParameterConfig, RenderOptions, RenderConfig, SessionConfig,
    create_basic_serum_session, create_basic_serum_render_config
)


class TestFxConfig:
    def test_fx_config_creation(self):
        fx = FxConfig(name="Serum", plugin_name="Serum")
        assert fx.name == "Serum"
        assert fx.plugin_name == "Serum"


class TestTrackConfig:
    def test_track_config_creation(self):
        fx = FxConfig(name="Serum", plugin_name="Serum")
        track = TrackConfig(index=0, name="Test Track", fx_chain=[fx])

        assert track.index == 0
        assert track.name == "Test Track"
        assert len(track.fx_chain) == 1
        assert track.fx_chain[0].name == "Serum"


class TestParameterConfig:
    def test_parameter_config_creation(self):
        param = ParameterConfig(track="0", fx="Serum", param="A Octave", value=0.5)

        assert param.track == "0"
        assert param.fx == "Serum"
        assert param.param == "A Octave"
        assert param.value == 0.5


class TestRenderOptions:
    def test_render_options_defaults(self):
        options = RenderOptions()

        assert options.sample_rate == 44100
        assert options.channels == 2
        assert options.render_format == ""

    def test_render_options_custom(self):
        options = RenderOptions(sample_rate=48000, channels=1, render_format="wav")

        assert options.sample_rate == 48000
        assert options.channels == 1
        assert options.render_format == "wav"


class TestRenderConfig:
    def test_render_config_creation(self):
        fx = FxConfig(name="Serum", plugin_name="Serum")
        track = TrackConfig(index=0, name="Test Track", fx_chain=[fx])
        param = ParameterConfig(track="0", fx="Serum", param="A Octave", value=0.5)
        options = RenderOptions()

        render_config = RenderConfig(
            render_id="test_render",
            tracks=[track],
            parameters=[param],
            midi_files={"0": "test.mid"},
            render_options=options
        )

        assert render_config.render_id == "test_render"
        assert len(render_config.tracks) == 1
        assert len(render_config.parameters) == 1
        assert render_config.midi_files["0"] == "test.mid"


class TestSessionConfig:
    def test_session_config_creation(self):
        render_config = create_basic_serum_render_config("test_render", 0.5, 0.3)
        session = SessionConfig(session_name="test_session", render_configs=[render_config])

        assert session.session_name == "test_session"
        assert len(session.render_configs) == 1
        assert session.render_configs[0].render_id == "test_render"

    def test_session_to_json(self):
        render_config = create_basic_serum_render_config("test_render", 0.5, 0.3)
        session = SessionConfig(session_name="test_session", render_configs=[render_config])

        json_str = session.to_json()
        assert isinstance(json_str, str)

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["session_name"] == "test_session"
        assert len(data["render_configs"]) == 1

    def test_session_save_and_load(self):
        render_config = create_basic_serum_render_config("test_render", 0.5, 0.3)
        original_session = SessionConfig(session_name="test_session", render_configs=[render_config])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Save to file
            original_session.save_to_file(temp_path)
            assert temp_path.exists()

            # Load from file
            loaded_session = SessionConfig.load_from_file(temp_path)

            # Verify loaded session matches original
            assert loaded_session.session_name == original_session.session_name
            assert len(loaded_session.render_configs) == len(original_session.render_configs)
            assert loaded_session.render_configs[0].render_id == original_session.render_configs[0].render_id

        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_session_from_json(self):
        json_data = {
            "session_name": "test_session",
            "render_configs": [
                {
                    "render_id": "test_render",
                    "tracks": [
                        {
                            "index": 0,
                            "name": "Test Track",
                            "fx_chain": [
                                {"name": "Serum", "plugin_name": "Serum"}
                            ]
                        }
                    ],
                    "parameters": [
                        {"track": "0", "fx": "Serum", "param": "A Octave", "value": 0.5}
                    ],
                    "midi_files": {"0": "test.mid"},
                    "render_options": {"sample_rate": 44100, "channels": 2, "render_format": ""}
                }
            ]
        }

        session = SessionConfig.from_dict(json_data)

        assert session.session_name == "test_session"
        assert len(session.render_configs) == 1
        assert session.render_configs[0].render_id == "test_render"
        assert session.render_configs[0].tracks[0].name == "Test Track"


class TestFactoryFunctions:
    def test_create_basic_serum_render_config(self):
        render_config = create_basic_serum_render_config("test", 0.6, 0.4, "custom.mid")

        assert render_config.render_id == "test"
        assert len(render_config.tracks) == 1
        assert render_config.tracks[0].name == "Serum Track"
        assert len(render_config.parameters) == 2
        assert render_config.midi_files["0"] == "custom.mid"

        # Check parameter values
        octave_param = next(p for p in render_config.parameters if p.param == "A Octave")
        fine_param = next(p for p in render_config.parameters if p.param == "A Fine")

        assert octave_param.value == 0.6
        assert fine_param.value == 0.4

    def test_create_basic_serum_session(self):
        render_config = create_basic_serum_render_config("test", 0.5, 0.3)
        session = create_basic_serum_session("test_session", [render_config])

        assert session.session_name == "test_session"
        assert len(session.render_configs) == 1
        assert session.render_configs[0] == render_config
