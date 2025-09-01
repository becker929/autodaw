"""Tests for Bradley-Terry demonstration."""

import pytest
import numpy as np
from choix_demo.bradley_terry import BradleyTerryDemo


class TestBradleyTerryDemo:
    """Test cases for BradleyTerryDemo class."""

    def test_initialization(self):
        """Test proper initialization of demo instance."""
        demo = BradleyTerryDemo(n_items=5, random_seed=42)

        assert demo.n_items == 5
        assert demo.random_seed == 42
        assert len(demo.true_strengths) == 5
        assert len(demo.item_names) == 5
        assert demo.comparisons == []
        assert demo.estimated_strengths is None

    def test_generate_comparison_data(self):
        """Test comparison data generation."""
        demo = BradleyTerryDemo(n_items=4, random_seed=42)
        comparisons = demo.generate_comparison_data(n_comparisons=50)

        assert len(comparisons) == 50
        assert len(demo.comparisons) == 50

        # Check that all comparisons are valid
        for winner, loser, margin in comparisons:
            assert 0 <= winner < 4
            assert 0 <= loser < 4
            assert winner != loser
            assert margin == 1

    def test_fit_bradley_terry_model(self):
        """Test model fitting."""
        demo = BradleyTerryDemo(n_items=4, random_seed=42)
        demo.generate_comparison_data(n_comparisons=100)

        strengths = demo.fit_bradley_terry_model()

        assert len(strengths) == 4
        assert demo.estimated_strengths is not None
        assert np.all(np.isfinite(strengths))

    def test_fit_without_data_raises_error(self):
        """Test that fitting without data raises an error."""
        demo = BradleyTerryDemo(n_items=4, random_seed=42)

        with pytest.raises(ValueError, match="No comparison data available"):
            demo.fit_bradley_terry_model()

    def test_get_rankings(self):
        """Test ranking generation."""
        demo = BradleyTerryDemo(n_items=4, random_seed=42)
        demo.generate_comparison_data(n_comparisons=100)
        demo.fit_bradley_terry_model()

        rankings = demo.get_rankings()

        assert 'true_ranking' in rankings
        assert 'estimated_ranking' in rankings
        assert 'true_strengths' in rankings
        assert 'estimated_strengths' in rankings

        assert len(rankings['true_ranking']) == 4
        assert len(rankings['estimated_ranking']) == 4
        assert len(rankings['true_strengths']) == 4
        assert len(rankings['estimated_strengths']) == 4

    def test_get_rankings_without_fitting_raises_error(self):
        """Test that getting rankings without fitting raises an error."""
        demo = BradleyTerryDemo(n_items=4, random_seed=42)

        with pytest.raises(ValueError, match="Model not fitted"):
            demo.get_rankings()

    def test_get_comparison_matrix(self):
        """Test comparison matrix generation."""
        demo = BradleyTerryDemo(n_items=3, random_seed=42)
        demo.generate_comparison_data(n_comparisons=50)

        matrix = demo.get_comparison_matrix()

        assert matrix.shape == (3, 3)
        assert np.all(matrix.values >= 0)
        assert np.sum(matrix.values) == 50  # Total comparisons
        assert np.all(np.diag(matrix.values) == 0)  # No self-comparisons

    def test_calculate_accuracy_metrics(self):
        """Test accuracy metrics calculation."""
        demo = BradleyTerryDemo(n_items=5, random_seed=42)
        demo.generate_comparison_data(n_comparisons=200)
        demo.fit_bradley_terry_model()

        metrics = demo.calculate_accuracy_metrics()

        assert 'kendall_tau' in metrics
        assert 'kendall_p_value' in metrics
        assert 'top_1_accuracy' in metrics

        # Check that tau is between -1 and 1
        assert -1 <= metrics['kendall_tau'] <= 1

        # Check that accuracies are between 0 and 1
        for key, value in metrics.items():
            if key.endswith('_accuracy'):
                assert 0 <= value <= 1

    def test_run_full_demo(self):
        """Test complete demo run."""
        demo = BradleyTerryDemo(n_items=4, random_seed=42)
        results = demo.run_full_demo(n_comparisons=100)

        assert 'n_items' in results
        assert 'n_comparisons' in results
        assert 'rankings' in results
        assert 'accuracy_metrics' in results
        assert 'comparison_matrix' in results

        assert results['n_items'] == 4
        assert results['n_comparisons'] == 100

    def test_reproducibility(self):
        """Test that results are reproducible with same random seed."""
        demo1 = BradleyTerryDemo(n_items=4, random_seed=42)
        results1 = demo1.run_full_demo(n_comparisons=100)

        demo2 = BradleyTerryDemo(n_items=4, random_seed=42)
        results2 = demo2.run_full_demo(n_comparisons=100)

        # True strengths should be identical
        np.testing.assert_array_equal(demo1.true_strengths, demo2.true_strengths)

        # Comparisons should be identical
        assert demo1.comparisons == demo2.comparisons

        # Estimated strengths should be very close
        np.testing.assert_allclose(
            demo1.estimated_strengths,
            demo2.estimated_strengths,
            rtol=1e-10
        )
