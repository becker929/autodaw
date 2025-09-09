"""
Experiment management and artifact organization for SerumEvolver.

This module provides tools for organizing experiments, managing artifacts,
generating target audio, and tracking results across evolution runs.

Components:
- artifact_manager: Experiment organization and result management
- target_generator: Target audio generation and feature extraction
"""

from .artifact_manager import ArtifactManager
# from .target_generator import TargetAudioGenerator  # Temporarily disabled due to circular import

__all__ = [
    'ArtifactManager',
    # 'TargetAudioGenerator',  # Temporarily disabled
]
