"""Demo runner with dependency injection for testing and flexibility."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Protocol
import numpy as np

from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize
from pymoo.termination import get_termination


class ProjectValidator(Protocol):
    """Protocol for validating REAPER projects."""

    def validate(self, path: Path) -> bool:
        """Validate that a REAPER project exists and is accessible."""
        ...


class OptimizationProblemFactory(Protocol):
    """Protocol for creating optimization problems."""

    def create_jsi_problem(self, reaper_project_path: Path, **kwargs) -> Any:
        """Create a JSI audio optimization problem."""
        ...

    def create_multi_target_problem(self, reaper_project_path: Path, **kwargs) -> Any:
        """Create a multi-target JSI optimization problem."""
        ...


class GAConfigFactory(Protocol):
    """Protocol for creating GA configurations."""

    def create_algorithm(self, population_size: int) -> GA:
        """Create a configured GA algorithm."""
        ...

    def create_termination(self, n_generations: int) -> Any:
        """Create termination criteria."""
        ...


class DemoRunner:
    """Runs optimization demos with injected dependencies."""

    def __init__(
        self,
        validator: ProjectValidator,
        problem_factory: OptimizationProblemFactory,
        ga_factory: GAConfigFactory
    ):
        self.validator = validator
        self.problem_factory = problem_factory
        self.ga_factory = ga_factory

    def run_jsi_optimization(
        self,
        reaper_project_path: Path,
        target_frequency: float = 440.0,
        target_audio_path: Optional[Path] = None,
        n_generations: int = 10,
        population_size: int = 8,
        oracle_noise_level: float = 0.05,
        show_live_ranking: bool = True
    ) -> Dict[str, Any]:
        """Run JSI + Audio Oracle optimization demo."""
        if not self.validator.validate(reaper_project_path):
            raise FileNotFoundError(f"REAPER project not found: {reaper_project_path}")

        # Create problem
        problem = self.problem_factory.create_jsi_problem(
            reaper_project_path=reaper_project_path,
            target_frequency=target_frequency,
            target_audio_path=target_audio_path,
            oracle_noise_level=oracle_noise_level,
            show_live_ranking=show_live_ranking
        )

        # Create GA
        algorithm = self.ga_factory.create_algorithm(population_size)
        termination = self.ga_factory.create_termination(n_generations)

        # Run optimization
        result = minimize(problem, algorithm, termination, verbose=False)

        # Get results
        return problem.get_best_solution_info()

    def run_multi_target_optimization(
        self,
        reaper_project_path: Path,
        target_frequencies: list = None,
        n_generations: int = 20,
        population_size: int = 8,
        oracle_noise_level: float = 0.05
    ) -> Dict[str, Any]:
        """Run multi-target JSI optimization demo."""
        if not self.validator.validate(reaper_project_path):
            raise FileNotFoundError(f"REAPER project not found: {reaper_project_path}")

        if target_frequencies is None:
            target_frequencies = [220.0, 440.0, 880.0]

        # Create problem
        problem = self.problem_factory.create_multi_target_problem(
            reaper_project_path=reaper_project_path,
            target_frequencies=target_frequencies,
            session_name_prefix="multi_jsi_demo",
            oracle_noise_level=oracle_noise_level,
            show_live_ranking=True
        )

        # Create GA
        algorithm = self.ga_factory.create_algorithm(population_size)
        termination = self.ga_factory.create_termination(n_generations)

        # Run optimization
        result = minimize(problem, algorithm, termination, verbose=False)

        # Get results
        return problem.get_best_solution_info()


class DemoResultsFormatter:
    """Formats and displays demo results."""

    @staticmethod
    def format_jsi_results(results: Dict[str, Any]) -> str:
        """Format JSI optimization results."""
        lines = [
            f"Best fitness: {results.get('best_fitness', 0):.3f}",
            f"Best solution: {results.get('best_solution', [])}",
            f"Generations: {results.get('generation_count', 0)}",
            f"Comparisons: {results.get('comparison_count', 0)}"
        ]
        return "\n".join(lines)

    @staticmethod
    def format_multi_target_results(results: Dict[str, Any]) -> str:
        """Format multi-target optimization results."""
        lines = [
            f"Best fitness: {results.get('best_fitness', 0):.3f}",
            f"Target frequencies: {results.get('target_frequencies', [])}",
            f"Generations: {results.get('generation_count', 0)}",
            f"Comparisons: {results.get('comparison_count', 0)}"
        ]
        return "\n".join(lines)

    @staticmethod
    def print_demo_header(title: str):
        """Print a formatted demo header."""
        print(f"=== {title} ===")

    @staticmethod
    def print_suite_header():
        """Print the full demo suite header."""
        print("=" * 80)
        print("GA + JSI + AUDIO ORACLE INTEGRATION - FULL DEMO SUITE")
        print("=" * 80)

    @staticmethod
    def print_suite_footer():
        """Print the full demo suite footer."""
        print("\n" + "=" * 80)
        print("DEMO SUITE COMPLETE")
        print("=" * 80)
