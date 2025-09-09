"""
Demo functions and main orchestration for SerumEvolver.

This module contains the main demo functions that showcase the capabilities
of the SerumEvolver system, including JSI optimization, multi-target
optimization, and oracle accuracy analysis.

Components:
- main: Main orchestration and demo functions
"""

from .main import (
    demo_jsi_audio_optimization,
    demo_multi_target_optimization,
    demo_comparison_oracle_accuracy,
    run_full_demo_suite
)

__all__ = [
    'demo_jsi_audio_optimization',
    'demo_multi_target_optimization',
    'demo_comparison_oracle_accuracy',
    'run_full_demo_suite',
]
