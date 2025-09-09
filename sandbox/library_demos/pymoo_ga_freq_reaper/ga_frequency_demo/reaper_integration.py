"""
REAPER integration for genetic algorithm optimization.
Handles session execution, audio rendering, and result collection.
"""

import subprocess
import time
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import os
import signal
from .config import SessionConfig, RenderConfig
from .genetics import Solution
from .audio_analysis import FrequencyDistanceCalculator


class ReaperExecutor:
    """Execute REAPER sessions and collect rendered audio"""

    def __init__(
        self,
        reaper_project_path: Path,
        session_configs_dir: Path = None,
        renders_dir: Path = None,
        timeout: int = 120
    ):
        """Initialize REAPER executor with project paths"""
        self.reaper_project_path = reaper_project_path
        self.session_configs_dir = session_configs_dir or reaper_project_path / "session-configs"
        self.renders_dir = renders_dir or reaper_project_path / "renders"
        self.timeout = timeout

        # Ensure directories exist
        self.session_configs_dir.mkdir(exist_ok=True)
        self.renders_dir.mkdir(exist_ok=True)

    def execute_session(self, session_config: SessionConfig) -> Dict[str, Path]:
        """Execute REAPER session and return paths to rendered audio files"""
        # Save session config to file
        session_file = self.session_configs_dir / f"{session_config.session_name}.json"
        session_config.save_to_file(session_file)

        # Execute REAPER with session
        render_paths = self._run_reaper_session(session_config.session_name)

        return render_paths

    def _run_reaper_session(self, session_name: str) -> Dict[str, Path]:
        """Run REAPER with the specified session configuration"""
        # Change to REAPER project directory
        original_cwd = os.getcwd()

        try:
            os.chdir(self.reaper_project_path)

            # Start REAPER in background [[memory:7053637]]
            cmd = ["uv", "run", "python", "main.py"]

            print(f"Executing REAPER session: {session_name}")
            print(f"Command: {' '.join(cmd)}")
            print(f"Working directory: {self.reaper_project_path}")

            # Run the process and wait for completion
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Create new process group for clean termination
            )

            try:
                stdout, stderr = process.communicate(timeout=self.timeout)

                if process.returncode != 0:
                    raise RuntimeError(f"REAPER execution failed with code {process.returncode}:\n{stderr}")

                print(f"REAPER session completed successfully")
                if stdout.strip():
                    print(f"STDOUT: {stdout}")

            except subprocess.TimeoutExpired:
                # Kill the entire process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                raise RuntimeError(f"REAPER session timed out after {self.timeout} seconds")

            # Collect rendered audio files
            render_paths = self._collect_rendered_files(session_name)
            return render_paths

        finally:
            os.chdir(original_cwd)

    def _collect_rendered_files(self, session_name: str) -> Dict[str, Path]:
        """Collect rendered audio files from the renders directory"""
        render_paths = {}

        # Look for directories matching the session pattern
        for render_dir in self.renders_dir.iterdir():
            if render_dir.is_dir() and session_name in render_dir.name:
                # Look for audio files in the render directory
                for audio_file in render_dir.glob("*.wav"):
                    # Extract render_id from directory name
                    render_id = self._extract_render_id(render_dir.name, session_name)
                    render_paths[render_id] = audio_file
                    print(f"Found rendered audio: {render_id} -> {audio_file}")

        return render_paths

    def _extract_render_id(self, dir_name: str, session_name: str) -> str:
        """Extract render ID from directory name"""
        # Directory format: session_name_render_id_timestamp_params
        parts = dir_name.split('_')
        if len(parts) >= 2:
            # Find session_name in parts and get the next part as render_id
            try:
                session_idx = parts.index(session_name.replace('_', ''))
                if session_idx + 1 < len(parts):
                    return parts[session_idx + 1]
            except ValueError:
                pass

        # Fallback: use the directory name
        return dir_name


class FitnessEvaluator:
    """Evaluate fitness of genetic algorithm solutions using audio analysis"""

    def __init__(
        self,
        target_audio_path: Optional[Path] = None,
        distance_calculator: Optional[FrequencyDistanceCalculator] = None
    ):
        """Initialize fitness evaluator with target audio and distance calculator"""
        self.target_audio_path = target_audio_path
        self.distance_calculator = distance_calculator or FrequencyDistanceCalculator()
        self._target_audio = None

        if target_audio_path and target_audio_path.exists():
            self._target_audio = self.distance_calculator.load_audio(target_audio_path)

    def set_target_audio(self, target_audio_path: Path) -> None:
        """Set the target audio for fitness evaluation"""
        self.target_audio_path = target_audio_path
        self._target_audio = self.distance_calculator.load_audio(target_audio_path)

    def evaluate_solution(self, solution: Solution, rendered_audio_path: Path) -> float:
        """Evaluate fitness of a single solution based on rendered audio"""
        if not rendered_audio_path.exists():
            # Penalize missing audio files heavily
            return 1000.0

        if self._target_audio is None:
            # If no target audio, use parameter-based fitness
            return self._parameter_based_fitness(solution)

        try:
            # Load rendered audio
            rendered_audio = self.distance_calculator.load_audio(rendered_audio_path)

            # Calculate frequency domain distance
            distance = self.distance_calculator.compute_frequency_distance(
                self._target_audio, rendered_audio
            )

            return distance

        except Exception as e:
            print(f"Error evaluating audio {rendered_audio_path}: {e}")
            # Return high penalty for evaluation errors
            return 500.0

    def _parameter_based_fitness(self, solution: Solution) -> float:
        """Fallback fitness based on parameter values when no target audio is available"""
        # Simple fitness function: prefer values closer to center
        octave_penalty = abs(solution.octave) * 0.5
        fine_penalty = abs(solution.fine) * 0.3
        return octave_penalty + fine_penalty

    def evaluate_population(
        self,
        solutions: List[Solution],
        render_paths: Dict[str, Path]
    ) -> List[float]:
        """Evaluate fitness for entire population"""
        fitness_values = []

        for i, solution in enumerate(solutions):
            individual_id = f"individual_{i:03d}"

            # Find matching rendered audio file
            matching_path = None
            for path_id, path in render_paths.items():
                if individual_id in path_id:
                    matching_path = path
                    break

            if matching_path is None:
                # No matching render found
                fitness = 1000.0
                print(f"Warning: No rendered audio found for {individual_id}")
                print(f"Available renders: {list(render_paths.keys())}")
            else:
                fitness = self.evaluate_solution(solution, matching_path)
                print(f"Solution {i}: fitness = {fitness:.4f} (audio: {matching_path.name})")

            fitness_values.append(fitness)

        return fitness_values


class ReaperGAIntegration:
    """Complete integration between genetic algorithm and REAPER"""

    def __init__(
        self,
        reaper_project_path: Path,
        target_audio_path: Optional[Path] = None,
        session_name_prefix: str = "ga_optimization"
    ):
        """Initialize GA-REAPER integration"""
        self.reaper_project_path = reaper_project_path
        self.session_name_prefix = session_name_prefix
        self.executor = ReaperExecutor(reaper_project_path)
        self.evaluator = FitnessEvaluator(target_audio_path)
        self.generation_counter = 0

    def evaluate_population_fitness(self, solutions: List[Solution]) -> List[float]:
        """Evaluate fitness for entire population by rendering and analyzing audio"""
        self.generation_counter += 1
        session_name = f"{self.session_name_prefix}_gen_{self.generation_counter:03d}"

        print(f"\n=== Evaluating Generation {self.generation_counter} ===")
        print(f"Population size: {len(solutions)}")

        # Convert solutions to render configs
        from .genetics import GenomeToPhenotypeMapper
        mapper = GenomeToPhenotypeMapper()
        render_configs = mapper.population_to_render_configs(solutions, session_name)

        # Create session config
        session_config = SessionConfig(
            session_name=session_name,
            render_configs=render_configs
        )

        # Execute REAPER session
        try:
            render_paths = self.executor.execute_session(session_config)
            print(f"Rendered {len(render_paths)} audio files")

            # Evaluate fitness
            fitness_values = self.evaluator.evaluate_population(solutions, render_paths)

            # Log generation statistics
            self._log_generation_stats(self.generation_counter, solutions, fitness_values)

            return fitness_values

        except Exception as e:
            print(f"Error during population evaluation: {e}")
            # Return high penalty values for all solutions
            return [1000.0] * len(solutions)

    def _log_generation_stats(
        self,
        generation: int,
        solutions: List[Solution],
        fitness_values: List[float]
    ) -> None:
        """Log statistics for the current generation"""
        best_fitness = min(fitness_values)
        worst_fitness = max(fitness_values)
        avg_fitness = sum(fitness_values) / len(fitness_values)

        best_idx = fitness_values.index(best_fitness)
        best_solution = solutions[best_idx]

        print(f"\nGeneration {generation} Statistics:")
        print(f"  Best fitness: {best_fitness:.4f}")
        print(f"  Worst fitness: {worst_fitness:.4f}")
        print(f"  Average fitness: {avg_fitness:.4f}")
        print(f"  Best solution: {best_solution}")
        print(f"  Frequency ratio: {best_solution.calculate_frequency_ratio():.4f}")

    def cleanup_old_renders(self, keep_generations: int = 3) -> None:
        """Clean up old render directories to save disk space"""
        if self.generation_counter <= keep_generations:
            return

        cleanup_gen = self.generation_counter - keep_generations
        cleanup_pattern = f"{self.session_name_prefix}_gen_{cleanup_gen:03d}"

        for render_dir in self.executor.renders_dir.iterdir():
            if render_dir.is_dir() and cleanup_pattern in render_dir.name:
                try:
                    shutil.rmtree(render_dir)
                    print(f"Cleaned up old render directory: {render_dir}")
                except Exception as e:
                    print(f"Warning: Could not clean up {render_dir}: {e}")
