"""Entry point for GA + JSI + Human Audio Oracle integration demo."""

from pathlib import Path
from ga_jsi_audio_oracle.main import demo_jsi_audio_optimization
from ga_jsi_audio_oracle.human_audio_oracle import HumanAudioComparisonOracle


def main():
    """Run the GA + JSI + Human Audio Oracle demo."""
    print("GA + JSI + Human Audio Oracle Integration Demo")
    print("=" * 50)
    print("This demo uses HUMAN selection instead of automated frequency analysis!")
    print("You will be presented with pairs of audio files to choose between.")
    print("=" * 50)

    # Locate REAPER project
    reaper_path = Path("../../reaper").resolve()
    if not reaper_path.exists():
        print(f"Error: REAPER project not found at {reaper_path}")
        print("Please ensure the reaper project is available at the expected location.")
        return 1

    try:
        # Create human oracle with GUI interface
        print("\nInitializing GUI interface for audio comparisons...")
        print("Note: If GUI fails, the system will automatically fall back to console mode.")
        oracle = HumanAudioComparisonOracle(window_title="Audio Evolution - Make Your Choice")

        print("\nStarting human-guided audio optimization...")
        print("You will be asked to choose between audio samples during the optimization process.")
        print("The genetic algorithm will evolve based on your preferences!")

        # Run the optimization with human oracle
        result = demo_jsi_human_audio_optimization(
            reaper_project_path=reaper_path,
            oracle=oracle,
            n_generations=4,  # Fewer generations since human input takes time
            population_size=4,  # Smaller population for manageable human comparisons
            show_live_ranking=True
        )

        if result['success']:
            print("\n" + "="*60)
            print("HUMAN-GUIDED OPTIMIZATION COMPLETED!")
            print("="*60)

            best_info = result.get('best_info', {})
            if best_info:
                print(f"Best solution found: {best_info.get('solution', 'N/A')}")
                print(f"Best fitness: {best_info.get('fitness', 'N/A')}")
                print(f"Human comparisons made: {oracle.get_comparison_count()}")

            print(f"Total duration: {result.get('duration_seconds', 'N/A')} seconds")
            print(f"Generations completed: {result.get('generations_completed', 'N/A')}")

            print("\nThe audio files have been evolved based on your preferences!")
            print("Check reaper/renders/ for the generated audio files.")
            print("The final solution represents what the algorithm learned you prefer.")
        else:
            print(f"Demo failed: {result.get('error', 'Unknown error')}")
            return 1

        return 0

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def demo_jsi_human_audio_optimization(
    reaper_project_path: Path,
    oracle: HumanAudioComparisonOracle,
    n_generations: int = 4,
    population_size: int = 4,
    show_live_ranking: bool = True
):
    """Run JSI optimization with human audio oracle.

    Args:
        reaper_project_path: Path to REAPER project directory
        oracle: Human audio comparison oracle
        n_generations: Number of GA generations
        population_size: Size of GA population
        show_live_ranking: Whether to show live JSI ranking updates

    Returns:
        Dictionary with optimization results
    """
    import time
    from pymoo.algorithms.soo.nonconvex.ga import GA
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.operators.sampling.rnd import FloatRandomSampling
    from pymoo.optimize import minimize
    from pymoo.termination import get_termination
    from ga_jsi_audio_oracle.ga_problem import HumanJSIAudioOptimizationProblem

    print("=== GA + JSI + Human Audio Oracle Integration ===")
    print(f"REAPER project: {reaper_project_path}")
    print(f"Generations: {n_generations}, Population: {population_size}")
    print(f"Oracle: {type(oracle).__name__}")
    print(f"Live ranking: {show_live_ranking}")

    # Validate REAPER project
    if not reaper_project_path.exists():
        raise FileNotFoundError(f"REAPER project not found: {reaper_project_path}")

    # Create optimization problem with human oracle
    problem = HumanJSIAudioOptimizationProblem(
        reaper_project_path=reaper_project_path,
        human_oracle=oracle,
        session_name_prefix="human_audio_demo",
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

    print(f"\nStarting human-guided optimization...")
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
            'oracle_type': type(oracle).__name__,
            'generations_completed': problem.generation_counter,
            'total_evaluations': problem.evaluation_count,
            'population_size': population_size,
            'human_comparisons': oracle.get_comparison_count(),
            'result': result
        }

        # Print summary
        print("\n" + "="*60)
        print("HUMAN-GUIDED OPTIMIZATION SUMMARY")
        print("="*60)

        if best_info:
            print(f"Best solution: {best_info['solution']}")
            print(f"Best fitness: {best_info['fitness']:.6f}")
            print(f"Total evaluations: {best_info['evaluations']}")
            print(f"Human comparisons: {oracle.get_comparison_count()}")

        print(f"Optimization time: {duration:.2f} seconds")
        print(f"Generations completed: {problem.generation_counter}")

        return results

    except Exception as e:
        print(f"Optimization failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e),
            'duration_seconds': time.time() - start_time,
            'generations_completed': getattr(problem, 'generation_counter', 0),
            'total_evaluations': getattr(problem, 'evaluation_count', 0)
        }


if __name__ == "__main__":
    exit(main())
