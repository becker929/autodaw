"""Main orchestration for GA + JSI + Audio Oracle + REAPER integration demo."""

import time
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize
from pymoo.termination import get_termination

from .ga_problem import JSIAudioOptimizationProblem, MultiTargetJSIOptimizationProblem
from .audio_oracle import AudioComparisonOracle, FrequencyTargetOracle


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

    Args:
        reaper_project_path: Path to REAPER project directory
        target_frequency: Target frequency in Hz
        target_audio_path: Optional target audio file
        n_generations: Number of GA generations
        population_size: Size of GA population
        oracle_noise_level: Noise level for oracle decisions (0.0 = perfect, 1.0 = random)
        show_live_ranking: Whether to show live JSI ranking updates

    Returns:
        Dictionary with optimization results
    """
    print("=== GA + JSI + Audio Oracle Integration Demo ===")
    print(f"REAPER project: {reaper_project_path}")
    print(f"Target frequency: {target_frequency} Hz")
    print(f"Target audio: {target_audio_path or 'None (using frequency)'}")
    print(f"Generations: {n_generations}, Population: {population_size}")
    print(f"Oracle noise level: {oracle_noise_level}")
    print(f"Live ranking: {show_live_ranking}")

    # Validate REAPER project
    if not reaper_project_path.exists():
        raise FileNotFoundError(f"REAPER project not found: {reaper_project_path}")

    # Create optimization problem
    problem = JSIAudioOptimizationProblem(
        reaper_project_path=reaper_project_path,
        target_frequency=target_frequency,
        target_audio_path=target_audio_path,
        session_name_prefix="jsi_audio_demo",
        oracle_noise_level=oracle_noise_level,
        show_live_ranking=show_live_ranking
    )

    # Configure genetic algorithm
    algorithm = GA(
        pop_size=population_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=0.1, eta=20),
        eliminate_duplicates=True
    )

    # Set termination criteria
    termination = get_termination("n_gen", n_generations)

    print(f"\nStarting optimization...")
    start_time = time.time()

    try:
        # Run optimization
        result = minimize(
            problem=problem,
            algorithm=algorithm,
            termination=termination,
            verbose=True,
            save_history=True
        )

        end_time = time.time()
        duration = end_time - start_time

        print(f"\nOptimization completed in {duration:.2f} seconds")

        # Extract best solution information
        best_info = problem.get_best_solution_info(result)

        # Compile results
        results = {
            'success': True,
            'best_info': best_info,
            'duration_seconds': duration,
            'target_frequency': target_frequency,
            'target_audio_path': str(target_audio_path) if target_audio_path else None,
            'oracle_noise_level': oracle_noise_level,
            'generations_completed': problem.generation_counter,
            'total_evaluations': problem.evaluation_count,
            'population_size': population_size,
            'result': result
        }

        # Print summary
        print("\n" + "="*60)
        print("OPTIMIZATION SUMMARY")
        print("="*60)

        if best_info:
            print(f"Best solution: {best_info['solution']}")
            print(f"Best fitness: {best_info['fitness']:.6f}")
            print(f"Frequency ratio: {best_info['frequency_ratio']:.6f}")
            print(f"Total evaluations: {best_info['evaluations']}")
            print(f"JSI comparisons: {best_info.get('jsi_comparisons', 'N/A')}")

        print(f"Optimization time: {duration:.2f} seconds")
        print(f"Generations completed: {problem.generation_counter}")

        # Clear oracle cache to free memory
        problem.clear_oracle_cache()

        return results

    except Exception as e:
        print(f"Optimization failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e),
            'duration_seconds': time.time() - start_time,
            'generations_completed': problem.generation_counter,
            'total_evaluations': problem.evaluation_count
        }


def demo_multi_target_optimization(
    reaper_project_path: Path,
    target_frequencies: list = None,
    n_generations: int = 20,
    population_size: int = 8,
    oracle_noise_level: float = 0.05
) -> Dict[str, Any]:
    """Run multi-target JSI optimization demo.

    Args:
        reaper_project_path: Path to REAPER project directory
        target_frequencies: List of target frequencies to optimize towards
        n_generations: Number of GA generations
        population_size: Size of GA population
        oracle_noise_level: Oracle noise level

    Returns:
        Dictionary with optimization results
    """
    if target_frequencies is None:
        target_frequencies = [440.0, 523.25, 659.25, 783.99]  # A4, C5, E5, G5

    print("=== Multi-Target JSI Audio Optimization Demo ===")
    print(f"Target frequencies: {target_frequencies} Hz")

    # Create multi-target problem
    problem = MultiTargetJSIOptimizationProblem(
        reaper_project_path=reaper_project_path,
        target_frequencies=target_frequencies,
        session_name_prefix="multi_jsi_demo",
        oracle_noise_level=oracle_noise_level,
        show_live_ranking=True
    )

    # Configure algorithm
    algorithm = GA(
        pop_size=population_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=0.1, eta=20),
        eliminate_duplicates=True
    )

    termination = get_termination("n_gen", n_generations)

    print(f"\nStarting multi-target optimization...")
    start_time = time.time()

    try:
        result = minimize(
            problem=problem,
            algorithm=algorithm,
            termination=termination,
            verbose=True,
            save_history=True
        )

        end_time = time.time()
        duration = end_time - start_time

        best_info = problem.get_best_solution_info(result)

        results = {
            'success': True,
            'best_info': best_info,
            'duration_seconds': duration,
            'target_frequencies': target_frequencies,
            'generations_completed': problem.generation_counter,
            'total_evaluations': problem.evaluation_count,
            'result': result
        }

        print(f"\nMulti-target optimization completed in {duration:.2f} seconds")
        if best_info:
            print(f"Final best solution: {best_info['solution']}")
            print(f"Final frequency ratio: {best_info['frequency_ratio']:.6f}")

        problem.clear_oracle_cache()
        return results

    except Exception as e:
        print(f"Multi-target optimization failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'duration_seconds': time.time() - start_time
        }


def demo_comparison_oracle_accuracy(
    reaper_project_path: Path,
    target_frequency: float = 440.0,
    noise_levels: list = None,
    n_comparisons: int = 50
) -> Dict[str, Any]:
    """Demonstrate oracle accuracy at different noise levels.

    Args:
        reaper_project_path: Path to REAPER project
        target_frequency: Target frequency for comparisons
        noise_levels: List of noise levels to test
        n_comparisons: Number of comparisons per noise level

    Returns:
        Dictionary with accuracy results
    """
    if noise_levels is None:
        noise_levels = [0.0, 0.05, 0.1, 0.2, 0.5]

    print("=== Audio Oracle Accuracy Demo ===")
    print(f"Target frequency: {target_frequency} Hz")
    print(f"Noise levels: {noise_levels}")
    print(f"Comparisons per level: {n_comparisons}")

    results = {}

    for noise_level in noise_levels:
        print(f"\nTesting noise level: {noise_level}")

        oracle = AudioComparisonOracle(
            target_frequency=target_frequency,
            noise_level=noise_level,
            random_seed=42
        )

        # Create synthetic test data
        # Generate frequencies at different distances from target
        test_frequencies = [
            target_frequency * (1 + 0.1 * i) for i in range(-5, 6)
        ]

        correct_decisions = 0
        total_decisions = 0

        # Test all pairwise comparisons
        for i, freq_a in enumerate(test_frequencies):
            for j, freq_b in enumerate(test_frequencies):
                if i != j:
                    # Create mock audio data (just frequency values for testing)
                    # In real usage, these would be audio file paths

                    # Ground truth: freq closer to target should win
                    dist_a = abs(freq_a - target_frequency)
                    dist_b = abs(freq_b - target_frequency)
                    expected_a_wins = dist_a < dist_b

                    # Oracle decision (using frequency as mock audio)
                    oracle_decision = oracle.compare(freq_a, freq_b)

                    if oracle_decision == expected_a_wins:
                        correct_decisions += 1

                    total_decisions += 1

                    if total_decisions >= n_comparisons:
                        break

            if total_decisions >= n_comparisons:
                break

        accuracy = correct_decisions / total_decisions if total_decisions > 0 else 0.0
        results[noise_level] = {
            'accuracy': accuracy,
            'correct_decisions': correct_decisions,
            'total_decisions': total_decisions
        }

        print(f"Accuracy: {accuracy:.3f} ({correct_decisions}/{total_decisions})")

    return {
        'target_frequency': target_frequency,
        'noise_levels': noise_levels,
        'results': results
    }


def run_full_demo_suite(reaper_project_path: Path) -> Dict[str, Any]:
    """Run the complete demo suite.

    Args:
        reaper_project_path: Path to REAPER project

    Returns:
        Dictionary with all demo results
    """
    print("="*80)
    print("GA + JSI + AUDIO ORACLE INTEGRATION - FULL DEMO SUITE")
    print("="*80)

    all_results = {}

    try:
        # Demo 1: Basic JSI optimization
        print("\n" + "="*50)
        print("DEMO 1: Basic JSI Audio Optimization")
        print("="*50)

        basic_result = demo_jsi_audio_optimization(
            reaper_project_path=reaper_project_path,
            target_frequency=440.0,
            n_generations=8,
            population_size=6,
            oracle_noise_level=0.05,
            show_live_ranking=True
        )
        all_results['basic_optimization'] = basic_result

        # Demo 2: Multi-target optimization
        print("\n" + "="*50)
        print("DEMO 2: Multi-Target Optimization")
        print("="*50)

        multi_result = demo_multi_target_optimization(
            reaper_project_path=reaper_project_path,
            target_frequencies=[440.0, 523.25, 659.25],
            n_generations=12,
            population_size=6,
            oracle_noise_level=0.05
        )
        all_results['multi_target'] = multi_result

        # Demo 3: Oracle accuracy analysis
        print("\n" + "="*50)
        print("DEMO 3: Oracle Accuracy Analysis")
        print("="*50)

        accuracy_result = demo_comparison_oracle_accuracy(
            reaper_project_path=reaper_project_path,
            target_frequency=440.0,
            noise_levels=[0.0, 0.05, 0.1, 0.2],
            n_comparisons=30
        )
        all_results['oracle_accuracy'] = accuracy_result

        print("\n" + "="*80)
        print("FULL DEMO SUITE COMPLETED SUCCESSFULLY")
        print("="*80)

        return {
            'success': True,
            'demos': all_results,
            'summary': 'All demos completed successfully'
        }

    except Exception as e:
        print(f"\nDemo suite failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e),
            'completed_demos': all_results
        }
