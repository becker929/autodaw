"""
Integration tests for the complete GA-REAPER system.
"""

import pytest
import tempfile
import subprocess
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from ga_frequency_demo.genetics import Solution, PopulationGenerator, GenomeToPhenotypeMapper
from ga_frequency_demo.config import SessionConfig
from ga_frequency_demo.reaper_integration import ReaperExecutor, FitnessEvaluator, ReaperGAIntegration
from ga_frequency_demo.ga_problem import FrequencyOptimizationProblem, TargetFrequencyProblem


class TestGenomeToPhenotypeIntegration:
    def test_solution_to_session_config_integration(self):
        """Test complete pipeline from solutions to session config"""
        # Create population
        population = PopulationGenerator.random_population(size=3, seed=42)

        # Map to render configs
        mapper = GenomeToPhenotypeMapper()
        render_configs = mapper.population_to_render_configs(population, "integration_test")

        # Create session config
        session = SessionConfig(
            session_name="integration_test",
            render_configs=render_configs
        )

        # Verify structure
        assert session.session_name == "integration_test"
        assert len(session.render_configs) == 3

        # Verify JSON serialization works
        json_str = session.to_json()
        assert "integration_test" in json_str

        # Verify can be loaded back
        loaded_session = SessionConfig.from_json(json_str)
        assert loaded_session.session_name == session.session_name
        assert len(loaded_session.render_configs) == len(session.render_configs)

    def test_parameter_mapping_consistency(self):
        """Test that parameter mapping is consistent and reversible"""
        solution = Solution(octave=1.5, fine=0.3)
        mapper = GenomeToPhenotypeMapper()

        # Map to Serum parameters
        serum_params = mapper.solution_to_serum_params(solution)

        # Verify parameters are in valid range
        assert 0.0 <= serum_params["A Octave"] <= 1.0
        assert 0.0 <= serum_params["A Fine"] <= 1.0

        # Verify mapping is consistent
        render_config = mapper.solution_to_render_config(solution, "test")

        octave_param = next(p for p in render_config.parameters if p.param == "A Octave")
        fine_param = next(p for p in render_config.parameters if p.param == "A Fine")

        assert octave_param.value == serum_params["A Octave"]
        assert fine_param.value == serum_params["A Fine"]


class TestReaperExecutorMocked:
    """Test ReaperExecutor with mocked subprocess calls"""

    def test_executor_initialization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            executor = ReaperExecutor(temp_path)

            assert executor.reaper_project_path == temp_path
            assert executor.session_configs_dir == temp_path / "session-configs"
            assert executor.renders_dir == temp_path / "renders"

            # Directories should be created
            assert executor.session_configs_dir.exists()
            assert executor.renders_dir.exists()

    @patch('ga_frequency_demo.reaper_integration.subprocess.Popen')
    @patch('os.chdir')
    def test_execute_session_success(self, mock_chdir, mock_popen):
        """Test successful session execution"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            executor = ReaperExecutor(temp_path)

            # Mock successful subprocess execution
            mock_process = Mock()
            mock_process.communicate.return_value = ("Success", "")
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Create mock render directory and file
            render_dir = executor.renders_dir / "integration_test_individual_000_20241201_120000_params"
            render_dir.mkdir(parents=True)
            render_file = render_dir / "untitled.wav"
            render_file.touch()

            # Create session config
            render_config = GenomeToPhenotypeMapper().solution_to_render_config(
                Solution(0.0, 0.0), "individual_000"
            )
            session = SessionConfig("integration_test", [render_config])

            # Execute session
            render_paths = executor.execute_session(session)

            # Verify execution
            mock_popen.assert_called_once()
            assert len(render_paths) == 1
            assert "individual_000" in list(render_paths.keys())[0]

    @patch('ga_frequency_demo.reaper_integration.os.killpg')
    @patch('ga_frequency_demo.reaper_integration.os.getpgid')
    @patch('ga_frequency_demo.reaper_integration.subprocess.Popen')
    @patch('os.chdir')
    def test_execute_session_timeout(self, mock_chdir, mock_popen, mock_getpgid, mock_killpg):
        """Test session execution timeout"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            executor = ReaperExecutor(temp_path, timeout=1)  # Very short timeout

            # Mock timeout
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=1)
            mock_popen.return_value = mock_process

            # Mock the process group functions
            mock_getpgid.return_value = 12345

            render_config = GenomeToPhenotypeMapper().solution_to_render_config(
                Solution(0.0, 0.0), "test"
            )
            session = SessionConfig("test_session", [render_config])

            with pytest.raises(RuntimeError, match="timed out"):
                executor.execute_session(session)

            # Verify cleanup was attempted
            mock_killpg.assert_called()


class TestFitnessEvaluatorMocked:
    def test_evaluator_initialization(self):
        evaluator = FitnessEvaluator()

        assert evaluator.target_audio_path is None
        assert evaluator._target_audio is None
        assert evaluator.distance_calculator is not None

    def test_parameter_based_fitness(self):
        evaluator = FitnessEvaluator()  # No target audio

        # Test center solution (should have low fitness)
        center_solution = Solution(0.0, 0.0)
        fitness = evaluator._parameter_based_fitness(center_solution)
        assert fitness >= 0

        # Test extreme solution (should have higher fitness)
        extreme_solution = Solution(2.0, 1.0)
        extreme_fitness = evaluator._parameter_based_fitness(extreme_solution)
        assert extreme_fitness > fitness

    def test_evaluate_solution_missing_file(self):
        evaluator = FitnessEvaluator()
        solution = Solution(0.0, 0.0)

        # Test with non-existent file
        fitness = evaluator.evaluate_solution(solution, Path("nonexistent.wav"))

        # Should return high penalty
        assert fitness == 1000.0

    def test_evaluate_population_partial_renders(self):
        evaluator = FitnessEvaluator()
        solutions = [Solution(0.0, 0.0), Solution(1.0, 0.5)]

        # Mock render paths with only one file
        render_paths = {"individual_000": Path("nonexistent.wav")}

        fitness_values = evaluator.evaluate_population(solutions, render_paths)

        assert len(fitness_values) == 2
        assert fitness_values[0] == 1000.0  # No matching render
        assert fitness_values[1] == 1000.0  # No matching render


class TestGAProblemIntegration:
    @patch('ga_frequency_demo.reaper_integration.ReaperGAIntegration')
    def test_frequency_optimization_problem_creation(self, mock_integration):
        """Test problem creation and basic structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            problem = FrequencyOptimizationProblem(temp_path)

            assert problem.n_var == 2  # octave, fine
            assert problem.n_obj == 1  # single objective
            assert len(problem.xl) == 2
            assert len(problem.xu) == 2
            assert problem.xl[0] == -2.0  # octave lower bound
            assert problem.xu[0] == 2.0   # octave upper bound
            assert problem.xl[1] == -1.0  # fine lower bound
            assert problem.xu[1] == 1.0   # fine upper bound

    @patch('ga_frequency_demo.reaper_integration.ReaperGAIntegration')
    def test_target_frequency_problem_creation(self, mock_integration):
        """Test target frequency problem creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            problem = TargetFrequencyProblem(temp_path, target_frequency_ratio=2.0)

            assert problem.n_var == 2
            assert problem.n_obj == 1
            assert problem.target_frequency_ratio == 2.0

    def test_problem_evaluate_structure(self):
        """Test that problem evaluation has correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a problem and mock its reaper_integration directly
            problem = FrequencyOptimizationProblem(temp_path)

            # Mock the evaluate_population_fitness method
            mock_fitness_values = [1.0, 2.0, 3.0]
            problem.reaper_integration.evaluate_population_fitness = Mock(return_value=mock_fitness_values)

            # Test evaluation with 3 individuals
            x = np.array([[0.0, 0.0], [1.0, 0.5], [-1.0, -0.5]])
            out = {}

            problem._evaluate(x, out)

            # Verify output structure
            assert "F" in out
            assert out["F"].shape == (3, 1)
            assert np.array_equal(out["F"].flatten(), [1.0, 2.0, 3.0])

            # Verify integration was called correctly
            problem.reaper_integration.evaluate_population_fitness.assert_called_once()
            call_args = problem.reaper_integration.evaluate_population_fitness.call_args[0]
            solutions = call_args[0]
            assert len(solutions) == 3
            assert all(isinstance(sol, Solution) for sol in solutions)


class TestEndToEndIntegration:
    def test_complete_pipeline_structure(self):
        """Test the complete pipeline structure without actual REAPER execution"""
        # Create population
        population = PopulationGenerator.random_population(size=5, seed=42)

        # Map to render configs
        mapper = GenomeToPhenotypeMapper()
        render_configs = mapper.population_to_render_configs(population, "e2e_test")

        # Create session
        session = SessionConfig("e2e_test", render_configs)

        # Verify complete structure
        assert len(session.render_configs) == 5

        for i, config in enumerate(session.render_configs):
            assert config.render_id == f"e2e_test_individual_{i:03d}"
            assert len(config.tracks) == 1
            assert config.tracks[0].name == "Serum Track"
            assert len(config.parameters) == 2

            # Verify parameter values are in valid range
            for param in config.parameters:
                assert 0.0 <= param.value <= 1.0

        # Test JSON serialization
        json_str = session.to_json()
        loaded_session = SessionConfig.from_json(json_str)

        assert loaded_session.session_name == session.session_name
        assert len(loaded_session.render_configs) == len(session.render_configs)

    def test_solution_frequency_consistency(self):
        """Test that solution frequency calculations are consistent"""
        solutions = [
            Solution(0.0, 0.0),   # Should be 1.0
            Solution(1.0, 0.0),   # Should be 2.0
            Solution(-1.0, 0.0),  # Should be 0.5
            Solution(0.0, 1.0),   # Should be slightly above 1.0
            Solution(0.0, -1.0),  # Should be slightly below 1.0
        ]

        expected_ratios = [1.0, 2.0, 0.5]

        for i, (solution, expected) in enumerate(zip(solutions[:3], expected_ratios)):
            ratio = solution.calculate_frequency_ratio()
            assert abs(ratio - expected) < 1e-6, f"Solution {i}: expected {expected}, got {ratio}"

        # Test fine tuning effects
        base_ratio = solutions[0].calculate_frequency_ratio()
        up_ratio = solutions[3].calculate_frequency_ratio()
        down_ratio = solutions[4].calculate_frequency_ratio()

        assert up_ratio > base_ratio
        assert down_ratio < base_ratio
