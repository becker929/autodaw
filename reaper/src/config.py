"""Configuration management for the automation system."""

from pathlib import Path
from typing import Dict, Any, Optional
import json
from dataclasses import dataclass, asdict


@dataclass
class AutomationConfig:
    """Configuration for automation sessions."""
    workflow_mode: str = "full"
    target_parameter: str = "octave"
    parameter_value: float = 0.0
    session_id: str = "1"
    output_dir: Path = Path("/Users/anthonybecker/Desktop")

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
    beacon_file: Path = Path("/Users/anthonybecker/Desktop/reaper_automation_beacon.txt")
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
