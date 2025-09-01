# GA Frequency Demo

A genetic algorithm system for optimizing frequency parameters in REAPER using the Serum VST synthesizer.

## Overview

This project integrates genetic algorithms with REAPER audio rendering to optimize synthesizer parameters based on audio analysis. The system:

1. **Generates populations** of parameter combinations (octave and fine tuning)
2. **Maps genetic solutions** to REAPER session configurations
3. **Executes REAPER** to render audio with different parameter sets
4. **Analyzes rendered audio** using librosa frequency domain analysis
5. **Evolves parameters** using pymoo genetic algorithms to minimize frequency distance

## Architecture

### Core Components

- **`Solution`**: Genetic algorithm genome representing octave and fine tuning parameters
- **`GenomeToPhenotypeMapper`**: Converts genetic solutions to REAPER render configurations
- **`SessionConfig`/`RenderConfig`**: Data structures compatible with Lua session manager
- **`FrequencyDistanceCalculator`**: Audio analysis using librosa spectral features
- **`ReaperExecutor`**: Manages REAPER session execution and audio collection
- **`FitnessEvaluator`**: Evaluates solution fitness based on rendered audio
- **`FrequencyOptimizationProblem`**: Custom pymoo problem for GA optimization

### Data Flow

```
Population → RenderConfigs → SessionConfig → REAPER → Audio → Analysis → Fitness → Evolution
```

## Installation

```bash
# Clone and navigate to demo directory
cd ga_frequency_demo

# Install dependencies with uv
uv sync

# Install development dependencies for testing
uv add --dev pytest pytest-cov
```

## Dependencies

- **pymoo**: Genetic algorithm framework
- **librosa**: Audio analysis and feature extraction
- **numpy**: Numerical computing
- **soundfile**: Audio file I/O
- **pytest**: Testing framework (dev)

## Usage

### Basic Demo

```python
from ga_frequency_demo.main import demo_basic_optimization

# Run basic frequency optimization
result = demo_basic_optimization()
```

### Target Frequency Demo

```python
from ga_frequency_demo.main import demo_target_frequency

# Optimize for specific frequency ratio (e.g., one octave up)
result = demo_target_frequency()
```

### Command Line Interface

```bash
# Basic optimization
uv run python -m ga_frequency_demo.main --demo basic --pop-size 10 --generations 5

# Target frequency optimization
uv run python -m ga_frequency_demo.main --demo target --target-ratio 2.0 --pop-size 10 --generations 5
```

### Integration Demo

```bash
# Run complete integration test
uv run python demo.py
```

## Configuration

### Genetic Algorithm Parameters

- **Population Size**: Number of individuals per generation (default: 10)
- **Generations**: Number of evolution cycles (default: 5)
- **Parameter Bounds**:
  - Octave: -2.0 to +2.0 (±2 octaves)
  - Fine: -1.0 to +1.0 (±1 semitone approximate)

### Audio Analysis

- **Sample Rate**: 44.1 kHz
- **FFT Size**: 2048 samples
- **Hop Length**: 512 samples
- **Features**: Spectral centroid, bandwidth, rolloff, MFCCs, chroma

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=ga_frequency_demo

# Run specific test modules
uv run pytest tests/test_genetics.py -v
```

## Project Structure

```
ga_frequency_demo/
├── ga_frequency_demo/          # Main package
│   ├── __init__.py
│   ├── config.py              # REAPER configuration classes
│   ├── genetics.py            # GA solutions and population generation
│   ├── audio_analysis.py      # Librosa-based audio analysis
│   ├── reaper_integration.py  # REAPER execution and fitness evaluation
│   ├── ga_problem.py          # Custom pymoo optimization problems
│   └── main.py                # Demo scripts and CLI
├── tests/                     # Unit tests
│   ├── test_config.py
│   ├── test_genetics.py
│   ├── test_audio_analysis.py
│   └── test_integration.py
├── demo.py                    # Integration demo script
├── README.md
└── pyproject.toml            # Project configuration
```

## Integration with REAPER Project

The system integrates with the main REAPER project located at `../reaper/`. It expects:

- **Session configs**: Written to `reaper/session-configs/`
- **REAPER execution**: Via `uv run python main.py` in reaper directory
- **Audio output**: Collected from `reaper/renders/`
- **MIDI files**: Uses `test_melody.mid` from reaper project

## Frequency Mapping

The system maps genetic parameters to Serum VST parameters:

- **Octave**: Maps [-2, 2] → [0, 1] for "A Octave" parameter
- **Fine**: Maps [-1, 1] → [0, 1] for "A Fine" parameter

Frequency ratio calculation: `ratio = 2^octave × 2^(fine/12)`

## Fitness Function

Multi-component fitness based on spectral analysis:

1. **Spectral Centroid**: Brightness/timbre matching
2. **Spectral Bandwidth**: Harmonic content similarity
3. **Spectral Rolloff**: High-frequency energy distribution
4. **MFCCs**: Timbral characteristics (13 coefficients)
5. **Chroma**: Harmonic content (12-tone representation)
6. **Magnitude Spectrum**: Overall spectral shape

## Performance Considerations

- **Cleanup**: Old render directories are automatically cleaned up
- **Timeout**: REAPER execution has configurable timeout (default: 120s)
- **Parallel**: Tests run in parallel where possible
- **Memory**: Audio files are loaded on-demand during evaluation

## Troubleshooting

### Common Issues

1. **REAPER not found**: Ensure `../reaper/` directory exists with proper structure
2. **Audio analysis errors**: Check that rendered audio files are valid WAV format
3. **Timeout errors**: Increase timeout for complex REAPER sessions
4. **Parameter bounds**: Ensure genetic solutions stay within valid VST parameter ranges

### Debug Output

The system provides detailed logging during execution:
- Generation statistics (best/worst/average fitness)
- REAPER execution status and timing
- Audio file collection and analysis results
- Parameter mapping verification

## Extension Points

The system is designed for extensibility:

- **New Parameters**: Add more VST parameters to `Solution` class
- **Different VSTs**: Modify config classes for other synthesizers
- **Audio Features**: Extend `FrequencyDistanceCalculator` with new analysis methods
- **Optimization**: Try different pymoo algorithms (NSGA-II, CMA-ES, etc.)
- **Multi-objective**: Use `MultiObjectiveFrequencyProblem` for Pareto optimization
