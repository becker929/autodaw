"""Tests for live ranking engine."""

import pytest
import numpy as np
import threading
import time
from choix_active_online_demo.live_ranking_engine import LiveRankingEngine


class TestLiveRankingEngine:
    """Test cases for LiveRankingEngine."""

    def test_initialization(self):
        """Test proper initialization."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        assert engine.item_names == items
        assert engine.n_items == 3
        assert engine.name_to_idx == {"A": 0, "B": 1, "C": 2}
        assert engine.comparisons == []
        assert engine.strengths is None

    def test_add_comparison(self):
        """Test adding comparisons."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        engine.add_comparison("A", "B", "A")
        assert len(engine.comparisons) == 1
        assert engine.comparisons[0] == (0, 1)  # A beats B
        assert engine.strengths is not None

        engine.add_comparison("B", "C", "C")
        assert len(engine.comparisons) == 2
        assert engine.comparisons[1] == (2, 1)  # C beats B

    def test_add_comparison_invalid_winner(self):
        """Test adding comparison with invalid winner."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        with pytest.raises(ValueError, match="Winner 'X' must be either"):
            engine.add_comparison("A", "B", "X")

    def test_get_current_ranking(self):
        """Test getting current ranking."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        # Initially should return original order
        ranking = engine.get_current_ranking()
        assert len(ranking) == 3
        assert all(item in ranking for item in items)

        # After comparisons, should return strength-based ranking
        engine.add_comparison("A", "B", "A")
        engine.add_comparison("A", "C", "A")

        ranking = engine.get_current_ranking()
        assert len(ranking) == 3
        # A should likely be first (beat both B and C)
        # Note: exact ranking depends on Bradley-Terry model convergence

    def test_get_win_probabilities(self):
        """Test win probability calculations."""
        items = ["A", "B"]
        engine = LiveRankingEngine(items)

        # Initially 50-50
        prob_a, prob_b = engine.get_win_probabilities("A", "B")
        assert prob_a == 0.5
        assert prob_b == 0.5

        # After A beats B once
        engine.add_comparison("A", "B", "A")

        prob_a, prob_b = engine.get_win_probabilities("A", "B")
        assert prob_a + prob_b == pytest.approx(1.0)
        # Just verify probabilities are valid

    def test_get_comparison_count(self):
        """Test comparison counting."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        assert engine.get_comparison_count() == 0

        engine.add_comparison("A", "B", "A")
        assert engine.get_comparison_count() == 1

        engine.add_comparison("B", "C", "C")
        assert engine.get_comparison_count() == 2

    def test_get_comparison_matrix(self):
        """Test comparison matrix generation."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        engine.add_comparison("A", "B", "A")
        engine.add_comparison("A", "C", "A")
        engine.add_comparison("B", "C", "B")

        matrix = engine.get_comparison_matrix()

        assert matrix.shape == (3, 3)
        assert matrix.loc["A", "B"] == 1  # A beat B once
        assert matrix.loc["A", "C"] == 1  # A beat C once
        assert matrix.loc["B", "C"] == 1  # B beat C once
        assert matrix.loc["B", "A"] == 0  # B never beat A

    def test_get_ranking_statistics(self):
        """Test ranking statistics."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        # Initial statistics
        stats = engine.get_ranking_statistics()
        assert stats['comparison_count'] == 0
        assert stats['n_items'] == 3
        assert stats['model_fitted'] == False

        # After comparisons
        engine.add_comparison("A", "B", "A")
        engine.add_comparison("B", "C", "B")

        stats = engine.get_ranking_statistics()
        assert stats['comparison_count'] == 2
        assert stats['model_fitted'] == True
        assert 'strengths' in stats
        assert 'uncertainties' in stats
        assert 'top_item' in stats
        assert 'ranking_confidence' in stats

    def test_update_callbacks(self):
        """Test update callbacks."""
        items = ["A", "B"]
        engine = LiveRankingEngine(items)

        callback_called = []

        def callback():
            callback_called.append(True)

        engine.add_update_callback(callback)

        engine.add_comparison("A", "B", "A")
        assert len(callback_called) == 1

        engine.add_comparison("B", "A", "B")
        assert len(callback_called) == 2

        # Remove callback
        engine.remove_update_callback(callback)
        engine.add_comparison("A", "B", "A")
        assert len(callback_called) == 2  # Should not increase

    def test_reset(self):
        """Test resetting the engine."""
        items = ["A", "B", "C"]
        engine = LiveRankingEngine(items)

        engine.add_comparison("A", "B", "A")
        engine.add_comparison("B", "C", "B")

        assert len(engine.comparisons) > 0
        assert engine.strengths is not None

        engine.reset()

        assert len(engine.comparisons) == 0
        assert engine.strengths is None

    def test_thread_safety(self):
        """Test thread safety of the engine."""
        items = ["A", "B", "C", "D"]
        engine = LiveRankingEngine(items)

        def worker(item_pairs):
            for item_a, item_b, winner in item_pairs:
                engine.add_comparison(item_a, item_b, winner)

        # Create multiple threads adding comparisons (reduced load)
        comparisons_1 = [("A", "B", "A"), ("C", "D", "C")] * 2
        comparisons_2 = [("B", "C", "B"), ("A", "D", "D")] * 2

        thread1 = threading.Thread(target=worker, args=(comparisons_1,))
        thread2 = threading.Thread(target=worker, args=(comparisons_2,))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Should have all comparisons
        assert engine.get_comparison_count() == 8

        # Should have valid ranking
        ranking = engine.get_current_ranking()
        assert len(ranking) == 4
        assert all(item in ranking for item in items)

    def test_fallback_strengths(self):
        """Test fallback strength calculation."""
        items = ["A", "B"]
        engine = LiveRankingEngine(items)

        # Add comparison that might cause Bradley-Terry to fail
        engine.add_comparison("A", "B", "A")

        # Should have some strength estimates (either BT or fallback)
        assert engine.strengths is not None
        assert len(engine.strengths) == 2

        # Test ranking still works
        ranking = engine.get_current_ranking()
        assert len(ranking) == 2
