"""Data persistence utilities for experiments."""

import json
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Protocol


class DataPersistence(Protocol):
    """Protocol for persisting experiment data."""

    def save_json(self, data: Dict, file_path: Path) -> None:
        """Save data as JSON."""
        ...

    def load_json(self, file_path: Path) -> Optional[Dict]:
        """Load data from JSON."""
        ...

    def append_csv_row(self, file_path: Path, headers: List[str], row: Dict[str, Any]) -> None:
        """Append row to CSV file."""
        ...


class StandardDataPersistence:
    """Standard JSON and CSV persistence implementation."""

    def save_json(self, data: Dict, file_path: Path) -> None:
        """Save data as JSON."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_json(self, file_path: Path) -> Optional[Dict]:
        """Load data from JSON."""
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def append_csv_row(self, file_path: Path, headers: List[str], row: Dict[str, Any]) -> None:
        """Append row to CSV file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if file exists and has headers
        file_exists = file_path.exists()

        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)

            # Write headers if file is new
            if not file_exists:
                writer.writeheader()

            writer.writerow(row)


class MockDataPersistence:
    """Mock persistence for testing."""

    def __init__(self):
        self.saved_data = {}
        self.csv_rows = []

    def save_json(self, data: Dict, file_path: Path) -> None:
        """Mock JSON save."""
        self.saved_data[str(file_path)] = data

    def load_json(self, file_path: Path) -> Optional[Dict]:
        """Mock JSON load."""
        return self.saved_data.get(str(file_path))

    def append_csv_row(self, file_path: Path, headers: List[str], row: Dict[str, Any]) -> None:
        """Mock CSV append."""
        self.csv_rows.append((str(file_path), headers, row))


class FitnessLogger:
    """Specialized logger for fitness data."""

    def __init__(self, persistence: DataPersistence):
        self.persistence = persistence
        self.headers = ['generation', 'individual', 'fitness', 'octave', 'fine', 'frequency_ratio']

    def log_generation_fitness(
        self,
        file_path: Path,
        generation: int,
        individual_fitness: List[Tuple[int, float, Dict]]
    ) -> None:
        """Log fitness data for a generation."""
        for individual_id, fitness, solution_data in individual_fitness:
            row = {
                'generation': generation,
                'individual': individual_id,
                'fitness': fitness,
                'octave': solution_data.get('octave', 0.0),
                'fine': solution_data.get('fine', 0.0),
                'frequency_ratio': solution_data.get('frequency_ratio', 1.0)
            }

            self.persistence.append_csv_row(file_path, self.headers, row)


class ExperimentDataManager:
    """Manages experiment configuration and metadata."""

    def __init__(self, persistence: DataPersistence):
        self.persistence = persistence

    def save_experiment_config(self, config_path: Path, config: Dict[str, Any]) -> None:
        """Save experiment configuration."""
        self.persistence.save_json(config, config_path)

    def load_experiment_config(self, config_path: Path) -> Optional[Dict[str, Any]]:
        """Load experiment configuration."""
        return self.persistence.load_json(config_path)

    def save_target_features(self, features_path: Path, features: Dict[str, Any]) -> None:
        """Save target audio features."""
        self.persistence.save_json(features, features_path)

    def load_target_features(self, features_path: Path) -> Optional[Dict[str, Any]]:
        """Load target audio features."""
        return self.persistence.load_json(features_path)

    def save_generation_stats(self, stats_path: Path, stats: Dict[str, Any]) -> None:
        """Save generation statistics."""
        self.persistence.save_json(stats, stats_path)

    def load_generation_stats(self, stats_path: Path) -> Optional[Dict[str, Any]]:
        """Load generation statistics."""
        return self.persistence.load_json(stats_path)
