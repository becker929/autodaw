"""
Configuration classes for REAPER session and render configs.
These classes generate JSON configurations compatible with the Lua session manager.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass
class FxConfig:
    """Configuration for a single FX plugin"""
    name: str
    plugin_name: str


@dataclass
class TrackConfig:
    """Configuration for a single track"""
    index: int
    name: str
    fx_chain: List[FxConfig]


@dataclass
class ParameterConfig:
    """Configuration for a single FX parameter"""
    track: str
    fx: str
    param: str
    value: float


@dataclass
class RenderOptions:
    """Render options for audio output"""
    sample_rate: int = 44100
    channels: int = 2
    render_format: str = ""


@dataclass
class RenderConfig:
    """Configuration for a single render variation"""
    render_id: str
    tracks: List[TrackConfig]
    parameters: List[ParameterConfig]
    midi_files: Dict[str, str]
    render_options: RenderOptions


@dataclass
class SessionConfig:
    """Complete session configuration"""
    session_name: str
    render_configs: List[RenderConfig]

    def to_json(self) -> str:
        """Convert to JSON string compatible with Lua parser"""
        return json.dumps(asdict(self), indent=2)

    def save_to_file(self, file_path: Path) -> None:
        """Save configuration to JSON file"""
        with open(file_path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def from_json(cls, json_str: str) -> 'SessionConfig':
        """Load configuration from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """Load configuration from dictionary"""
        render_configs = []
        for rc_data in data['render_configs']:
            tracks = [
                TrackConfig(
                    index=t['index'],
                    name=t['name'],
                    fx_chain=[FxConfig(**fx) for fx in t['fx_chain']]
                )
                for t in rc_data['tracks']
            ]

            parameters = [ParameterConfig(**p) for p in rc_data['parameters']]

            render_options = RenderOptions(**rc_data.get('render_options', {}))

            render_config = RenderConfig(
                render_id=rc_data['render_id'],
                tracks=tracks,
                parameters=parameters,
                midi_files=rc_data['midi_files'],
                render_options=render_options
            )
            render_configs.append(render_config)

        return cls(
            session_name=data['session_name'],
            render_configs=render_configs
        )

    @classmethod
    def load_from_file(cls, file_path: Path) -> 'SessionConfig':
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            return cls.from_json(f.read())


def create_basic_serum_session(session_name: str, render_configs: List[RenderConfig]) -> SessionConfig:
    """Create a basic session configuration with Serum VST"""
    return SessionConfig(
        session_name=session_name,
        render_configs=render_configs
    )


def create_basic_serum_render_config(
    render_id: str,
    octave_value: float,
    fine_value: float,
    midi_file: str = "test_melody.mid"
) -> RenderConfig:
    """Create a basic render configuration with Serum octave and fine parameters"""
    track = TrackConfig(
        index=0,
        name="Serum Track",
        fx_chain=[FxConfig(name="Serum", plugin_name="Serum")]
    )

    parameters = [
        ParameterConfig(track="0", fx="Serum", param="A Octave", value=octave_value),
        ParameterConfig(track="0", fx="Serum", param="A Fine", value=fine_value)
    ]

    midi_files = {"0": midi_file}

    render_options = RenderOptions()

    return RenderConfig(
        render_id=render_id,
        tracks=[track],
        parameters=parameters,
        midi_files=midi_files,
        render_options=render_options
    )
