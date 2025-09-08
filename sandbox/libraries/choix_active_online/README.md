# "Just Sort It" - Active Learning Ranking System

An interactive TUI application that implements the "Just Sort It" approach to active learning for pairwise ranking. Uses adaptive quicksort with live Bradley-Terry model updates for efficient ranking discovery.

**✅ FULLY IMPLEMENTED**: Complete working system with both simulated and human-in-the-loop oracles.

## Overview

This project implements the "Just Sort It" active learning architecture:

1. **Adaptive Quicksort**: Runs continuous quicksort iterations on the item set
2. **Comparison Oracles**: Simulated (demo) or Human (interactive) comparison providers
3. **Live Bradley-Terry Updates**: Model refits after every single comparison
4. **Session Management**: Start/stop learning with comprehensive statistics
5. **Real-time TUI**: Live ranking updates and learning progress visualization

## Architecture Components

### 🎯 Comparison Oracles
- **SimulatedOracle**: Ground truth with configurable noise for demonstrations
- **HumanOracle**: Interactive TUI prompts for real human comparisons
- **Pluggable Design**: Easy to add new oracle types (e.g., crowdsourcing, ML models)

### ⚡ Active Learning Engine
- **Adaptive Quicksort**: Standard quicksort algorithm with session checking
- **Continuous Iterations**: Runs complete O(n log n) sorts until stopped
- **Comparison Recording**: Each comparison immediately updates the live model
- **Threading**: Background learning with responsive UI

### 📊 Real-time Feedback
- Live ranking updates after each comparison
- Model confidence and uncertainty metrics
- Comparison history and activity log
- Bootstrap-based uncertainty estimation

### 🎯 Information Gain Optimization
- Expected information gain calculations for pair selection
- Entropy-based query optimization
- Intelligent avoidance of recently compared pairs

### 💻 Rich TUI Interface
- Clean, organized layout with multiple information panels
- Keyboard and mouse interaction
- Real-time statistics display
- Activity logging with rich formatting

## Installation

```bash
cd choix_active_online_demo
uv sync
```

## Usage

**Note**: The TUI application runs the complete "Just Sort It" architecture with both simulated and human oracles.

### Basic Usage

Run with default programming language items:

```bash
uv run python main.py
```

### Custom Items

Provide your own items to rank:

```bash
uv run python main.py "Pizza" "Burgers" "Tacos" "Sushi" "Pasta"
```

### Interface Guide

The TUI is organized into several panels:

1. **Comparison Panel** (top): Shows current pair and selection buttons
2. **Statistics Panel** (middle-left): Displays learning metrics
3. **Ranking Panel** (middle-right): Shows current item ranking with uncertainties
4. **Activity Log** (bottom): Records all comparisons and system messages

#### Controls
- Click item buttons to indicate preference
- Click "Skip" to get a different pair
- Press `q` to quit
- Use mouse or keyboard navigation

## Active Learning Algorithm

### Query Selection Process

1. **Information Gain Calculation**:
   ```
   Information Gain = Outcome Uncertainty × (1 + Item Uncertainty)
   ```

2. **Outcome Uncertainty**: Higher when win probability is close to 50%
3. **Item Uncertainty**: Based on bootstrap estimation of strength variance

### Learning Stages

- **Early Stage** (< 10 comparisons): Focus on diversity sampling
- **Middle Stage** (10-50 comparisons): Balance uncertainty and diversity
- **Late Stage** (> 50 comparisons): Focus on uncertainty sampling

### Model Updates

The Bradley-Terry model updates after each comparison using:
- **ILSR Algorithm**: Iterative Luce Spectral Ranking for parameter estimation
- **Bootstrap Sampling**: Uncertainty quantification via resampling
- **Online Learning**: Immediate model updates without retraining from scratch

## Implementation Details

### Core Components

#### `ActiveBradleyTerryLearner`
- Manages the Bradley-Terry model and comparison data
- Implements multiple active learning strategies
- Provides uncertainty estimation and statistics

#### `RankingApp` (TUI)
- Textual-based terminal user interface
- Real-time display updates
- Interactive comparison collection

### Active Learning Strategies

#### Uncertainty Sampling
Selects pairs with highest expected information gain:
```python
def select_next_query_uncertainty(self) -> Tuple[str, str]:
    best_gain = -1
    for item1, item2 in combinations(self.item_names, 2):
        gain = self.calculate_expected_information_gain(item1, item2)
        if gain > best_gain:
            best_gain = gain
            best_pair = (item1, item2)
    return best_pair
```

#### Diversity Sampling
Focuses on items from different ranking regions:
- Early stage: Compare top vs bottom ranked items
- Later stage: Fill gaps in middle rankings

#### Adaptive Strategy
Combines approaches based on learning progress:
- Adapts strategy based on number of comparisons made
- Balances exploration (diversity) and exploitation (uncertainty)

### Uncertainty Estimation

Uses bootstrap resampling to estimate parameter uncertainty:

```python
def _estimate_uncertainties(self, n_bootstrap: int = 50):
    bootstrap_strengths = []
    for _ in range(n_bootstrap):
        # Resample comparisons
        bootstrap_comparisons = resample(self.comparisons)
        # Refit model
        bootstrap_strength = choix.ilsr_pairwise(self.n_items, bootstrap_comparisons)
        bootstrap_strengths.append(bootstrap_strength)
    # Calculate standard deviation
    self.strength_uncertainties = np.std(bootstrap_strengths, axis=0)
```

## Example Session

```
🏆 Active Learning Ranking System 🏆

Current Comparison:
Which is better: Python vs JavaScript?
Model predicts: Python (52%) vs JavaScript (48%)

[Python] [JavaScript] [Skip]

Statistics:
Comparisons Made: 15
Items: 10
Model Status: Fitted
Ranking Confidence: 78%
Top Item: Python
Most Uncertain: Go

Current Ranking:
1. Python    (2.145 ±0.234)
2. Rust      (1.892 ±0.187)
3. JavaScript (1.654 ±0.298)
4. TypeScript (1.432 ±0.312)
...

Activity Log:
✅ Comparison #15: Python > JavaScript
🎯 Next pair selected: Go vs Swift (high information gain)
📈 Ranking confidence improved: 74% → 78%
```

## Testing

Run the test suite:

```bash
uv run pytest tests/ -v
```

Tests cover:
- Active learning algorithm correctness
- Query selection strategies
- Model update mechanisms
- Uncertainty estimation
- Statistics generation
- Edge case handling

## Mathematical Foundation

### Bradley-Terry Model

The probability that item $i$ beats item $j$ is:

$$P(i \text{ beats } j) = \frac{\pi_i}{\pi_i + \pi_j}$$

where $\pi_i$ is the strength parameter for item $i$.

### Information Gain

Expected information gain for querying pair $(i,j)$:

$$\text{IG}(i,j) = H(\text{outcome}) \times (1 + U(i) + U(j))$$

where:
- $H(\text{outcome}) = -p \log_2 p - (1-p) \log_2 (1-p)$ is outcome entropy
- $U(i)$ is the uncertainty in item $i$'s strength estimate
- $p = P(i \text{ beats } j)$ is the predicted win probability

### Uncertainty Quantification

Item strength uncertainty estimated via bootstrap:

$$\hat{\sigma}_i = \text{std}(\{\hat{\pi}_i^{(b)}\}_{b=1}^B)$$

where $\hat{\pi}_i^{(b)}$ is the strength estimate from bootstrap sample $b$.

## Dependencies

- `numpy`: Numerical computations
- `scipy`: Statistical functions
- `choix`: Bradley-Terry model implementation
- `pandas`: Data handling
- `rich`: Rich text formatting
- `textual`: Modern TUI framework

## Future Enhancements

- **Multi-objective Ranking**: Handle multiple ranking criteria
- **Batch Active Learning**: Select multiple pairs simultaneously
- **Transfer Learning**: Leverage rankings from related domains
- **Preference Elicitation**: Handle uncertain or inconsistent user preferences
- **Export/Import**: Save and load ranking sessions

## References

1. Bradley, R. A., & Terry, M. E. (1952). Rank analysis of incomplete block designs
2. Settles, B. (2009). Active Learning Literature Survey
3. Maystre, L., & Grossglauser, M. (2015). Fast and accurate inference of Plackett–Luce models
