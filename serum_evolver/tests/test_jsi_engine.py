"""Tests for src/ranking/jsi_engine.py module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from rich.console import Console

from serum_evolver.src.ranking.jsi_engine import JSIAdaptiveQuicksort


class TestJSIAdaptiveQuicksort:
    """Test cases for JSIAdaptiveQuicksort class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.oracle = Mock()
        self.tracker = Mock()
        self.engine = JSIAdaptiveQuicksort(self.oracle, self.tracker)

    def test_initialization(self):
        """Test basic initialization."""
        assert self.engine.oracle is self.oracle
        assert self.engine.tracker is self.tracker
        assert self.engine.comparison_count == 0

    def test_adaptive_quicksort_empty_list(self):
        """Test sorting empty list."""
        result = self.engine.adaptive_quicksort([])
        assert result == []
        assert self.engine.comparison_count == 0

        # No oracle or tracker calls should be made
        self.oracle.compare.assert_not_called()
        self.tracker.add_comparison.assert_not_called()

    def test_adaptive_quicksort_single_item(self):
        """Test sorting single item list."""
        items = ['item1']
        result = self.engine.adaptive_quicksort(items)
        assert result == ['item1']
        assert self.engine.comparison_count == 0

        # No oracle or tracker calls should be made
        self.oracle.compare.assert_not_called()
        self.tracker.add_comparison.assert_not_called()

    def test_adaptive_quicksort_two_items_first_greater(self):
        """Test sorting two items where first is greater."""
        items = ['item1', 'item2']

        # Mock oracle to say item2 > item1 (so item2 goes to greater partition)
        self.oracle.compare.return_value = True

        result = self.engine.adaptive_quicksort(items)

        # Should be sorted as [item1, item2] (pivot item1, item2 in greater)
        assert result == ['item1', 'item2']
        assert self.engine.comparison_count == 1

        # Verify oracle and tracker calls
        self.oracle.compare.assert_called_once_with('item2', 'item1')
        self.tracker.add_comparison.assert_called_once_with('item2', 'item1', 'item2')

    def test_adaptive_quicksort_two_items_first_smaller(self):
        """Test sorting two items where first is smaller."""
        items = ['item1', 'item2']

        # Mock oracle to say item2 <= item1 (so item2 goes to less partition)
        self.oracle.compare.return_value = False

        result = self.engine.adaptive_quicksort(items)

        # Should be sorted as [item2, item1] (pivot item1, item2 in less)
        assert result == ['item2', 'item1']
        assert self.engine.comparison_count == 1

        # Verify oracle and tracker calls
        self.oracle.compare.assert_called_once_with('item2', 'item1')
        self.tracker.add_comparison.assert_called_once_with('item2', 'item1', 'item1')

    def test_adaptive_quicksort_multiple_items(self):
        """Test sorting multiple items."""
        items = ['pivot', 'less1', 'greater1', 'less2']

        # Mock oracle responses: less1 <= pivot, greater1 > pivot, less2 <= pivot
        # Use return_value instead of side_effect to avoid StopIteration
        def mock_compare(item1, item2):
            if item1 == 'less1' and item2 == 'pivot':
                return False
            elif item1 == 'greater1' and item2 == 'pivot':
                return True
            elif item1 == 'less2' and item2 == 'pivot':
                return False
            else:
                return False  # Default case

        self.oracle.compare.side_effect = mock_compare

        result = self.engine.adaptive_quicksort(items)

        # Check structure: less items, pivot, greater items
        # Order within less partition may vary due to recursion
        assert len(result) == 4
        pivot_index = result.index('pivot')
        assert pivot_index == 2  # Pivot should be in position 2

        less_items = result[:pivot_index]
        greater_items = result[pivot_index+1:]

        assert set(less_items) == {'less1', 'less2'}
        assert greater_items == ['greater1']
        # Comparison count may be higher due to recursive sorting within partitions
        assert self.engine.comparison_count >= 3

        # Verify that oracle was called (exact order may vary due to recursion)
        assert self.oracle.compare.call_count >= 3
        assert self.tracker.add_comparison.call_count >= 3

    @patch('serum_evolver.src.ranking.display_utils.create_ranking_table')
    def test_adaptive_quicksort_with_console(self, mock_create_table):
        """Test sorting with console output."""
        items = ['item1', 'item2']
        console = Mock(spec=Console)

        # Mock oracle response
        self.oracle.compare.return_value = True

        # Mock tracker ranking
        self.tracker.get_simple_ranking.return_value = [('item2', 1), ('item1', 2)]

        # Mock table creation
        mock_table = Mock()
        mock_create_table.return_value = mock_table

        result = self.engine.adaptive_quicksort(items, console)

        assert result == ['item1', 'item2']

        # Verify console interactions
        console.clear.assert_called_once()
        console.print.assert_called_once_with(mock_table)

        # Verify table creation
        mock_create_table.assert_called_once_with(
            [('item2', 1), ('item1', 2)],
            title="Live Ranking (after 1 comparisons)"
        )

        # Verify tracker ranking call
        self.tracker.get_simple_ranking.assert_called_once()

    @patch('serum_evolver.src.ranking.display_utils.create_ranking_table')
    def test_adaptive_quicksort_no_console(self, mock_create_table):
        """Test sorting without console output."""
        items = ['item1', 'item2']

        # Mock oracle response
        self.oracle.compare.return_value = True

        result = self.engine.adaptive_quicksort(items, None)

        assert result == ['item1', 'item2']

        # No table creation or tracker ranking should occur
        mock_create_table.assert_not_called()
        self.tracker.get_simple_ranking.assert_not_called()

    def test_adaptive_quicksort_recursive_sorting(self):
        """Test that recursive sorting works correctly."""
        items = ['d', 'b', 'e', 'a', 'c']

        # Mock oracle to implement consistent comparison
        # We'll simulate alphabetical ordering
        def mock_compare(item1, item2):
            return item1 > item2

        self.oracle.compare.side_effect = mock_compare

        result = self.engine.adaptive_quicksort(items)

        # Should be sorted alphabetically: a, b, c, d, e
        # The exact result depends on pivot choice and partitioning, but should be sorted
        assert result == ['a', 'b', 'c', 'd', 'e']  # Corrected expected result

        # Should have made some comparisons
        assert self.engine.comparison_count > 0
        assert self.oracle.compare.call_count > 0
        assert self.tracker.add_comparison.call_count > 0

    def test_adaptive_quicksort_comparison_counting(self):
        """Test that comparison counting works across multiple calls."""
        # First sort
        items1 = ['a', 'b']
        self.oracle.compare.return_value = True
        self.engine.adaptive_quicksort(items1)
        assert self.engine.comparison_count == 1

        # Second sort - count should accumulate
        items2 = ['c', 'd']
        self.oracle.compare.return_value = False
        self.engine.adaptive_quicksort(items2)
        assert self.engine.comparison_count == 2

    def test_adaptive_quicksort_preserves_input_list(self):
        """Test that input list is not modified."""
        original_items = ['item1', 'item2', 'item3']
        items = original_items.copy()

        # Mock oracle responses
        self.oracle.compare.side_effect = [True, False]

        result = self.engine.adaptive_quicksort(items)

        # Original list should be unchanged
        assert items == original_items
        # Result should be different (unless already sorted)
        assert result is not items

    def test_adaptive_quicksort_edge_case_all_equal(self):
        """Test sorting when all items are equal according to oracle."""
        items = ['same', 'same', 'same']

        # Oracle always returns False (items are equal)
        self.oracle.compare.return_value = False

        result = self.engine.adaptive_quicksort(items)

        # All items should end up in less partition, so reversed order
        assert len(result) == 3
        assert all(item == 'same' for item in result)
        # With recursive calls, there might be more comparisons than expected
        assert self.engine.comparison_count >= 2

    def test_adaptive_quicksort_pivot_selection(self):
        """Test that pivot is always the first item."""
        items = ['pivot', 'other1', 'other2']

        # Mock oracle responses
        self.oracle.compare.side_effect = [True, False]

        result = self.engine.adaptive_quicksort(items)

        # Verify that comparisons were made against the first item (pivot)
        for call_args in self.oracle.compare.call_args_list:
            # Second argument should always be the pivot
            assert call_args[0][1] == 'pivot'

    @patch('serum_evolver.src.ranking.display_utils.create_ranking_table')
    def test_adaptive_quicksort_multiple_console_updates(self, mock_create_table):
        """Test console updates for multiple comparisons."""
        items = ['pivot', 'item1', 'item2']
        console = Mock(spec=Console)

        # Mock oracle responses
        self.oracle.compare.side_effect = [True, False]

        # Mock tracker rankings
        self.tracker.get_simple_ranking.side_effect = [
            [('item1', 1), ('pivot', 2)],
            [('item1', 1), ('pivot', 2), ('item2', 3)]
        ]

        # Mock table creation
        mock_table = Mock()
        mock_create_table.return_value = mock_table

        result = self.engine.adaptive_quicksort(items, console)

        # Should have cleared and printed twice (once per comparison)
        assert console.clear.call_count == 2
        assert console.print.call_count == 2

        # Should have created two tables with different titles
        expected_calls = [
            ((([('item1', 1), ('pivot', 2)],), {'title': 'Live Ranking (after 1 comparisons)'})),
            ((([('item1', 1), ('pivot', 2), ('item2', 3)],), {'title': 'Live Ranking (after 2 comparisons)'}))
        ]
        assert mock_create_table.call_args_list == expected_calls
