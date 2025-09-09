"""
GA Frequency Demo - Genetic Algorithm optimization for REAPER frequency parameters.
"""

from .genetics import Solution, GenomeToPhenotypeMapper, PopulationGenerator
from .config import SessionConfig, RenderConfig, create_basic_serum_render_config
from .audio_analysis import FrequencyDistanceCalculator
from .reaper_integration import ReaperExecutor, FitnessEvaluator, ReaperGAIntegration
from .ga_problem import FrequencyOptimizationProblem, TargetFrequencyProblem
# JSI problems are available but not imported by default to avoid circular imports
# from .jsi_problems import JSIAudioOptimizationProblem, MultiTargetJSIOptimizationProblem

__version__ = "0.1.0"
__all__ = [
    "Solution",
    "GenomeToPhenotypeMapper",
    "PopulationGenerator",
    "SessionConfig",
    "RenderConfig",
    "create_basic_serum_render_config",
    "FrequencyDistanceCalculator",
    "ReaperExecutor",
    "FitnessEvaluator",
    "ReaperGAIntegration",
    "FrequencyOptimizationProblem",
    "TargetFrequencyProblem",
    # "JSIAudioOptimizationProblem",  # Available via direct import
    # "MultiTargetJSIOptimizationProblem"  # Available via direct import
]
