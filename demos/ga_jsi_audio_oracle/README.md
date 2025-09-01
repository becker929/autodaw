# GA + JSI + Audio Oracle Integration Demo

This demo integrates three powerful components for audio optimization:

1. **Genetic Algorithm (GA)** - Population-based optimization using pymoo
2. **Just Sort It (JSI)** - Adaptive quicksort algorithm for ranking with minimal comparisons
3. **Audio Oracle** - Librosa-based comparison system that evaluates audio proximity to target frequencies

## Overview

Instead of using direct frequency distance calculations for fitness evaluation, this demo creates an indirection through a simulated user ranking system. The workflow is:

1. **GA Population** → Generate parameter sets (octave, fine tuning)
2. **REAPER Rendering** → Convert parameters to audio files
3. **Audio Oracle** → Use librosa to determine which audio files are closer to target frequency
4. **JSI Ranking** → Efficiently rank the population using pairwise comparisons
5. **Fitness Assignment** → Convert JSI rankings to fitness values for GA

## Key Components

### AudioComparisonOracle
- Uses librosa for fundamental frequency estimation
- Compares audio files based on proximity to target frequency
- Supports configurable noise levels for realistic user simulation
- Can work with either target frequency values or target audio files

### JSI Integration
- Adapts the JSI adaptive quicksort to work with GA populations
- Efficiently ranks solutions using minimal audio comparisons
- Provides live ranking updates during optimization
- Maintains Bradley-Terry model for confidence estimation

### GA Problem Class
- Integrates REAPER rendering with JSI ranking
- Handles population evaluation through audio oracle comparisons
- Supports both single and multi-target frequency optimization
- Includes automatic cleanup of old render files

## Usage

### Basic Demo
```bash
cd demos/ga_jsi_audio_oracle
uv run python main.py
```

### Custom Configuration
```python
from pathlib import Path
from ga_jsi_audio_oracle.main import demo_jsi_audio_optimization

result = demo_jsi_audio_optimization(
    reaper_project_path=Path("../reaper"),
    target_frequency=440.0,  # A4 note
    n_generations=10,
    population_size=8,
    oracle_noise_level=0.05,  # 5% noise in decisions
    show_live_ranking=True
)
```

## Features

### Single Target Optimization
Optimize towards a specific frequency target:
- Target frequency in Hz
- Configurable oracle noise level
- Live JSI ranking display
- Automatic render cleanup

### Multi-Target Optimization
Optimize towards multiple frequency targets with rotation:
- List of target frequencies
- Automatic target switching every N generations
- Explores diverse frequency space

### Oracle Accuracy Analysis
Evaluate oracle performance at different noise levels:
- Test synthetic frequency data
- Measure decision accuracy
- Analyze noise impact on ranking quality

## Dependencies

- **pymoo**: Genetic algorithm framework
- **librosa**: Audio analysis and feature extraction
- **choix**: Bradley-Terry model implementation
- **rich**: Terminal UI for live ranking display
- **numpy**: Numerical computations
- **soundfile**: Audio file I/O

## Integration Points

This demo builds on:
- `../choix_active_online/` - JSI algorithm and ranking components
- `../pymoo_ga_freq_reaper/` - GA problem structure and REAPER integration
- `../../reaper/` - REAPER project for audio rendering

## Output

The demo generates:
- Rendered audio files in `reaper/renders/`
- Live ranking displays during optimization
- Optimization statistics and best solution information
- JSI comparison counts and confidence metrics

## Technical Details

### Audio Analysis
- Fundamental frequency estimation using librosa.piptrack
- Spectral centroid fallback for robust frequency detection
- Weighted pitch extraction using magnitude information
- Caching system for efficient repeated audio loading

### Ranking Algorithm
- JSI adaptive quicksort with audio-based comparisons
- Bradley-Terry model for strength estimation
- Confidence calculation based on comparison density
- Fallback ranking for insufficient data cases

### Fitness Conversion
- Exponential decay from rank to fitness values
- Higher ranks receive lower fitness (minimization problem)
- Penalty fitness for solutions without valid audio renders
- Support for multiple normalization strategies

## Performance

- Small populations (4-8 individuals) for quick demos
- Efficient audio caching to avoid repeated I/O
- Periodic cleanup of old render directories
- Live ranking updates every 5 comparisons

This integration demonstrates how user preference models (simulated through audio analysis) can be incorporated into genetic algorithm optimization, providing a more realistic approach to audio parameter optimization than direct mathematical fitness functions.
