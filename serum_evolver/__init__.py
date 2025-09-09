"""
SerumEvolver: Evolutionary optimization for Serum synthesizer parameters.

A complete solution for evolving Serum synthesizer parameters using:
- Genetic algorithms (GA) with pymoo
- Just-Noticeable-Difference Sorting and Identification (JSI)
- Audio comparison oracles using librosa
- REAPER DAW integration for audio rendering
- Comprehensive experiment management and artifact organization
"""

# Import from src
from .src import *

__version__ = "1.0.0"
__author__ = "SerumEvolver Team"
