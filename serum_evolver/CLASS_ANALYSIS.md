# Class-by-Class Analysis: Keep vs Remove

## CLASSES NEEDED FOR CORE FUNCTIONALITY

### JSI Problem (Entry Point)
- ✅ `JSIAudioOptimizationProblem` - Main pymoo problem class
- ✅ `MultiTargetJSIOptimizationProblem` - Multi-target variant

### Genetics System
- ✅ `Solution` - Genetic representation
- ✅ `GenomeToPhenotypeMapper` - Maps genes to Serum parameters
- ✅ `PopulationGenerator` - Creates initial populations

### Configuration System
- ✅ `SessionConfig` - REAPER session configuration
- ✅ `RenderConfig` - Individual render configuration
- ✅ `ParameterConfig` - FX parameter specification
- ✅ `TrackConfig` - Track configuration
- ✅ `FxConfig` - FX plugin configuration
- ✅ `RenderOptions` - Render settings

### REAPER Integration
- ✅ `ReaperExecutor` - Executes REAPER sessions, collects audio

### Fitness/Ranking System
- ✅ `AudioComparisonOracle` - Librosa-based audio comparison
- ✅ `FrequencyTargetOracle` - Target audio comparison
- ✅ `ComparisonOracle` - Base oracle interface
- ✅ `GAPopulationRanker` - JSI-based population ranking
- ✅ `JSIFitnessEvaluator` - Converts rankings to fitness
- ✅ `JSIAdaptiveQuicksort` - JSI sorting algorithm
- ✅ `FallbackSorter` - Fallback when JSI not applicable
- ✅ `SimpleRankingTracker` - Tracks comparison results
- ✅ `AudioPathMatcher` - Maps solution IDs to audio paths
- ✅ `FitnessCalculator` - Converts rankings to fitness values
- ✅ `RankingInfoBuilder` - Builds ranking statistics

### Display System (Optional but Used)
- ✅ `RankingDisplayer` - Interface for ranking display
- ✅ `LiveRankingDisplayer` - Shows live ranking updates
- ✅ `SilentRankingDisplayer` - No-op displayer

## CLASSES NOT NEEDED (LEGACY)

### Legacy GA Problems
- ❌ `FrequencyOptimizationProblem` - Uses direct distance, not JSI
- ❌ `TargetFrequencyProblem` - Uses direct distance, not JSI
- ❌ `MultiObjectiveFrequencyProblem` - Uses direct distance, not JSI

### Legacy Integration
- ❌ `ReaperGAIntegration` - Tightly coupled to frequency optimization
- ❌ `FitnessEvaluator` (from reaper_integration.py) - Direct fitness evaluation

### Legacy Audio Analysis
- ❌ `FrequencyDistanceCalculator` - Direct distance calculation, replaced by oracle

### Demo/Experiment Classes
- ❌ All classes in `src/demos/` - Demo code not core functionality
- ❌ All classes in `src/experiments/` - Experiment management not core GA

### Unused Utilities
- ❌ `FitnessNormalizer` - Not used by core system
- ❌ `SimulatedOracle` - Not used by core system
- ❌ `HumanOracle` - Not used by core system

## SUMMARY

**KEEP: 23 classes** (Core JSI + genetics + config + REAPER integration)
**REMOVE: 30+ classes** (Legacy frequency optimization + demos + experiments)

The core system is: JSI Problem → Genetics → REAPER Executor → Audio Oracle → JSI Ranking → Fitness
