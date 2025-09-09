# Serum Evolver: Core vs Legacy Components Analysis

## CORE COMPONENTS TO RETAIN

### 1. Genetics System (Flexible Serum FX Parameters)
**Location**: `src/genetics/`

#### Core Files:
- `genetics.py` - Solution class, GenomeToPhenotypeMapper, PopulationGenerator
  - **Purpose**: Flexible genetic representation for Serum parameters
  - **Key Features**:
    - Solution class maps to any Serum parameters (currently octave/fine)
    - GenomeToPhenotypeMapper converts genetic values to Serum VST parameter ranges (0.0-1.0)
    - Population generators with diverse initialization strategies
  - **Status**: ✅ KEEP - Core genetic algorithm foundation

- `config.py` - Configuration system for REAPER sessions and FX parameters
  - **Purpose**: JSON-based configuration for flexible parameter mapping
  - **Key Features**:
    - ParameterConfig allows any FX parameter specification
    - RenderConfig supports multiple tracks and FX chains
    - Extensible to any number of Serum parameters
  - **Status**: ✅ KEEP - Essential for parameter flexibility

- `reaper_integration.py` - ReaperExecutor class (PARTIAL KEEP)
  - **Purpose**: Execute REAPER sessions and collect rendered audio
  - **Key Features**:
    - ReaperExecutor handles REAPER subprocess execution
    - Session config file management
    - Audio file collection from renders
  - **Status**: ⚠️ PARTIAL KEEP - ReaperExecutor class only

### 2. Fitness Function (Configurable Librosa Features)
**Location**: `src/audio/oracle.py`, `src/ranking/`

#### Core Files:
- `oracle.py` - AudioComparisonOracle with librosa-based feature extraction
  - **Purpose**: Configurable audio comparison using librosa features
  - **Key Features**:
    - Fundamental frequency estimation using librosa.piptrack
    - Spectral centroid fallback for frequency analysis
    - Configurable noise levels and comparison strategies
  - **Status**: ✅ KEEP - Core fitness evaluation

- `population_ranker.py` - JSI-based fitness evaluation with dependency injection
  - **Purpose**: Converts JSI rankings to fitness values
  - **Key Features**:
    - GAPopulationRanker with composition pattern
    - JSIFitnessEvaluator for GA integration
    - Configurable fitness normalization (exponential, linear, inverse)
  - **Status**: ✅ KEEP - Core fitness system

### 3. PyMOO JSI Problem
**Location**: `src/genetics/jsi_problems.py`

#### Core Files:
- `jsi_problems.py` - JSIAudioOptimizationProblem
  - **Purpose**: PyMOO-compatible GA problem using JSI ranking
  - **Key Features**:
    - Integrates JSI ranking with pymoo optimization
    - Uses audio oracle for pairwise comparisons
    - Supports multiple target frequencies
    - Clean separation of concerns with dependency injection
  - **Status**: ✅ KEEP - Modern GA problem implementation

## LEGACY COMPONENTS TO REMOVE

### 1. Frequency Optimization (Legacy GA Problem)
**Location**: `src/genetics/ga_problem.py`, `src/genetics/main.py`

#### Legacy Files:
- `ga_problem.py` - FrequencyOptimizationProblem, TargetFrequencyProblem
  - **Issues**:
    - Direct frequency distance calculation instead of JSI ranking
    - Hardcoded to frequency-only optimization
    - Superseded by JSIAudioOptimizationProblem
  - **Status**: ❌ REMOVE - Replaced by JSI approach

- `main.py` - Demo scripts for frequency optimization
  - **Issues**:
    - Uses legacy ga_problem.py
    - Hardcoded to frequency optimization only
    - Command-line interface not needed for library
  - **Status**: ❌ REMOVE - Legacy demo code

- `audio_analysis.py` - FrequencyDistanceCalculator
  - **Issues**:
    - Direct distance calculation approach
    - Superseded by oracle-based comparisons
    - Complex multi-feature distance computation
  - **Status**: ❌ REMOVE - Replaced by oracle system

- `reaper_integration.py` - PARTIAL REMOVAL
  - **Keep**: ReaperExecutor class (used by JSI system)
  - **Remove**: ReaperGAIntegration, FitnessEvaluator classes
  - **Issues with removed parts**:
    - Tightly coupled to frequency optimization
    - Direct fitness evaluation instead of JSI ranking
  - **Status**: ⚠️ PARTIAL REMOVAL - Keep ReaperExecutor, remove GA integration classes

### 2. Demo and Experiment Scripts
**Location**: `src/demos/`, `experiment_scripts/`

#### Legacy Directories:
- `src/demos/` - All demo files
  - **Issues**: Demo code not needed for core library
  - **Status**: ❌ REMOVE - Not core functionality

- `experiment_scripts/` - All experiment scripts
  - **Issues**: Specific experiment scripts not part of core library
  - **Status**: ❌ REMOVE - Not core functionality

### 3. Supporting Legacy Systems
**Location**: Various locations

#### Files to Remove:
- `src/experiments/` - Experiment management (not core GA)
- `src/core/` - Empty or minimal core utilities
- Legacy test files testing removed components

## ARCHITECTURE DIAGRAM

```
RETAINED CORE ARCHITECTURE:

┌─────────────────────────────────────────────────────────────┐
│                    SERUM EVOLVER CORE                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌──────────────────┐               │
│  │   GENETICS      │    │   FITNESS        │               │
│  │                 │    │                  │               │
│  │ • Solution      │    │ • AudioOracle    │               │
│  │ • Mapper        │    │ • PopulationRank │               │
│  │ • PopGen        │    │ • JSIEvaluator   │               │
│  │ • Config        │    │ • FitnessCalc    │               │
│  └─────────────────┘    └──────────────────┘               │
│           │                       │                        │
│           └───────────┬───────────┘                        │
│                       │                                    │
│              ┌─────────────────┐                           │
│              │  PYMOO JSI      │                           │
│              │  PROBLEM        │                           │
│              │                 │                           │
│              │ • JSIAudioOpt   │                           │
│              │ • MultiTarget   │                           │
│              │ • Integration   │                           │
│              └─────────────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

REMOVED LEGACY SYSTEMS:

┌─────────────────────────────────────────────────────────────┐
│                    LEGACY TO REMOVE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ❌ FrequencyOptimizationProblem                            │
│  ❌ ReaperGAIntegration                                     │
│  ❌ FrequencyDistanceCalculator                             │
│  ❌ Demo scripts and experiments                            │
│  ❌ Direct fitness evaluation                               │
│  ❌ Hardcoded frequency optimization                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## SUMMARY

**KEEP (3 core systems):**
1. **Genetics**: Flexible Serum parameter mapping with Solution class
2. **Fitness**: Configurable librosa features via AudioOracle + JSI ranking
3. **PyMOO JSI**: Modern GA problem with dependency injection

**REMOVE (Legacy frequency optimization):**
1. **ga_problem.py** - Legacy direct distance GA problems
2. **main.py** - Legacy demo scripts
3. **audio_analysis.py** - Legacy direct distance calculation
4. **reaper_integration.py** - Legacy tightly-coupled integration
5. **demos/** - Demo code directory
6. **experiment_scripts/** - Experiment scripts directory
7. **experiments/** - Experiment management utilities

The core retained system provides a clean, flexible architecture for genetic optimization of any Serum parameters using JSI ranking with configurable librosa features.
