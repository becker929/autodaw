"""
Audio processing and comparison components for SerumEvolver.

This module handles audio analysis, comparison, and oracle-based fitness
evaluation using librosa for audio feature extraction.

Components:
- oracle: Audio comparison oracles for fitness evaluation
"""

from .oracle import (
    AudioComparisonOracle,
    FrequencyTargetOracle
)

__all__ = [
    'AudioComparisonOracle',
    'FrequencyTargetOracle',
]
