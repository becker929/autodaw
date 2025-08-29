"""Interface for communicating with Lua ReaScripts."""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from config import AutomationConfig


@dataclass
class BeaconData:
    """Structured beacon data for Lua-Python communication."""
    timestamp: str
    status: str  # 'STARTED', 'RUNNING', 'COMPLETED', 'ERROR'
    script: str
    message: str
    session_id: str = ""
    progress: float = 0.0  # 0.0 to 1.0
    data: Dict[str, Any] = None

    @classmethod
    def from_beacon_file(cls, beacon_path: Path) -> Optional['BeaconData']:
        """Load beacon data from file."""
        if not beacon_path.exists():
            return None

        try:
            with open(beacon_path, 'r') as f:
                content = f.read().strip()

            # Parse key=value lines
            data = {}
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()

            # Handle optional JSON data
            extra_data = {}
            if 'data' in data:
                try:
                    extra_data = json.loads(data['data'])
                except json.JSONDecodeError:
                    pass

            return cls(
                timestamp=data.get('timestamp', ''),
                status=data.get('status', 'UNKNOWN'),
                script=data.get('script', 'unknown'),
                message=data.get('message', ''),
                session_id=data.get('session_id', ''),
                progress=float(data.get('progress', 0.0)),
                data=extra_data
            )

        except Exception as e:
            print(f"Error reading beacon file: {e}")
            return None

    def save_to_beacon_file(self, beacon_path: Path) -> None:
        """Save beacon data to file."""
        beacon_path.parent.mkdir(parents=True, exist_ok=True)

        with open(beacon_path, 'w') as f:
            f.write(f"timestamp={self.timestamp}\n")
            f.write(f"status={self.status}\n")
            f.write(f"script={self.script}\n")
            f.write(f"message={self.message}\n")
            f.write(f"session_id={self.session_id}\n")
            f.write(f"progress={self.progress}\n")

            if self.data:
                f.write(f"data={json.dumps(self.data)}\n")


class LuaScriptInterface:
    """Interface for executing and communicating with Lua scripts."""

    def __init__(self, beacon_file: Path):
        self.beacon_file = beacon_file

    def clear_beacon_file(self) -> None:
        """Remove beacon file if it exists."""
        try:
            if self.beacon_file.exists():
                self.beacon_file.unlink()
        except Exception as e:
            print(f"Warning: Could not clear beacon file: {e}")

    def read_beacon_data(self) -> Optional[BeaconData]:
        """Read structured beacon data."""
        return BeaconData.from_beacon_file(self.beacon_file)

    def wait_for_completion(self, timeout_seconds: int = 60) -> tuple[bool, Optional[BeaconData]]:
        """Monitor beacon file until completion or timeout."""
        print("Monitoring automation progress via beacon file...")

        start_time = time.time()
        last_status = None
        last_beacon_data = None

        while time.time() - start_time < timeout_seconds:
            beacon_data = self.read_beacon_data()

            if beacon_data:
                last_beacon_data = beacon_data

                # Print status updates
                if beacon_data.status != last_status:
                    print(f"Status: {beacon_data.status} - {beacon_data.script}")
                    if beacon_data.message:
                        print(f"  Message: {beacon_data.message}")
                    if beacon_data.progress > 0:
                        print(f"  Progress: {beacon_data.progress:.1%}")
                    last_status = beacon_data.status

                # Check for completion or error
                if beacon_data.status == 'COMPLETED':
                    print("✓ Automation completed successfully!")
                    return True, beacon_data
                elif beacon_data.status == 'ERROR':
                    print(f"✗ Automation failed: {beacon_data.message}")
                    return False, beacon_data

            # Wait before checking again
            time.sleep(1)

        print(f"⚠ Timeout after {timeout_seconds} seconds - automation may still be running")
        return False, last_beacon_data

    def create_config_for_script(self, config: AutomationConfig, script_data: Dict[str, Any] = None) -> None:
        """Create configuration file for Lua scripts to read."""
        config_path = self.beacon_file.parent / "automation_config.txt"

        # Merge script-specific data
        if script_data:
            config_dict = config.to_dict()
            config_dict.update(script_data)
        else:
            config_dict = config.to_dict()

        # Write config file
        with open(config_path, 'w') as f:
            for key, value in config_dict.items():
                f.write(f"{key}={value}\n")


@dataclass
class ParameterInfo:
    """Information about a VST parameter."""
    index: int
    name: str
    current_value: float
    current_formatted: str
    min_normalized: float = 0.0
    max_normalized: float = 1.0
    min_formatted: str = ""
    max_formatted: str = ""


class ParameterDiscoveryInterface:
    """Interface for discovering VST parameters via Lua scripts."""

    def __init__(self, lua_interface: LuaScriptInterface):
        self.lua_interface = lua_interface

    def discover_parameters(self, fx_index: int = 0) -> List[ParameterInfo]:
        """Discover all parameters for a VST."""
        # This would be implemented by creating a specialized Lua script
        # that discovers parameter ranges and returns structured data

        # For now, return mock data - this would be replaced with actual
        # Lua script execution and JSON parsing
        return [
            ParameterInfo(
                index=0,
                name="Octave",
                current_value=0.5,
                current_formatted="0 oct",
                min_formatted="-4 oct",
                max_formatted="+4 oct"
            ),
            ParameterInfo(
                index=1,
                name="Filter Cutoff",
                current_value=0.7,
                current_formatted="70%",
                min_formatted="0%",
                max_formatted="100%"
            )
        ]

    def get_parameter_ranges(self, parameters: List[str]) -> Dict[str, ParameterInfo]:
        """Get range information for specific parameters."""
        all_params = self.discover_parameters()

        result = {}
        for param in all_params:
            if param.name.lower() in [p.lower() for p in parameters]:
                result[param.name] = param

        return result
