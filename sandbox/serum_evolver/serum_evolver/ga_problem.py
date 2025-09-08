"""GA problem class that integrates JSI ranking with audio oracle comparisons."""

import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
from pymoo.core.problem import Problem

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "pymoo_ga_freq_reaper"))

from ga_frequency_demo.genetics import Solution, GenomeToPhenotypeMapper
from ga_frequency_demo.reaper_integration import ReaperExecutor
from ga_frequency_demo.config import SessionConfig
from .audio_oracle import AudioComparisonOracle, FrequencyTargetOracle
from .jsi_ga_integration import JSIFitnessEvaluator


class JSIAudioOptimizationProblem(Problem):
    """GA problem that uses JSI + audio oracle for fitness evaluation instead of direct distance."""

    def __init__(
        self,
        reaper_project_path: Path,
        target_frequency: float = 440.0,
        target_audio_path: Optional[Path] = None,
        session_name_prefix: str = "jsi_audio_ga",
        oracle_noise_level: float = 0.05,
        show_live_ranking: bool = True
    ):
        """Initialize JSI audio optimization problem.

        Args:
            reaper_project_path: Path to REAPER project directory
            target_frequency: Target frequency in Hz for comparisons
            target_audio_path: Optional path to target audio file
            session_name_prefix: Prefix for session names
            oracle_noise_level: Noise level for oracle decisions
            show_live_ranking: Whether to show live JSI ranking updates
        """
        # Define problem dimensions (same as original frequency problem)
        n_var = 2  # octave, fine
        n_obj = 1  # Single objective: maximize JSI-derived fitness
        xl = np.array([-2.0, -1.0])  # Lower bounds
        xu = np.array([2.0, 1.0])    # Upper bounds

        super().__init__(n_var=n_var, n_obj=n_obj, xl=xl, xu=xu)

        # Store configuration
        self.reaper_project_path = reaper_project_path
        self.session_name_prefix = session_name_prefix
        self.show_live_ranking = show_live_ranking

        # Initialize REAPER executor
        self.reaper_executor = ReaperExecutor(reaper_project_path)

        # Initialize audio oracle
        if target_audio_path and target_audio_path.exists():
            self.oracle = FrequencyTargetOracle(
                target_audio_path=target_audio_path,
                noise_level=oracle_noise_level
            )
            print(f"Using target audio file: {target_audio_path}")
        else:
            self.oracle = AudioComparisonOracle(
                target_frequency=target_frequency,
                noise_level=oracle_noise_level
            )
            print(f"Using target frequency: {target_frequency} Hz")

        # Initialize JSI fitness evaluator
        # Note: Don't store Console object directly to avoid serialization issues with pymoo
        self.jsi_evaluator = JSIFitnessEvaluator(
            oracle=self.oracle,
            console=None  # Will create console when needed
        )
        self.show_live_ranking = show_live_ranking

        # Initialize genome mapper
        self.genome_mapper = GenomeToPhenotypeMapper()

        # Tracking
        self.generation_counter = 0
        self.evaluation_count = 0

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate population using JSI ranking with audio oracle comparisons."""
        self.generation_counter += 1
        session_name = f"{self.session_name_prefix}_gen_{self.generation_counter:03d}"

        print(f"\n=== Evaluating Generation {self.generation_counter} ===")
        print(f"Population size: {len(x)}")

        # Convert numpy population to Solution objects
        solutions = []
        for i, individual in enumerate(x):
            octave, fine = individual
            solution = Solution(octave=octave, fine=fine)
            solutions.append(solution)

        try:
            # Step 1: Render audio using REAPER
            audio_paths = self._render_population_audio(solutions, session_name)

            # Step 2: Use JSI + audio oracle to rank population
            fitness_values = self.jsi_evaluator.evaluate_population_fitness(
                solutions, audio_paths, self.generation_counter
            )

            # Update evaluation counter
            self.evaluation_count += len(solutions)

            # Log generation statistics
            self._log_generation_stats(solutions, fitness_values)

            # Cleanup old renders periodically
            if self.generation_counter % 3 == 0:
                self._cleanup_old_renders(keep_generations=2)

            # Convert to numpy array for pymoo (note: we need to negate for minimization)
            # JSI gives higher values for better solutions, but pymoo minimizes by default
            out["F"] = np.array([-f for f in fitness_values]).reshape(-1, 1)

        except Exception as e:
            print(f"Error during population evaluation: {e}")
            import traceback
            traceback.print_exc()

            # Return penalty values for all solutions
            penalty_fitness = [-1000.0] * len(solutions)
            out["F"] = np.array(penalty_fitness).reshape(-1, 1)

    def _render_population_audio(
        self,
        solutions: List[Solution],
        session_name: str
    ) -> Dict[str, Path]:
        """Render audio for entire population using REAPER.

        Args:
            solutions: List of solutions to render
            session_name: Name for this rendering session

        Returns:
            Dictionary mapping solution IDs to rendered audio paths
        """
        # Convert solutions to render configs
        render_configs = self.genome_mapper.population_to_render_configs(
            solutions, session_name
        )

        # Create session config
        session_config = SessionConfig(
            session_name=session_name,
            render_configs=render_configs
        )

        # Execute REAPER session
        print(f"Rendering {len(solutions)} audio files with REAPER...")
        render_paths = self.reaper_executor.execute_session(session_config)

        print(f"Successfully rendered {len(render_paths)} audio files")

        # Map render paths to solution IDs for JSI
        solution_audio_map = {}
        for i, solution in enumerate(solutions):
            solution_id = f"sol_{i:03d}"
            individual_id = f"individual_{i:03d}"

            # Find matching rendered audio
            matching_path = None
            for render_id, path in render_paths.items():
                if individual_id in render_id or str(i).zfill(3) in render_id:
                    matching_path = path
                    break

            if matching_path:
                solution_audio_map[solution_id] = matching_path
            else:
                print(f"Warning: No rendered audio found for solution {i}")

        return solution_audio_map

    def _log_generation_stats(
        self,
        solutions: List[Solution],
        fitness_values: List[float]
    ) -> None:
        """Log statistics for the current generation.

        Args:
            solutions: List of solutions
            fitness_values: List of fitness values
        """
        if not fitness_values:
            return

        best_fitness = max(fitness_values)  # Higher is better for JSI
        worst_fitness = min(fitness_values)
        avg_fitness = sum(fitness_values) / len(fitness_values)

        best_idx = fitness_values.index(best_fitness)
        best_solution = solutions[best_idx]

        # Get JSI ranking info
        ranking_info = self.jsi_evaluator.get_ranking_info()

        print(f"\nGeneration {self.generation_counter} Statistics:")
        print(f"  Best fitness: {best_fitness:.4f}")
        print(f"  Worst fitness: {worst_fitness:.4f}")
        print(f"  Average fitness: {avg_fitness:.4f}")
        print(f"  Best solution: {best_solution}")
        print(f"  Frequency ratio: {best_solution.calculate_frequency_ratio():.4f}")
        print(f"  JSI comparisons: {ranking_info.get('comparison_count', 0)}")
        print(f"  Total evaluations: {self.evaluation_count}")

    def _cleanup_old_renders(self, keep_generations: int = 2) -> None:
        """Clean up old render directories to save disk space.

        Args:
            keep_generations: Number of recent generations to keep
        """
        if self.generation_counter <= keep_generations:
            return

        cleanup_gen = self.generation_counter - keep_generations
        cleanup_pattern = f"{self.session_name_prefix}_gen_{cleanup_gen:03d}"

        renders_dir = self.reaper_executor.renders_dir
        for render_dir in renders_dir.iterdir():
            if render_dir.is_dir() and cleanup_pattern in render_dir.name:
                try:
                    import shutil
                    shutil.rmtree(render_dir)
                    print(f"Cleaned up old render directory: {render_dir}")
                except Exception as e:
                    print(f"Warning: Could not clean up {render_dir}: {e}")

    def get_best_solution_info(self, result) -> Dict[str, Any]:
        """Extract information about the best solution found.

        Args:
            result: Optimization result from pymoo

        Returns:
            Dictionary with best solution information
        """
        if hasattr(result, 'X') and hasattr(result, 'F'):
            best_x = result.X
            best_fitness = -result.F[0]  # Convert back from negated fitness

            best_solution = Solution(octave=best_x[0], fine=best_x[1])

            return {
                'solution': best_solution,
                'fitness': best_fitness,
                'frequency_ratio': best_solution.calculate_frequency_ratio(),
                'evaluations': self.evaluation_count,
                'generations': self.generation_counter,
                'jsi_comparisons': self.jsi_evaluator.get_ranking_info().get('comparison_count', 0)
            }

        return {}

    def set_target_frequency(self, frequency: float) -> None:
        """Update the target frequency for the oracle.

        Args:
            frequency: New target frequency in Hz
        """
        if hasattr(self.oracle, 'set_target_frequency'):
            self.oracle.set_target_frequency(frequency)
            print(f"Updated target frequency to {frequency} Hz")

    def clear_oracle_cache(self) -> None:
        """Clear the oracle's audio cache to free memory."""
        if hasattr(self.oracle, 'clear_cache'):
            self.oracle.clear_cache()


class MultiTargetJSIOptimizationProblem(JSIAudioOptimizationProblem):
    """JSI optimization problem that can handle multiple target frequencies."""

    def __init__(
        self,
        reaper_project_path: Path,
        target_frequencies: List[float],
        session_name_prefix: str = "multi_jsi_audio_ga",
        oracle_noise_level: float = 0.05,
        show_live_ranking: bool = True
    ):
        """Initialize multi-target JSI problem.

        Args:
            reaper_project_path: Path to REAPER project
            target_frequencies: List of target frequencies to optimize towards
            session_name_prefix: Session name prefix
            oracle_noise_level: Oracle noise level
            show_live_ranking: Whether to show live ranking
        """
        # Initialize with first target frequency
        super().__init__(
            reaper_project_path=reaper_project_path,
            target_frequency=target_frequencies[0],
            session_name_prefix=session_name_prefix,
            oracle_noise_level=oracle_noise_level,
            show_live_ranking=show_live_ranking
        )

        self.target_frequencies = target_frequencies
        self.current_target_index = 0

    def _evaluate(self, x, out, *args, **kwargs):
        """Evaluate with rotating target frequencies."""
        # Rotate target frequency every few generations
        if self.generation_counter > 0 and self.generation_counter % 5 == 0:
            self.current_target_index = (self.current_target_index + 1) % len(self.target_frequencies)
            new_target = self.target_frequencies[self.current_target_index]
            self.set_target_frequency(new_target)
            print(f"Switched to target frequency: {new_target} Hz")

        # Call parent evaluation
        super()._evaluate(x, out, *args, **kwargs)
