"""
Custom genetic algorithm problem for frequency optimization using REAPER.
"""

import numpy as np
from pymoo.core.problem import Problem
from typing import List, Optional
from pathlib import Path

from .genetics import Solution
from .reaper_integration import ReaperGAIntegration


class FrequencyOptimizationProblem(Problem):
    """Custom GA problem for optimizing frequency parameters through REAPER"""

    def __init__(
        self,
        reaper_project_path: Path,
        target_audio_path: Optional[Path] = None,
        session_name_prefix: str = "ga_frequency_opt"
    ):
        """Initialize the optimization problem"""
        # Define problem dimensions and bounds
        # 2 variables: octave [-2, 2], fine [-1, 1]
        n_var = 2
        n_obj = 1  # Single objective: minimize frequency distance
        xl = np.array([-2.0, -1.0])  # Lower bounds
        xu = np.array([2.0, 1.0])    # Upper bounds

        super().__init__(n_var=n_var, n_obj=n_obj, xl=xl, xu=xu)

        # Initialize REAPER integration
        self.reaper_integration = ReaperGAIntegration(
            reaper_project_path=reaper_project_path,
            target_audio_path=target_audio_path,
            session_name_prefix=session_name_prefix
        )

        self.evaluation_count = 0

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate the population using REAPER audio rendering and analysis"""
        # Convert numpy array population to Solution objects
        solutions = []
        for individual in x:
            octave, fine = individual
            solution = Solution(octave=octave, fine=fine)
            solutions.append(solution)

        # Evaluate population fitness through REAPER integration
        fitness_values = self.reaper_integration.evaluate_population_fitness(solutions)

        # Update evaluation counter
        self.evaluation_count += len(solutions)

        # Clean up old renders periodically to save disk space
        if self.reaper_integration.generation_counter % 5 == 0:
            self.reaper_integration.cleanup_old_renders(keep_generations=2)

        # Convert to numpy array for pymoo
        out["F"] = np.array(fitness_values).reshape(-1, 1)

    def get_best_solution_info(self, result) -> dict:
        """Extract information about the best solution found"""
        if hasattr(result, 'X') and hasattr(result, 'F'):
            best_x = result.X
            best_fitness = result.F[0] if hasattr(result.F, '__len__') else result.F

            best_solution = Solution(octave=best_x[0], fine=best_x[1])

            return {
                'solution': best_solution,
                'fitness': best_fitness,
                'frequency_ratio': best_solution.calculate_frequency_ratio(),
                'evaluations': self.evaluation_count,
                'generations': self.reaper_integration.generation_counter
            }

        return {}


class TargetFrequencyProblem(FrequencyOptimizationProblem):
    """Specialized problem for matching a specific target frequency"""

    def __init__(
        self,
        reaper_project_path: Path,
        target_frequency_ratio: float,
        reference_audio_path: Optional[Path] = None,
        session_name_prefix: str = "ga_target_freq"
    ):
        """Initialize with target frequency ratio"""
        super().__init__(
            reaper_project_path=reaper_project_path,
            target_audio_path=reference_audio_path,
            session_name_prefix=session_name_prefix
        )

        self.target_frequency_ratio = target_frequency_ratio

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate population with additional target frequency penalty"""
        # First, get the standard audio-based fitness
        super()._evaluate(x, out, *args, **kwargs)

        # Add penalty based on frequency ratio distance
        frequency_penalties = []
        for individual in x:
            octave, fine = individual
            solution = Solution(octave=octave, fine=fine)
            frequency_ratio = solution.calculate_frequency_ratio()

            # Calculate penalty based on distance from target frequency
            frequency_penalty = abs(frequency_ratio - self.target_frequency_ratio) * 10.0
            frequency_penalties.append(frequency_penalty)

        # Combine audio fitness with frequency penalty
        audio_fitness = out["F"].flatten()
        combined_fitness = audio_fitness + np.array(frequency_penalties)

        out["F"] = combined_fitness.reshape(-1, 1)


class MultiObjectiveFrequencyProblem(Problem):
    """Multi-objective version optimizing both frequency accuracy and audio quality"""

    def __init__(
        self,
        reaper_project_path: Path,
        target_frequency_ratio: float,
        target_audio_path: Optional[Path] = None,
        session_name_prefix: str = "ga_multi_freq"
    ):
        """Initialize multi-objective problem"""
        # 2 variables, 2 objectives
        n_var = 2
        n_obj = 2  # Objective 1: frequency accuracy, Objective 2: audio quality
        xl = np.array([-2.0, -1.0])
        xu = np.array([2.0, 1.0])

        super().__init__(n_var=n_var, n_obj=n_obj, xl=xl, xu=xu)

        self.target_frequency_ratio = target_frequency_ratio
        self.reaper_integration = ReaperGAIntegration(
            reaper_project_path=reaper_project_path,
            target_audio_path=target_audio_path,
            session_name_prefix=session_name_prefix
        )

        self.evaluation_count = 0

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate population for both objectives"""
        # Convert to solutions
        solutions = []
        for individual in x:
            octave, fine = individual
            solution = Solution(octave=octave, fine=fine)
            solutions.append(solution)

        # Get audio quality fitness
        audio_fitness = self.reaper_integration.evaluate_population_fitness(solutions)

        # Calculate frequency accuracy objective
        frequency_objectives = []
        for solution in solutions:
            frequency_ratio = solution.calculate_frequency_ratio()
            frequency_error = abs(frequency_ratio - self.target_frequency_ratio)
            frequency_objectives.append(frequency_error)

        self.evaluation_count += len(solutions)

        # Periodic cleanup
        if self.reaper_integration.generation_counter % 5 == 0:
            self.reaper_integration.cleanup_old_renders(keep_generations=2)

        # Set objectives: minimize both frequency error and audio distance
        objectives = np.column_stack([frequency_objectives, audio_fitness])
        out["F"] = objectives
