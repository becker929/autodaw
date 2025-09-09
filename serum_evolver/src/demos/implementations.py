"""Concrete implementations of demo protocols."""

from pathlib import Path
from typing import Any

from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.termination import get_termination

from .demo_runner import ProjectValidator, OptimizationProblemFactory, GAConfigFactory
from ..genetics.jsi_problems import JSIAudioOptimizationProblem, MultiTargetJSIOptimizationProblem


class FileSystemProjectValidator:
    """Validates REAPER projects by checking filesystem."""

    def validate(self, path: Path) -> bool:
        """Check if REAPER project directory exists."""
        return path.exists() and path.is_dir()


class StandardOptimizationProblemFactory:
    """Creates standard optimization problems."""

    def create_jsi_problem(self, reaper_project_path: Path, **kwargs) -> JSIAudioOptimizationProblem:
        """Create a JSI audio optimization problem."""
        return JSIAudioOptimizationProblem(
            reaper_project_path=reaper_project_path,
            **kwargs
        )

    def create_multi_target_problem(self, reaper_project_path: Path, **kwargs) -> MultiTargetJSIOptimizationProblem:
        """Create a multi-target JSI optimization problem."""
        return MultiTargetJSIOptimizationProblem(
            reaper_project_path=reaper_project_path,
            **kwargs
        )


class StandardGAConfigFactory:
    """Creates standard GA configurations."""

    def create_algorithm(self, population_size: int) -> GA:
        """Create a configured GA algorithm."""
        return GA(
            pop_size=population_size,
            sampling=FloatRandomSampling(),
            crossover=SBX(prob=0.9, eta=15),
            mutation=PM(prob=0.1, eta=20),
            eliminate_duplicates=True
        )

    def create_termination(self, n_generations: int) -> Any:
        """Create termination criteria."""
        return get_termination("n_gen", n_generations)


class MockProjectValidator:
    """Mock validator for testing that always passes."""

    def validate(self, path: Path) -> bool:
        """Always return True for testing."""
        return True


class MockOptimizationProblemFactory:
    """Mock factory for testing."""

    def __init__(self, mock_problem=None):
        self.mock_problem = mock_problem

    def create_jsi_problem(self, reaper_project_path: Path, **kwargs) -> Any:
        """Return mock problem."""
        return self.mock_problem

    def create_multi_target_problem(self, reaper_project_path: Path, **kwargs) -> Any:
        """Return mock problem."""
        return self.mock_problem


class MockGAConfigFactory:
    """Mock GA factory for testing."""

    def __init__(self, mock_algorithm=None, mock_termination=None):
        self.mock_algorithm = mock_algorithm
        self.mock_termination = mock_termination

    def create_algorithm(self, population_size: int) -> Any:
        """Return mock algorithm."""
        return self.mock_algorithm

    def create_termination(self, n_generations: int) -> Any:
        """Return mock termination."""
        return self.mock_termination
