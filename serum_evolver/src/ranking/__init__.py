"""
JSI ranking and comparison components for SerumEvolver.

This module provides Just-Noticeable-Difference Sorting and Identification (JSI)
functionality for ranking populations and making audio comparisons.

Components:
- comparison_oracle: Base comparison oracle interface
- ranking_tracker: Bradley-Terry model ranking tracker
- display_utils: Utilities for displaying ranking results
- population_ranker: JSI-based population ranking and fitness evaluation
"""

from .population_ranker import (
    JSIFitnessEvaluator,
    GAPopulationRanker
)

__all__ = [
    'JSIFitnessEvaluator',
    'GAPopulationRanker',
]
