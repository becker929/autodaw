# Dead Code Analysis

## IDENTIFIED DEAD CODE

### 1. Unused Classes (0% Coverage)
- ❌ **`FitnessNormalizer`** (`src/ranking/fitness_normalizer.py`)
  - Never imported or used anywhere in the codebase
  - 32 statements, 0% coverage
  - Purpose: Fitness normalization utilities
  - **Status**: DEAD CODE - Remove entire file

- ❌ **`SimulatedOracle`** (`src/ranking/comparison_oracle.py`)
  - Only defined, never imported or used
  - Used in tests but not in core system
  - **Status**: DEAD CODE - Keep only for testing

- ❌ **`HumanOracle`** (`src/ranking/comparison_oracle.py`)
  - Only defined, never imported or used
  - Used in tests but not in core system
  - **Status**: DEAD CODE - Keep only for testing

- ❌ **`LoggingRankingDisplayer`** (`src/ranking/ranking_display.py`)
  - Only defined, never imported or used
  - **Status**: DEAD CODE - Remove class

### 2. Duplicate Classes
- ⚠️ **`JSIAdaptiveQuicksort`** - Defined in TWO files:
  - `src/ranking/jsi_sorter.py` (USED - imported by population_ranker.py)
  - `src/ranking/jsi_engine.py` (UNUSED - different signature, not imported)
  - **Status**: Remove `jsi_engine.py` version, keep `jsi_sorter.py`

### 3. Unused Modules
- ❌ **`src/ranking/display_utils.py`**
  - 24 statements, 21% coverage
  - Only used by `ranking_display.py` and `jsi_engine.py` (which is dead)
  - Functions: `create_ranking_table`, `format_solution_info`, etc.
  - **Status**: Potentially dead if jsi_engine.py is removed

### 4. Unused Display Classes
- ⚠️ **`SilentRankingDisplayer`** - Used as default in jsi_sorter.py (KEEP)
- ❌ **`LoggingRankingDisplayer`** - Never imported (REMOVE)

## RECOMMENDED REMOVALS

### Files to Delete:
1. `src/ranking/fitness_normalizer.py` - Completely unused
2. `src/ranking/jsi_engine.py` - Duplicate of jsi_sorter functionality

### Classes to Remove:
1. `LoggingRankingDisplayer` from `src/ranking/ranking_display.py`
2. `SimulatedOracle` and `HumanOracle` from `src/ranking/comparison_oracle.py` (keep in tests only)

### Potential Cleanup:
1. Review `src/ranking/display_utils.py` usage after removing jsi_engine.py
2. Clean up any remaining imports of removed classes

## IMPACT ANALYSIS

**Files Affected:**
- Tests may reference some of these classes
- __init__.py files may export unused classes
- Coverage will improve by removing untested code

**Safe to Remove:**
- fitness_normalizer.py (0 imports)
- jsi_engine.py (0 imports)
- LoggingRankingDisplayer (0 imports)

**Keep for Tests:**
- SimulatedOracle, HumanOracle (used in test_comparison_oracle.py)
