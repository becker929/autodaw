"""
SerumEvolver core source code.

A modular system for evolutionary optimization of Serum synthesizer parameters
using genetic algorithms, Just-Noticeable-Difference Sorting and Identification (JSI),
and audio comparison oracles.

Modules:
- audio: Audio processing and comparison oracles
- genetics: Genetic algorithm implementation and REAPER integration
- ranking: JSI ranking and comparison components
- experiments: Experiment management and artifact organization
- demos: Demo functions and main orchestration
"""

# Import from submodules
from .audio import *
from .genetics import *
from .ranking import *
from .experiments import *
from .demos import *

# Re-export everything for convenience
__all__ = [
    # JSI-enhanced GA problems (import directly from genetics.jsi_problems)
    # 'JSIAudioOptimizationProblem',
    # 'MultiTargetJSIOptimizationProblem',

    # JSI Ranking
    'JSIFitnessEvaluator',
    'GAPopulationRanker',

    # Audio processing
    'AudioComparisonOracle',
    'FrequencyTargetOracle',

    # Genetics (from genetics module)
    'Solution',
    'GenomeToPhenotypeMapper',
    'PopulationGenerator',
    'SessionConfig',
    'RenderConfig',
    'create_basic_serum_render_config',
    'FrequencyDistanceCalculator',
    'ReaperExecutor',
    'FitnessEvaluator',
    'ReaperGAIntegration',
    'FrequencyOptimizationProblem',
    'TargetFrequencyProblem',

    # Experiments
    'ArtifactManager',
    # 'TargetAudioGenerator',  # Temporarily disabled

    # Demos
    'demo_jsi_audio_optimization',
    'demo_multi_target_optimization',
    'demo_comparison_oracle_accuracy',
    'run_full_demo_suite',
]
