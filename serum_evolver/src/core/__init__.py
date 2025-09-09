"""
Core optimization components for SerumEvolver.

This module contains the high-level genetic algorithm problem definitions
that integrate JSI (Just-Noticeable-Difference Sorting and Identification)
with audio oracle comparisons.

Components:
- jsi_problems: JSI-enhanced GA problem definitions for audio optimization
"""

from ..genetics.jsi_problems import (
    JSIAudioOptimizationProblem,
    MultiTargetJSIOptimizationProblem
)

__all__ = [
    'JSIAudioOptimizationProblem',
    'MultiTargetJSIOptimizationProblem',
]
