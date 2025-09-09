"""
SerumEvolver core source code.

A modular system for evolutionary optimization of Serum synthesizer parameters
using genetic algorithms, Just-Noticeable-Difference Sorting and Identification (JSI),
and audio comparison oracles.

Core Modules:
- audio: Audio processing and comparison oracles using librosa
- genetics: Genetic algorithm implementation and REAPER integration
- ranking: JSI ranking and comparison components

JSI Problems are available via direct import:
    from serum_evolver.src.genetics.jsi_problems import JSIAudioOptimizationProblem
"""

# Import from core submodules
from .audio import *
from .genetics import *
from .ranking import *

# Re-export core functionality
__all__ = [
    # JSI Ranking System
    'JSIFitnessEvaluator',
    'GAPopulationRanker',

    # Audio Oracles (Librosa-based)
    'AudioComparisonOracle',
    'FrequencyTargetOracle',

    # Genetics Core
    'Solution',
    'GenomeToPhenotypeMapper',
    'PopulationGenerator',
    'SessionConfig',
    'RenderConfig',
    'create_basic_serum_render_config',
    'ReaperExecutor',
]
