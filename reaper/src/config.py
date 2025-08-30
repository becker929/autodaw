"""Configuration management for the automation system."""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import json
import logging
import logging.handlers
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid


@dataclass
class AutomationConfig:
    """Configuration for automation sessions."""
    workflow_mode: str = "full"
    target_parameter: str = "octave"
    parameter_value: float = 0.0
    session_id: str = "1"
    output_dir: Path = Path("./sessions/runs")

    @classmethod
    def from_file(cls, config_path: Path) -> 'AutomationConfig':
        """Load configuration from file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        data = {}
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()

        # Convert string paths to Path objects
        if 'output_dir' in data:
            data['output_dir'] = Path(data['output_dir'])

        # Convert numeric strings
        if 'parameter_value' in data:
            data['parameter_value'] = float(data['parameter_value'])

        return cls(**data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to file."""
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            f.write(f"workflow_mode={self.workflow_mode}\n")
            f.write(f"target_parameter={self.target_parameter}\n")
            f.write(f"parameter_value={self.parameter_value}\n")
            f.write(f"session_id={self.session_id}\n")
            f.write(f"output_dir={self.output_dir}\n")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with Path objects as strings."""
        data = asdict(self)
        data['output_dir'] = str(self.output_dir)
        return data


@dataclass
class SystemConfig:
    """System-wide configuration."""
    reaper_path: Path = Path("/Applications/REAPER.app/Contents/MacOS/REAPER")
    startup_script: Path = Path("/Users/anthonybecker/Library/Application Support/REAPER/Scripts/__startup.lua")
    project_dir: Path = Path.cwd()
    beacon_file: Path = Path("./reaper_automation_beacon.txt")
    config_file: Path = Path("automation_config.txt")

    def validate(self) -> None:
        """Validate system configuration."""
        if not self.reaper_path.exists():
            raise FileNotFoundError(f"REAPER not found at {self.reaper_path}")

        if not self.startup_script.exists():
            raise FileNotFoundError(f"Startup script not found at {self.startup_script}")


@dataclass
class ParameterSpec:
    """Specification for a parameter to sweep."""
    name: str
    min_value: float
    max_value: float
    steps: int

    def __post_init__(self):
        if self.steps < 2:
            raise ValueError("Steps must be at least 2")
        if self.min_value >= self.max_value:
            raise ValueError("min_value must be less than max_value")


@dataclass
class SweepConfiguration:
    """Configuration for parameter sweeps."""
    parameters: list[ParameterSpec]
    strategy: str = 'grid'  # 'grid', 'random', 'adaptive'
    max_combinations: int = 1000

    def __post_init__(self):
        if self.strategy not in ['grid', 'random', 'adaptive']:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        if not self.parameters:
            raise ValueError("At least one parameter must be specified")


# Simplified logging system for Python stdout and file output only


# Enhanced configuration system with JSON-based session management
@dataclass
class MIDIConfig:
    """Configuration for MIDI files."""
    midi_files: List[str] = field(default_factory=list)
    track_index: int = 0
    clear_existing: bool = True

    def add_midi_file(self, file_path: str):
        """Add a MIDI file to the configuration."""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"MIDI file not found: {file_path}")
        self.midi_files.append(file_path)

    def validate(self):
        """Validate MIDI configuration."""
        for midi_file in self.midi_files:
            if not Path(midi_file).exists():
                raise FileNotFoundError(f"MIDI file not found: {midi_file}")


@dataclass
class ParameterConfig:
    """Configuration for a single parameter - raw value only."""
    name: str
    value: float

    def validate(self):
        """Validate parameter configuration."""
        # Basic validation - just ensure it's a number
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"Parameter {self.name} value must be a number, got {type(self.value)}")


@dataclass
class RenderConfig:
    """Configuration for a single render operation."""
    name: str
    parameters: Dict[str, ParameterConfig] = field(default_factory=dict)
    midi_config: Optional[MIDIConfig] = None
    output_filename: Optional[str] = None
    render_length: float = 30.0  # seconds
    render_quality: str = "high"  # "draft", "medium", "high"

    def add_parameter(self, name: str, value: float):
        """Add a parameter configuration with raw value."""
        self.parameters[name] = ParameterConfig(name, value)

    def set_midi_config(self, midi_config: MIDIConfig):
        """Set MIDI configuration for this render."""
        self.midi_config = midi_config

    def validate(self):
        """Validate render configuration."""
        for param in self.parameters.values():
            param.validate()

        if self.render_length <= 0:
            raise ValueError("Render length must be positive")

        if self.render_quality not in ["draft", "medium", "high"]:
            raise ValueError(f"Invalid render quality: {self.render_quality}")


@dataclass
class SessionConfig:
    """Configuration for an entire automation session."""
    session_name: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    project_file: Optional[str] = None
    renders: List[RenderConfig] = field(default_factory=list)
    global_midi_config: Optional[MIDIConfig] = None
    output_directory: str = "./sessions/runs"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_session_run_dir(self) -> str:
        """Get the directory name for this specific session run."""
        timestamp = datetime.fromisoformat(self.created_at).strftime('%Y%m%d_%H%M%S')
        return f"{self.session_name}_{timestamp}"

    def add_render(self, render_config: RenderConfig):
        """Add a render configuration to the session."""
        self.renders.append(render_config)

    def set_global_midi(self, midi_config: MIDIConfig):
        """Set global MIDI configuration for all renders."""
        self.global_midi_config = midi_config

    def validate(self):
        """Validate session configuration."""
        if not self.session_name:
            raise ValueError("Session name is required")

        if self.project_file and not Path(self.project_file).exists():
            raise ValueError(f"Project file not found: {self.project_file}")

        for render in self.renders:
            render.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionConfig':
        """Create from dictionary (JSON deserialization)."""
        # Convert renders
        renders = []
        for render_data in data.get('renders', []):
            # Convert parameters
            parameters = {}
            for param_name, param_data in render_data.get('parameters', {}).items():
                # Handle both old format (with min/max) and new format (raw values)
                if isinstance(param_data, dict):
                    parameters[param_name] = ParameterConfig(
                        name=param_data['name'],
                        value=param_data['value']
                    )
                else:
                    # Simple value
                    parameters[param_name] = ParameterConfig(param_name, param_data)

            # Convert MIDI config
            midi_config = None
            if render_data.get('midi_config'):
                midi_config = MIDIConfig(**render_data['midi_config'])

            render = RenderConfig(
                name=render_data['name'],
                parameters=parameters,
                midi_config=midi_config,
                output_filename=render_data.get('output_filename'),
                render_length=render_data.get('render_length', 30.0),
                render_quality=render_data.get('render_quality', 'high')
            )
            renders.append(render)

        # Convert global MIDI config
        global_midi_config = None
        if data.get('global_midi_config'):
            global_midi_config = MIDIConfig(**data['global_midi_config'])

        return cls(
            session_name=data['session_name'],
            session_id=data.get('session_id', str(uuid.uuid4())[:8]),
            project_file=data.get('project_file'),
            renders=renders,
            global_midi_config=global_midi_config,
            output_directory=data.get('output_directory', './outputs'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            metadata=data.get('metadata', {})
        )


class ConfigManager:
    """Manages session configurations with JSON storage."""

    def __init__(self, base_config_dir: Path = None):
        self.base_config_dir = base_config_dir or Path("./sessions/configs")
        self.base_config_dir.mkdir(parents=True, exist_ok=True)

    def save_session_config(self, session_config: SessionConfig) -> Path:
        """Save session configuration to JSON file."""
        session_config.validate()

        config_file = self.base_config_dir / f"{session_config.session_name}.json"

        with open(config_file, 'w') as f:
            json.dump(session_config.to_dict(), f, indent=2)

        return config_file

    def load_session_config(self, session_name: str) -> SessionConfig:
        """Load session configuration from JSON file."""
        config_file = self.base_config_dir / f"{session_name}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Session config not found: {config_file}")

        with open(config_file, 'r') as f:
            data = json.load(f)

        return SessionConfig.from_dict(data)

    def list_session_configs(self) -> List[str]:
        """List all available session configuration names."""
        return [f.stem for f in self.base_config_dir.glob("*.json")]

    def delete_session_config(self, session_name: str) -> bool:
        """Delete a session configuration file."""
        config_file = self.base_config_dir / f"{session_name}.json"

        if config_file.exists():
            config_file.unlink()
            return True
        return False

    def create_template_config(self, session_name: str,
                             project_file: str = None) -> SessionConfig:
        """Create a template session configuration."""
        config = SessionConfig(
            session_name=session_name,
            project_file=project_file
        )

        # Add default MIDI configuration (empty - user should add actual MIDI files)
        default_midi = MIDIConfig()
        config.set_global_midi(default_midi)

        # Add default render configurations with raw values
        render1 = RenderConfig(name="baseline")
        render1.add_parameter("octave", 0.0)
        render1.add_parameter("filter_cutoff", 0.5)

        render2 = RenderConfig(name="octave_up")
        render2.add_parameter("octave", 1.0)
        render2.add_parameter("filter_cutoff", 0.8)

        config.add_render(render1)
        config.add_render(render2)

        return config


# Serum parameter definitions with comprehensive range data
SERUM_PARAMETERS = {
    # Oscillator parameters
    "osc_a_octave": {"min": -3.0, "max": 3.0, "default": 0.0},
    "osc_a_semi": {"min": -12.0, "max": 12.0, "default": 0.0},
    "osc_a_fine": {"min": -100.0, "max": 100.0, "default": 0.0},
    "osc_a_phase": {"min": 0.0, "max": 360.0, "default": 0.0},
    "osc_a_pan": {"min": -1.0, "max": 1.0, "default": 0.0},
    "osc_a_level": {"min": 0.0, "max": 1.0, "default": 1.0},

    "osc_b_octave": {"min": -3.0, "max": 3.0, "default": 0.0},
    "osc_b_semi": {"min": -12.0, "max": 12.0, "default": 0.0},
    "osc_b_fine": {"min": -100.0, "max": 100.0, "default": 0.0},
    "osc_b_phase": {"min": 0.0, "max": 360.0, "default": 0.0},
    "osc_b_pan": {"min": -1.0, "max": 1.0, "default": 0.0},
    "osc_b_level": {"min": 0.0, "max": 1.0, "default": 1.0},

    # Filter parameters
    "filter_cutoff": {"min": 0.0, "max": 1.0, "default": 1.0},
    "filter_resonance": {"min": 0.0, "max": 1.0, "default": 0.0},
    "filter_drive": {"min": 0.0, "max": 1.0, "default": 0.0},
    "filter_fat": {"min": 0.0, "max": 1.0, "default": 0.0},

    # Envelope parameters
    "amp_attack": {"min": 0.0, "max": 20.0, "default": 0.0},
    "amp_decay": {"min": 0.0, "max": 20.0, "default": 0.5},
    "amp_sustain": {"min": 0.0, "max": 1.0, "default": 1.0},
    "amp_release": {"min": 0.0, "max": 20.0, "default": 0.5},

    "filter_attack": {"min": 0.0, "max": 20.0, "default": 0.0},
    "filter_decay": {"min": 0.0, "max": 20.0, "default": 0.5},
    "filter_sustain": {"min": 0.0, "max": 1.0, "default": 1.0},
    "filter_release": {"min": 0.0, "max": 20.0, "default": 0.5},

    # LFO parameters
    "lfo1_rate": {"min": 0.0, "max": 20.0, "default": 1.0},
    "lfo1_amount": {"min": -1.0, "max": 1.0, "default": 0.0},
    "lfo2_rate": {"min": 0.0, "max": 20.0, "default": 1.0},
    "lfo2_amount": {"min": -1.0, "max": 1.0, "default": 0.0},

    # Effects parameters
    "chorus_rate": {"min": 0.0, "max": 20.0, "default": 1.0},
    "chorus_depth": {"min": 0.0, "max": 1.0, "default": 0.0},
    "chorus_feedback": {"min": 0.0, "max": 1.0, "default": 0.0},
    "chorus_mix": {"min": 0.0, "max": 1.0, "default": 0.0},

    "delay_time": {"min": 0.0, "max": 2.0, "default": 0.25},
    "delay_feedback": {"min": 0.0, "max": 1.0, "default": 0.0},
    "delay_mix": {"min": 0.0, "max": 1.0, "default": 0.0},

    "reverb_size": {"min": 0.0, "max": 1.0, "default": 0.5},
    "reverb_decay": {"min": 0.0, "max": 1.0, "default": 0.5},
    "reverb_mix": {"min": 0.0, "max": 1.0, "default": 0.0},
}


def create_serum_parameter_sweep(session_name: str,
                               parameters: List[str],
                               steps_per_param: int = 5) -> SessionConfig:
    """Create a parameter sweep for specified Serum parameters."""
    if not parameters:
        raise ValueError("At least one parameter must be specified")

    # Validate parameters
    for param in parameters:
        if param not in SERUM_PARAMETERS:
            raise ValueError(f"Unknown Serum parameter: {param}")

    # Build parameter specs
    param_specs = {}
    for param in parameters:
        serum_spec = SERUM_PARAMETERS[param]
        param_specs[param] = {
            'min': serum_spec['min'],
            'max': serum_spec['max'],
            'steps': steps_per_param
        }

    # Generate grid sweep
    config = SessionConfig(session_name=session_name)

    # Generate all combinations
    param_names = list(param_specs.keys())
    param_values = []

    for param_name in param_names:
        spec = param_specs[param_name]
        min_val = spec['min']
        max_val = spec['max']
        steps = spec['steps']

        if steps == 1:
            values = [min_val]
        else:
            values = [min_val + (max_val - min_val) * i / (steps - 1)
                     for i in range(steps)]
        param_values.append(values)

    # Generate cartesian product
    import itertools
    combinations = list(itertools.product(*param_values))

    # Create render config for each combination
    for i, combo in enumerate(combinations):
        render_name = f"render_{i:03d}_" + "_".join(
            f"{param_names[j]}_{combo[j]:.3f}"
            for j in range(len(param_names))
        )

        render = RenderConfig(name=render_name)
        for j, param_name in enumerate(param_names):
            render.add_parameter(param_name, combo[j])

        config.add_render(render)

    return config


def setup_session_logging(log_level: str = "DEBUG",
                          session_dir: Optional[Path] = None,
                          enable_file_logging: bool = True) -> None:
    """
    Set up logging configuration for a specific session.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        session_dir: Session directory for log files. If None, logs only to console
        enable_file_logging: Whether to enable file logging
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create detailed formatter
    detailed_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create console formatter (less verbose)
    console_formatter = logging.Formatter(
        '%(levelname)s [%(name)s]: %(message)s'
    )

    # Add file handlers if enabled and session_dir provided
    if enable_file_logging and session_dir:
        # Main application log in session directory
        log_file = session_dir / "application.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=50*1024*1024, backupCount=10
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

        # Debug-only log in session directory
        debug_file = session_dir / "debug.log"
        debug_handler = logging.handlers.RotatingFileHandler(
            debug_file, maxBytes=50*1024*1024, backupCount=5
        )
        debug_handler.setFormatter(detailed_formatter)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
        root_logger.addHandler(debug_handler)

    # Add console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)  # Less verbose for console
    root_logger.addHandler(console_handler)

    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info(f"Session logging configured: level={log_level}, session_dir={session_dir}")
    if session_dir:
        logger.debug(f"Log files: application.log, debug.log in {session_dir}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.debug(f"Logger '{name}' requested")
    return logger
