"""Unit tests for genetics module."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch

from serum_evolver.src.genetics.genetics import (
    Solution, GenomeToPhenotypeMapper, PopulationGenerator,
    calculate_parameter_distance
)


class TestSolution:
    """Test cases for Solution class."""

    def test_initialization_basic(self):
        """Test basic solution initialization."""
        solution = Solution(octave=1.0, fine=0.5)

        assert solution.octave == 1.0
        assert solution.fine == 0.5

    def test_initialization_with_bounds_clamping(self):
        """Test initialization with parameter bounds clamping."""
        # Test octave bounds
        solution1 = Solution(octave=5.0, fine=0.0)  # Over upper bound
        assert solution1.octave == 2.0

        solution2 = Solution(octave=-5.0, fine=0.0)  # Under lower bound
        assert solution2.octave == -2.0

        # Test fine bounds
        solution3 = Solution(octave=0.0, fine=2.0)  # Over upper bound
        assert solution3.fine == 1.0

        solution4 = Solution(octave=0.0, fine=-2.0)  # Under lower bound
        assert solution4.fine == -1.0

    def test_to_array(self):
        """Test conversion to numpy array."""
        solution = Solution(octave=1.5, fine=-0.3)
        array = solution.to_array()

        assert isinstance(array, np.ndarray)
        np.testing.assert_array_equal(array, np.array([1.5, -0.3]))

    def test_from_array(self):
        """Test creation from numpy array."""
        array = np.array([0.8, -0.2])
        solution = Solution.from_array(array)

        assert solution.octave == 0.8
        assert solution.fine == -0.2

    def test_calculate_frequency_ratio(self):
        """Test frequency ratio calculation."""
        # Test octave = 0, fine = 0 (should be 1.0)
        solution1 = Solution(octave=0.0, fine=0.0)
        assert solution1.calculate_frequency_ratio() == pytest.approx(1.0)

        # Test octave = 1 (should be 2.0)
        solution2 = Solution(octave=1.0, fine=0.0)
        assert solution2.calculate_frequency_ratio() == pytest.approx(2.0)

        # Test octave = -1 (should be 0.5)
        solution3 = Solution(octave=-1.0, fine=0.0)
        assert solution3.calculate_frequency_ratio() == pytest.approx(0.5)

        # Test fine tuning effect
        solution4 = Solution(octave=0.0, fine=12.0)  # Will be clamped to 1.0
        ratio4 = solution4.calculate_frequency_ratio()
        assert ratio4 > 1.0  # Should be higher than baseline

    def test_string_representation(self):
        """Test string representation."""
        solution = Solution(octave=1.2345, fine=-0.6789)
        str_repr = str(solution)

        assert "Solution" in str_repr
        assert "1.2345" in str_repr
        assert "-0.6789" in str_repr


class TestGenomeToPhenotypeMapper:
    """Test cases for GenomeToPhenotypeMapper."""

    def test_initialization(self):
        """Test mapper initialization."""
        mapper = GenomeToPhenotypeMapper()
        assert mapper.midi_file == "test_melody.mid"

        custom_mapper = GenomeToPhenotypeMapper("custom.mid")
        assert custom_mapper.midi_file == "custom.mid"

    def test_solution_to_serum_params(self):
        """Test conversion of solution to Serum parameters."""
        mapper = GenomeToPhenotypeMapper()
        solution = Solution(octave=0.0, fine=0.0)

        params = mapper.solution_to_serum_params(solution)

        assert "A Octave" in params
        assert "A Fine" in params
        assert params["A Octave"] == 0.5  # (0 + 2) / 4 = 0.5
        assert params["A Fine"] == 0.5    # (0 + 1) / 2 = 0.5

    def test_solution_to_serum_params_bounds(self):
        """Test parameter conversion with bounds."""
        mapper = GenomeToPhenotypeMapper()

        # Test extremes
        solution_min = Solution(octave=-2.0, fine=-1.0)
        params_min = mapper.solution_to_serum_params(solution_min)
        assert params_min["A Octave"] == 0.0
        assert params_min["A Fine"] == 0.0

        solution_max = Solution(octave=2.0, fine=1.0)
        params_max = mapper.solution_to_serum_params(solution_max)
        assert params_max["A Octave"] == 1.0
        assert params_max["A Fine"] == 1.0

    @patch('serum_evolver.src.genetics.genetics.create_basic_serum_render_config')
    def test_solution_to_render_config(self, mock_create_config):
        """Test conversion of solution to render configuration."""
        mapper = GenomeToPhenotypeMapper("test.mid")
        solution = Solution(octave=1.0, fine=-0.5)

        mock_config = Mock()
        mock_create_config.return_value = mock_config

        result = mapper.solution_to_render_config(solution, "test_render")

        assert result == mock_config
        mock_create_config.assert_called_once_with(
            render_id="test_render",
            octave_value=0.75,  # (1 + 2) / 4 = 0.75
            fine_value=0.25,   # (-0.5 + 1) / 2 = 0.25
            midi_file="test.mid"
        )

    @patch('serum_evolver.src.genetics.genetics.create_basic_serum_render_config')
    def test_population_to_render_configs(self, mock_create_config):
        """Test conversion of entire population to render configurations."""
        mapper = GenomeToPhenotypeMapper()

        population = [
            Solution(octave=0.0, fine=0.0),
            Solution(octave=1.0, fine=-1.0),
            Solution(octave=-1.0, fine=1.0)
        ]

        mock_config = Mock()
        mock_create_config.return_value = mock_config

        configs = mapper.population_to_render_configs(population, "test_session")

        assert len(configs) == 3
        assert all(config == mock_config for config in configs)

        # Check that create_basic_serum_render_config was called correctly
        assert mock_create_config.call_count == 3

        # Check render IDs
        call_args_list = mock_create_config.call_args_list
        expected_render_ids = [
            "test_session_individual_000",
            "test_session_individual_001",
            "test_session_individual_002"
        ]

        for i, call_args in enumerate(call_args_list):
            args, kwargs = call_args
            assert kwargs["render_id"] == expected_render_ids[i]


class TestPopulationGenerator:
    """Test cases for PopulationGenerator."""

    def test_random_population(self):
        """Test random population generation."""
        population = PopulationGenerator.random_population(size=10, seed=42)

        assert len(population) == 10
        assert all(isinstance(sol, Solution) for sol in population)

        # Test bounds
        for solution in population:
            assert -2.0 <= solution.octave <= 2.0
            assert -1.0 <= solution.fine <= 1.0

    def test_random_population_reproducibility(self):
        """Test that random population is reproducible with seed."""
        pop1 = PopulationGenerator.random_population(size=5, seed=123)
        pop2 = PopulationGenerator.random_population(size=5, seed=123)

        for sol1, sol2 in zip(pop1, pop2):
            assert sol1.octave == sol2.octave
            assert sol1.fine == sol2.fine

    def test_targeted_population(self):
        """Test targeted population generation around specific values."""
        target_octave = 1.0
        target_fine = 0.5
        variance = 0.1

        population = PopulationGenerator.targeted_population(
            size=20,
            target_octave=target_octave,
            target_fine=target_fine,
            variance=variance,
            seed=456
        )

        assert len(population) == 20

        # Check that population is roughly centered around targets
        octave_mean = np.mean([sol.octave for sol in population])
        fine_mean = np.mean([sol.fine for sol in population])

        assert abs(octave_mean - target_octave) < variance
        assert abs(fine_mean - target_fine) < variance * 0.5  # Fine has less variance

    def test_diverse_population(self):
        """Test diverse population generation with corner cases."""
        population = PopulationGenerator.diverse_population(size=10, seed=789)

        assert len(population) == 10

        # Check that corner cases are included
        octave_values = [sol.octave for sol in population]
        fine_values = [sol.fine for sol in population]

        # Should include extreme values
        assert any(abs(oct - (-2.0)) < 0.01 for oct in octave_values)  # Low octave
        assert any(abs(oct - 2.0) < 0.01 for oct in octave_values)     # High octave
        assert any(abs(fine - (-1.0)) < 0.01 for fine in fine_values)  # Low fine
        assert any(abs(fine - 1.0) < 0.01 for fine in fine_values)     # High fine
        assert any(abs(oct) < 0.01 and abs(fine) < 0.01 for oct, fine in zip(octave_values, fine_values))  # Center

    def test_diverse_population_small_size(self):
        """Test diverse population with size smaller than corner cases."""
        population = PopulationGenerator.diverse_population(size=3, seed=999)

        assert len(population) == 3
        # Should still work and include some corner cases

    def test_diverse_population_large_size(self):
        """Test diverse population with large size."""
        population = PopulationGenerator.diverse_population(size=50, seed=111)

        assert len(population) == 50
        # Should include all corner cases plus random ones


class TestParameterDistance:
    """Test cases for parameter distance calculation."""

    def test_calculate_parameter_distance_identical(self):
        """Test distance between identical solutions."""
        sol1 = Solution(octave=1.0, fine=0.5)
        sol2 = Solution(octave=1.0, fine=0.5)

        distance = calculate_parameter_distance(sol1, sol2)
        assert distance == pytest.approx(0.0)

    def test_calculate_parameter_distance_octave_only(self):
        """Test distance with only octave difference."""
        sol1 = Solution(octave=0.0, fine=0.0)
        sol2 = Solution(octave=1.0, fine=0.0)

        distance = calculate_parameter_distance(sol1, sol2)

        # Distance should be weighted by octave weight (4.0)
        expected = 4.0 * 1.0  # octave_weight * diff_octave
        assert distance == pytest.approx(expected)

    def test_calculate_parameter_distance_fine_only(self):
        """Test distance with only fine difference."""
        sol1 = Solution(octave=0.0, fine=0.0)
        sol2 = Solution(octave=0.0, fine=1.0)

        distance = calculate_parameter_distance(sol1, sol2)

        # Distance should be weighted by fine weight (1.0)
        expected = 1.0 * 1.0  # fine_weight * diff_fine
        assert distance == pytest.approx(expected)

    def test_calculate_parameter_distance_both(self):
        """Test distance with both octave and fine differences."""
        sol1 = Solution(octave=0.0, fine=0.0)
        sol2 = Solution(octave=1.0, fine=1.0)

        distance = calculate_parameter_distance(sol1, sol2)

        # Distance should be sqrt((4.0 * 1.0)^2 + (1.0 * 1.0)^2)
        expected = np.sqrt(16.0 + 1.0)  # sqrt(4^2 + 1^2)
        assert distance == pytest.approx(expected)

    def test_calculate_parameter_distance_weighting(self):
        """Test that octave changes are weighted more heavily than fine changes."""
        sol_base = Solution(octave=0.0, fine=0.0)
        sol_octave = Solution(octave=0.25, fine=0.0)  # Small octave change
        sol_fine = Solution(octave=0.0, fine=1.0)     # Large fine change

        distance_octave = calculate_parameter_distance(sol_base, sol_octave)
        distance_fine = calculate_parameter_distance(sol_base, sol_fine)

        # Small octave change should have same impact as large fine change due to weighting
        expected_octave = 4.0 * 0.25  # 1.0
        expected_fine = 1.0 * 1.0     # 1.0

        assert distance_octave == pytest.approx(expected_octave)
        assert distance_fine == pytest.approx(expected_fine)


if __name__ == "__main__":
    pytest.main([__file__])
