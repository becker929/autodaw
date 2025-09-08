"""
Genetic algorithm components for frequency optimization.
Includes Solution class (genome) and mapping to RenderConfig (phenotype).
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Any
from .config import RenderConfig, create_basic_serum_render_config


@dataclass
class Solution:
    """Genetic algorithm solution representing Serum parameters"""
    octave: float
    fine: float

    def __init__(self, octave: float, fine: float):
        """Initialize solution with parameter bounds checking"""
        # Clamp values to valid ranges
        # Octave: typically -2 to +2 (mapped to 0.0-1.0 range in Serum)
        # Fine: typically -1 to +1 (mapped to 0.0-1.0 range in Serum)
        self.octave = max(-2.0, min(2.0, octave))
        self.fine = max(-1.0, min(1.0, fine))

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for GA operations"""
        return np.array([self.octave, self.fine])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Solution':
        """Create solution from numpy array"""
        return cls(octave=arr[0], fine=arr[1])

    def calculate_frequency_ratio(self) -> float:
        """Calculate approximate frequency ratio from parameters"""
        # Octave contributes 2^octave frequency ratio
        # Fine contributes small frequency adjustment (approximately ±100 cents = ±1 semitone)
        octave_ratio = 2.0 ** self.octave
        fine_ratio = 2.0 ** (self.fine / 12.0)  # Convert fine to semitones
        return octave_ratio * fine_ratio

    def __str__(self) -> str:
        """String representation"""
        return f"Solution(octave={self.octave:.4f}, fine={self.fine:.4f})"


class GenomeToPhenotypeMapper:
    """Maps genetic solutions to REAPER render configurations"""

    def __init__(self, midi_file: str = "test_melody.mid"):
        """Initialize mapper with default MIDI file"""
        self.midi_file = midi_file

    def solution_to_serum_params(self, solution: Solution) -> Dict[str, float]:
        """Convert solution parameters to Serum VST parameter values (0.0-1.0 range)"""
        # Map octave from [-2, 2] to [0, 1] range
        octave_normalized = (solution.octave + 2.0) / 4.0
        octave_normalized = max(0.0, min(1.0, octave_normalized))

        # Map fine from [-1, 1] to [0, 1] range
        fine_normalized = (solution.fine + 1.0) / 2.0
        fine_normalized = max(0.0, min(1.0, fine_normalized))

        return {
            "A Octave": octave_normalized,
            "A Fine": fine_normalized
        }

    def solution_to_render_config(self, solution: Solution, render_id: str) -> RenderConfig:
        """Convert genetic solution to REAPER render configuration"""
        serum_params = self.solution_to_serum_params(solution)

        return create_basic_serum_render_config(
            render_id=render_id,
            octave_value=serum_params["A Octave"],
            fine_value=serum_params["A Fine"],
            midi_file=self.midi_file
        )

    def population_to_render_configs(
        self,
        population: List[Solution],
        session_name: str = "ga_optimization"
    ) -> List[RenderConfig]:
        """Convert entire population to render configurations"""
        render_configs = []

        for i, solution in enumerate(population):
            render_id = f"{session_name}_individual_{i:03d}"
            render_config = self.solution_to_render_config(solution, render_id)
            render_configs.append(render_config)

        return render_configs


class PopulationGenerator:
    """Generate initial populations for genetic algorithm"""

    @staticmethod
    def random_population(size: int, seed: int = None) -> List[Solution]:
        """Generate random population within parameter bounds"""
        if seed is not None:
            np.random.seed(seed)

        population = []
        for _ in range(size):
            octave = np.random.uniform(-2.0, 2.0)
            fine = np.random.uniform(-1.0, 1.0)
            population.append(Solution(octave, fine))

        return population

    @staticmethod
    def targeted_population(
        size: int,
        target_octave: float = 0.0,
        target_fine: float = 0.0,
        variance: float = 0.5,
        seed: int = None
    ) -> List[Solution]:
        """Generate population around target values with specified variance"""
        if seed is not None:
            np.random.seed(seed)

        population = []
        for _ in range(size):
            octave = np.random.normal(target_octave, variance)
            fine = np.random.normal(target_fine, variance * 0.5)  # Less variance for fine tuning
            population.append(Solution(octave, fine))

        return population

    @staticmethod
    def diverse_population(size: int, seed: int = None) -> List[Solution]:
        """Generate diverse population covering parameter space"""
        if seed is not None:
            np.random.seed(seed)

        population = []

        # Add corner cases
        corners = [
            Solution(-2.0, -1.0),  # Low octave, low fine
            Solution(-2.0, 1.0),   # Low octave, high fine
            Solution(2.0, -1.0),   # High octave, low fine
            Solution(2.0, 1.0),    # High octave, high fine
            Solution(0.0, 0.0),    # Center
        ]

        for corner in corners[:min(size, len(corners))]:
            population.append(corner)

        # Fill remaining with random
        remaining = size - len(population)
        if remaining > 0:
            random_pop = PopulationGenerator.random_population(remaining, seed)
            population.extend(random_pop)

        return population[:size]


def calculate_parameter_distance(solution1: Solution, solution2: Solution) -> float:
    """Calculate Euclidean distance between two solutions in parameter space"""
    diff_octave = solution1.octave - solution2.octave
    diff_fine = solution1.fine - solution2.fine

    # Weight octave changes more heavily since they have larger frequency impact
    octave_weight = 4.0  # Octave changes are more significant
    fine_weight = 1.0

    weighted_distance = np.sqrt(
        (octave_weight * diff_octave) ** 2 +
        (fine_weight * diff_fine) ** 2
    )

    return weighted_distance
