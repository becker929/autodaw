"""
Main demo script for genetic algorithm frequency optimization with REAPER.
"""

import argparse
import numpy as np
from pathlib import Path
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling

from .ga_problem import FrequencyOptimizationProblem, TargetFrequencyProblem
from .genetics import PopulationGenerator, Solution
from .audio_analysis import create_target_audio_generator


def create_ga_algorithm(pop_size: int = 20, n_gen: int = 10) -> GA:
    """Create and configure genetic algorithm"""
    algorithm = GA(
        pop_size=pop_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=0.1, eta=20),
        eliminate_duplicates=True,
        verbose=True
    )
    return algorithm


def run_frequency_optimization(
    reaper_project_path: Path,
    target_audio_path: Path = None,
    pop_size: int = 20,
    n_gen: int = 10,
    session_prefix: str = "ga_demo"
) -> dict:
    """Run genetic algorithm optimization for frequency matching"""

    print("=== Genetic Algorithm Frequency Optimization ===")
    print(f"REAPER project path: {reaper_project_path}")
    print(f"Target audio: {target_audio_path}")
    print(f"Population size: {pop_size}")
    print(f"Generations: {n_gen}")

    # Create optimization problem
    problem = FrequencyOptimizationProblem(
        reaper_project_path=reaper_project_path,
        target_audio_path=target_audio_path,
        session_name_prefix=session_prefix
    )

    # Create algorithm
    algorithm = create_ga_algorithm(pop_size=pop_size, n_gen=n_gen)

    # Run optimization
    print("\nStarting optimization...")
    result = minimize(
        problem,
        algorithm,
        termination=("n_gen", n_gen),
        verbose=True
    )

    # Extract results
    best_info = problem.get_best_solution_info(result)

    print("\n=== Optimization Results ===")
    if best_info:
        print(f"Best solution: {best_info['solution']}")
        print(f"Best fitness: {best_info['fitness']:.6f}")
        print(f"Frequency ratio: {best_info['frequency_ratio']:.6f}")
        print(f"Total evaluations: {best_info['evaluations']}")
        print(f"Generations completed: {best_info['generations']}")

    return {
        'result': result,
        'problem': problem,
        'best_info': best_info
    }


def run_target_frequency_optimization(
    reaper_project_path: Path,
    target_frequency_ratio: float,
    reference_audio_path: Path = None,
    pop_size: int = 20,
    n_gen: int = 10,
    session_prefix: str = "ga_target_demo"
) -> dict:
    """Run optimization targeting a specific frequency ratio"""

    print("=== Target Frequency Ratio Optimization ===")
    print(f"Target frequency ratio: {target_frequency_ratio}")
    print(f"Expected octave: {np.log2(target_frequency_ratio):.3f}")

    # Create target frequency problem
    problem = TargetFrequencyProblem(
        reaper_project_path=reaper_project_path,
        target_frequency_ratio=target_frequency_ratio,
        reference_audio_path=reference_audio_path,
        session_name_prefix=session_prefix
    )

    # Create algorithm
    algorithm = create_ga_algorithm(pop_size=pop_size, n_gen=n_gen)

    # Run optimization
    result = minimize(
        problem,
        algorithm,
        termination=("n_gen", n_gen),
        verbose=True
    )

    # Extract results
    best_info = problem.get_best_solution_info(result)

    print("\n=== Target Frequency Results ===")
    if best_info:
        solution = best_info['solution']
        achieved_ratio = best_info['frequency_ratio']
        ratio_error = abs(achieved_ratio - target_frequency_ratio)

        print(f"Target frequency ratio: {target_frequency_ratio:.6f}")
        print(f"Achieved frequency ratio: {achieved_ratio:.6f}")
        print(f"Ratio error: {ratio_error:.6f}")
        print(f"Best solution: {solution}")
        print(f"Best fitness: {best_info['fitness']:.6f}")

    return {
        'result': result,
        'problem': problem,
        'best_info': best_info,
        'target_ratio': target_frequency_ratio
    }


def demo_basic_optimization():
    """Run basic optimization demo"""
    reaper_path = Path("../reaper").resolve()

    if not reaper_path.exists():
        print(f"Error: REAPER project not found at {reaper_path}")
        return

    # Run basic frequency optimization
    result = run_frequency_optimization(
        reaper_project_path=reaper_path,
        pop_size=10,
        n_gen=5,
        session_prefix="basic_demo"
    )

    return result


def demo_target_frequency():
    """Run target frequency demo"""
    reaper_path = Path("../reaper").resolve()

    if not reaper_path.exists():
        print(f"Error: REAPER project not found at {reaper_path}")
        return

    # Target frequency ratio of 2.0 (one octave up)
    target_ratio = 2.0

    result = run_target_frequency_optimization(
        reaper_project_path=reaper_path,
        target_frequency_ratio=target_ratio,
        pop_size=10,
        n_gen=5,
        session_prefix="target_demo"
    )

    return result


def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description="GA Frequency Optimization Demo")
    parser.add_argument("--reaper-path", type=Path, default="../reaper",
                       help="Path to REAPER project directory")
    parser.add_argument("--target-audio", type=Path, default=None,
                       help="Path to target audio file")
    parser.add_argument("--target-ratio", type=float, default=None,
                       help="Target frequency ratio for optimization")
    parser.add_argument("--pop-size", type=int, default=10,
                       help="Population size for GA")
    parser.add_argument("--generations", type=int, default=5,
                       help="Number of generations")
    parser.add_argument("--demo", choices=["basic", "target"], default="basic",
                       help="Demo type to run")

    args = parser.parse_args()

    reaper_path = args.reaper_path.resolve()

    if not reaper_path.exists():
        print(f"Error: REAPER project not found at {reaper_path}")
        return 1

    if args.demo == "basic":
        result = run_frequency_optimization(
            reaper_project_path=reaper_path,
            target_audio_path=args.target_audio,
            pop_size=args.pop_size,
            n_gen=args.generations,
            session_prefix="cli_basic"
        )
    elif args.demo == "target":
        if args.target_ratio is None:
            args.target_ratio = 2.0  # Default to one octave up

        result = run_target_frequency_optimization(
            reaper_project_path=reaper_path,
            target_frequency_ratio=args.target_ratio,
            reference_audio_path=args.target_audio,
            pop_size=args.pop_size,
            n_gen=args.generations,
            session_prefix="cli_target"
        )

    return 0


if __name__ == "__main__":
    exit(main())
