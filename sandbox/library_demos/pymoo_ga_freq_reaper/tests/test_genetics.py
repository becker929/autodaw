"""
Unit tests for genetics module.
"""

import pytest
import numpy as np
from ga_frequency_demo.genetics import (
    Solution, GenomeToPhenotypeMapper, PopulationGenerator, calculate_parameter_distance
)


class TestSolution:
    def test_solution_creation(self):
        solution = Solution(octave=1.5, fine=0.3)
        assert solution.octave == 1.5
        assert solution.fine == 0.3

    def test_solution_bounds_clamping(self):
        # Test upper bounds
        solution = Solution(octave=3.0, fine=2.0)
        assert solution.octave == 2.0  # Clamped to max
        assert solution.fine == 1.0    # Clamped to max

        # Test lower bounds
        solution = Solution(octave=-3.0, fine=-2.0)
        assert solution.octave == -2.0  # Clamped to min
        assert solution.fine == -1.0    # Clamped to min

    def test_to_array(self):
        solution = Solution(octave=1.0, fine=0.5)
        arr = solution.to_array()

        assert isinstance(arr, np.ndarray)
        assert len(arr) == 2
        assert arr[0] == 1.0
        assert arr[1] == 0.5

    def test_from_array(self):
        arr = np.array([1.0, 0.5])
        solution = Solution.from_array(arr)

        assert solution.octave == 1.0
        assert solution.fine == 0.5

    def test_calculate_frequency_ratio(self):
        # Test center values (should be 1.0)
        solution = Solution(octave=0.0, fine=0.0)
        ratio = solution.calculate_frequency_ratio()
        assert abs(ratio - 1.0) < 1e-6

        # Test one octave up (should be 2.0)
        solution = Solution(octave=1.0, fine=0.0)
        ratio = solution.calculate_frequency_ratio()
        assert abs(ratio - 2.0) < 1e-6

        # Test one octave down (should be 0.5)
        solution = Solution(octave=-1.0, fine=0.0)
        ratio = solution.calculate_frequency_ratio()
        assert abs(ratio - 0.5) < 1e-6

    def test_string_representation(self):
        solution = Solution(octave=1.5, fine=0.3)
        str_repr = str(solution)

        assert "Solution" in str_repr
        assert "1.5000" in str_repr
        assert "0.3000" in str_repr


class TestGenomeToPhenotypeMapper:
    def test_mapper_creation(self):
        mapper = GenomeToPhenotypeMapper()
        assert mapper.midi_file == "test_melody.mid"

        mapper = GenomeToPhenotypeMapper("custom.mid")
        assert mapper.midi_file == "custom.mid"

    def test_solution_to_serum_params(self):
        mapper = GenomeToPhenotypeMapper()
        solution = Solution(octave=0.0, fine=0.0)  # Center values

        params = mapper.solution_to_serum_params(solution)

        assert "A Octave" in params
        assert "A Fine" in params
        assert params["A Octave"] == 0.5  # (0 + 2) / 4 = 0.5
        assert params["A Fine"] == 0.5    # (0 + 1) / 2 = 0.5

    def test_solution_to_serum_params_bounds(self):
        mapper = GenomeToPhenotypeMapper()

        # Test minimum values
        solution = Solution(octave=-2.0, fine=-1.0)
        params = mapper.solution_to_serum_params(solution)
        assert params["A Octave"] == 0.0
        assert params["A Fine"] == 0.0

        # Test maximum values
        solution = Solution(octave=2.0, fine=1.0)
        params = mapper.solution_to_serum_params(solution)
        assert params["A Octave"] == 1.0
        assert params["A Fine"] == 1.0

    def test_solution_to_render_config(self):
        mapper = GenomeToPhenotypeMapper()
        solution = Solution(octave=1.0, fine=0.5)

        render_config = mapper.solution_to_render_config(solution, "test_render")

        assert render_config.render_id == "test_render"
        assert len(render_config.tracks) == 1
        assert render_config.tracks[0].name == "Serum Track"
        assert len(render_config.parameters) == 2

        # Check parameter values
        octave_param = next(p for p in render_config.parameters if p.param == "A Octave")
        fine_param = next(p for p in render_config.parameters if p.param == "A Fine")

        assert octave_param.value == 0.75  # (1 + 2) / 4 = 0.75
        assert fine_param.value == 0.75    # (0.5 + 1) / 2 = 0.75

    def test_population_to_render_configs(self):
        mapper = GenomeToPhenotypeMapper()
        population = [
            Solution(octave=0.0, fine=0.0),
            Solution(octave=1.0, fine=0.5),
            Solution(octave=-1.0, fine=-0.5)
        ]

        render_configs = mapper.population_to_render_configs(population, "test_session")

        assert len(render_configs) == 3
        assert render_configs[0].render_id == "test_session_individual_000"
        assert render_configs[1].render_id == "test_session_individual_001"
        assert render_configs[2].render_id == "test_session_individual_002"


class TestPopulationGenerator:
    def test_random_population(self):
        population = PopulationGenerator.random_population(size=10, seed=42)

        assert len(population) == 10
        assert all(isinstance(sol, Solution) for sol in population)

        # Check bounds
        for solution in population:
            assert -2.0 <= solution.octave <= 2.0
            assert -1.0 <= solution.fine <= 1.0

        # Test reproducibility
        population2 = PopulationGenerator.random_population(size=10, seed=42)
        for sol1, sol2 in zip(population, population2):
            assert sol1.octave == sol2.octave
            assert sol1.fine == sol2.fine

    def test_targeted_population(self):
        target_octave = 1.0
        target_fine = 0.5
        population = PopulationGenerator.targeted_population(
            size=10,
            target_octave=target_octave,
            target_fine=target_fine,
            variance=0.1,
            seed=42
        )

        assert len(population) == 10

        # Check that population is centered around target values
        octave_mean = np.mean([sol.octave for sol in population])
        fine_mean = np.mean([sol.fine for sol in population])

        assert abs(octave_mean - target_octave) < 0.5  # Should be close to target
        assert abs(fine_mean - target_fine) < 0.5

    def test_diverse_population(self):
        population = PopulationGenerator.diverse_population(size=10, seed=42)

        assert len(population) == 10

        # Check that corner cases are included
        octave_values = [sol.octave for sol in population]
        fine_values = [sol.fine for sol in population]

        # Should have some diversity in values
        assert len(set(octave_values)) > 1
        assert len(set(fine_values)) > 1

        # Should include center point
        center_solutions = [sol for sol in population if sol.octave == 0.0 and sol.fine == 0.0]
        assert len(center_solutions) >= 1

    def test_diverse_population_small_size(self):
        population = PopulationGenerator.diverse_population(size=3, seed=42)

        assert len(population) == 3
        # Should still work with small sizes


class TestUtilityFunctions:
    def test_calculate_parameter_distance(self):
        sol1 = Solution(octave=0.0, fine=0.0)
        sol2 = Solution(octave=1.0, fine=0.5)

        distance = calculate_parameter_distance(sol1, sol2)

        assert distance > 0
        assert isinstance(distance, float)

        # Distance to self should be 0
        self_distance = calculate_parameter_distance(sol1, sol1)
        assert abs(self_distance) < 1e-6

        # Distance should be symmetric
        reverse_distance = calculate_parameter_distance(sol2, sol1)
        assert abs(distance - reverse_distance) < 1e-6

    def test_calculate_parameter_distance_weights(self):
        # Test that octave changes are weighted more heavily
        sol_base = Solution(octave=0.0, fine=0.0)
        sol_octave = Solution(octave=1.0, fine=0.0)  # Only octave change
        sol_fine = Solution(octave=0.0, fine=1.0)    # Only fine change

        octave_distance = calculate_parameter_distance(sol_base, sol_octave)
        fine_distance = calculate_parameter_distance(sol_base, sol_fine)

        # Octave changes should have larger distance due to weighting
        assert octave_distance > fine_distance
