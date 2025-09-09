"""Main orchestration for GA + JSI + Audio Oracle + REAPER integration demo.

This module provides convenience functions that delegate to the refactored components.
"""

from pathlib import Path
from typing import Dict, Any, Optional

from .demo_runner import DemoRunner, DemoResultsFormatter
from .oracle_accuracy import OracleAccuracyTester
from .demo_suite import create_standard_demo_suite, run_full_demo_suite as _run_full_demo_suite
from .implementations import (
    FileSystemProjectValidator,
    StandardOptimizationProblemFactory,
    StandardGAConfigFactory
)
from .oracle_accuracy import StandardOracleFactory


def demo_jsi_audio_optimization(
    reaper_project_path: Path,
    target_frequency: float = 440.0,
    target_audio_path: Optional[Path] = None,
    n_generations: int = 10,
    population_size: int = 8,
    oracle_noise_level: float = 0.05,
    show_live_ranking: bool = True
) -> Dict[str, Any]:
    """Run JSI + Audio Oracle optimization demo.

    This is a convenience function that creates a demo runner with standard dependencies.
    """
    # Print demo header
    formatter = DemoResultsFormatter()
    formatter.print_demo_header("GA + JSI + Audio Oracle Integration Demo")

    print(f"REAPER project: {reaper_project_path}")
    print(f"Target frequency: {target_frequency} Hz")
    print(f"Target audio: {target_audio_path or 'None (using frequency)'}")
    print(f"Generations: {n_generations}, Population: {population_size}")
    print(f"Oracle noise level: {oracle_noise_level}")
    print(f"Live ranking: {show_live_ranking}")

    # Create dependencies
    validator = FileSystemProjectValidator()
    problem_factory = StandardOptimizationProblemFactory()
    ga_factory = StandardGAConfigFactory()

    # Create demo runner
    demo_runner = DemoRunner(validator, problem_factory, ga_factory)

    # Run demo
    results = demo_runner.run_jsi_optimization(
        reaper_project_path=reaper_project_path,
        target_frequency=target_frequency,
        target_audio_path=target_audio_path,
        n_generations=n_generations,
        population_size=population_size,
        oracle_noise_level=oracle_noise_level,
        show_live_ranking=show_live_ranking
    )

    print("\nResults:")
    print(formatter.format_jsi_results(results))

    return results


def demo_multi_target_optimization(
    reaper_project_path: Path,
    target_frequencies: list = None,
    n_generations: int = 20,
    population_size: int = 8,
    oracle_noise_level: float = 0.05
) -> Dict[str, Any]:
    """Run multi-target JSI optimization demo.

    This is a convenience function that creates a demo runner with standard dependencies.
    """
    if target_frequencies is None:
        target_frequencies = [220.0, 440.0, 880.0]

    # Print demo header
    formatter = DemoResultsFormatter()
    formatter.print_demo_header("Multi-Target JSI Optimization Demo")

    print(f"REAPER project: {reaper_project_path}")
    print(f"Target frequencies: {target_frequencies} Hz")
    print(f"Generations: {n_generations}, Population: {population_size}")
    print(f"Oracle noise level: {oracle_noise_level}")

    # Create dependencies
    validator = FileSystemProjectValidator()
    problem_factory = StandardOptimizationProblemFactory()
    ga_factory = StandardGAConfigFactory()

    # Create demo runner
    demo_runner = DemoRunner(validator, problem_factory, ga_factory)

    # Run demo
    try:
        results = demo_runner.run_multi_target_optimization(
            reaper_project_path=reaper_project_path,
            target_frequencies=target_frequencies,
            n_generations=n_generations,
            population_size=population_size,
            oracle_noise_level=oracle_noise_level
        )

        print("\nResults:")
        print(formatter.format_multi_target_results(results))

        return results
    except Exception as e:
        print(f"Multi-target optimization failed: {e}")
        return {'error': str(e)}


def demo_comparison_oracle_accuracy(
    reaper_project_path: Path,
    target_frequency: float = 440.0,
    noise_levels: list = None,
    n_comparisons: int = 50
) -> Dict[str, Any]:
    """Demonstrate oracle accuracy at different noise levels.

    This is a convenience function that creates an oracle tester with standard dependencies.
    """
    if noise_levels is None:
        noise_levels = [0.0, 0.1, 0.2, 0.5]

    # Print demo header
    formatter = DemoResultsFormatter()
    formatter.print_demo_header("Comparison Oracle Accuracy Demo")

    print(f"Target frequency: {target_frequency} Hz")
    print(f"Noise levels: {noise_levels}")
    print(f"Comparisons per level: {n_comparisons}")

    # Create dependencies
    oracle_factory = StandardOracleFactory()
    oracle_tester = OracleAccuracyTester(oracle_factory)

    # Run test
    results = oracle_tester.test_oracle_accuracy(
        reaper_project_path=reaper_project_path,
        target_frequency=target_frequency,
        noise_levels=noise_levels,
        n_comparisons=n_comparisons
    )

    print("\nResults:")
    for i, noise_level in enumerate(noise_levels):
        agreement_rate = results['agreement_rates'][i]
        print(f"Noise level {noise_level}: {agreement_rate:.3f} agreement rate")

    return results


def run_full_demo_suite(reaper_project_path: Path) -> Dict[str, Any]:
    """Run the complete demo suite.

    This delegates to the refactored demo suite implementation.
    """
    return _run_full_demo_suite(reaper_project_path)
