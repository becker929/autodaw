# Bradley-Terry Algorithm Demonstration

A comprehensive demonstration of the Bradley-Terry model for pairwise comparisons using simulated data.

## Overview

The Bradley-Terry model is a statistical method for analyzing pairwise comparison data. It estimates the "strength" or "skill" of items based on the outcomes of head-to-head comparisons. This project demonstrates the algorithm using simulated data and provides visualizations to understand how well the model recovers true item rankings.

## Mathematical Foundation

The Bradley-Terry model assumes that the probability of item $i$ beating item $j$ is:

$$P(i \text{ beats } j) = \frac{\pi_i}{\pi_i + \pi_j}$$

where $\pi_i$ and $\pi_j$ are the "strength" parameters for items $i$ and $j$ respectively.

## Features

- **Simulated Data Generation**: Creates realistic pairwise comparison data with known ground truth
- **Model Fitting**: Uses the `choix` library to estimate item strengths via Iterative Luce Spectral Ranking (ILSR)
- **Comprehensive Evaluation**: Calculates multiple accuracy metrics including Kendall's τ and top-k accuracy
- **Rich Visualizations**: Multiple plot types to understand model performance
- **Convergence Analysis**: Shows how accuracy improves with more comparison data

## Installation

```bash
cd choix_demo
uv sync
```

## Usage

### Basic Demo

Run the complete demonstration:

```bash
uv run python demo.py
```

### Programmatic Usage

```python
from choix_demo.bradley_terry import BradleyTerryDemo
from choix_demo.visualization import BradleyTerryVisualizer

# Create demo with 6 items
demo = BradleyTerryDemo(n_items=6, random_seed=42)

# Run complete demonstration with 300 comparisons
results = demo.run_full_demo(n_comparisons=300)

# Create visualizations
visualizer = BradleyTerryVisualizer()
visualizer.plot_strength_comparison(results)
visualizer.plot_ranking_comparison(results)
```

### Step-by-Step Usage

```python
# Initialize demo
demo = BradleyTerryDemo(n_items=5, random_seed=42)

# Generate comparison data
comparisons = demo.generate_comparison_data(n_comparisons=200)

# Fit the Bradley-Terry model
estimated_strengths = demo.fit_bradley_terry_model()

# Get rankings and metrics
rankings = demo.get_rankings()
metrics = demo.calculate_accuracy_metrics()

print(f"Kendall's τ: {metrics['kendall_tau']:.3f}")
print(f"Top-1 accuracy: {metrics['top_1_accuracy']:.3f}")
```

## Visualization Types

### 1. Strength Comparison
- Bar chart comparing true vs estimated item strengths
- Scatter plot showing correlation between true and estimated values

### 2. Comparison Matrix
- Heatmap showing win-loss records between all pairs of items
- Useful for understanding the comparison data structure

### 3. Ranking Comparison
- Line plot showing how estimated rankings compare to true rankings
- Bar chart of top-k accuracy for different values of k

### 4. Convergence Analysis
- Shows how ranking accuracy improves with more comparison data
- Plots Kendall's τ and top-1 accuracy vs number of comparisons

## Evaluation Metrics

### Kendall's τ (Tau)
Measures rank correlation between true and estimated rankings. Values range from -1 (perfect disagreement) to +1 (perfect agreement).

### Top-k Accuracy
Fraction of the true top-k items that are correctly identified in the estimated top-k. Perfect score is 1.0.

### Comparison Matrix
Shows the win-loss record between all pairs of items, providing insight into the comparison data structure.

## Example Results

A typical run with 8 items and 200 comparisons might produce:

```
Bradley-Terry Model Demonstration Results
========================================

Dataset Information:
- Number of items: 8
- Number of comparisons: 200

True Ranking:
1. Item_07, 2. Item_06, 3. Item_05, 4. Item_04, 5. Item_03, 6. Item_02, 7. Item_01, 8. Item_00

Estimated Ranking:
1. Item_07, 2. Item_06, 3. Item_04, 4. Item_05, 5. Item_03, 6. Item_02, 7. Item_01, 8. Item_00

Accuracy Metrics:
- Kendall's τ: 0.929 (p-value: 1.39e-04)
- Top-1 accuracy: 1.00
- Top-2 accuracy: 1.00
- Top-3 accuracy: 0.67
```

## Algorithm Details

The demonstration uses the Iterative Luce Spectral Ranking (ILSR) algorithm implemented in the `choix` library. This is an efficient method for maximum likelihood estimation in the Bradley-Terry model.

### Key Steps:
1. **Data Generation**: Simulate pairwise comparisons based on true item strengths
2. **Model Fitting**: Use ILSR to estimate item strengths from comparison outcomes
3. **Evaluation**: Compare estimated rankings against ground truth using multiple metrics
4. **Visualization**: Generate plots to understand model performance

## Testing

Run the test suite:

```bash
uv run pytest tests/
```

The tests cover:
- Proper initialization and data generation
- Model fitting and ranking calculation
- Error handling for edge cases
- Reproducibility with fixed random seeds
- Accuracy metric calculations

## Dependencies

- `numpy`: Numerical computations
- `pandas`: Data manipulation
- `matplotlib`: Plotting and visualization
- `seaborn`: Statistical plotting
- `scipy`: Statistical functions
- `choix`: Bradley-Terry model implementation

## References

1. Bradley, R. A., & Terry, M. E. (1952). Rank analysis of incomplete block designs: I. The method of paired comparisons. *Biometrika*, 39(3/4), 324-345.

2. Maystre, L., & Grossglauser, M. (2015). Fast and accurate inference of Plackett–Luce models. *Advances in neural information processing systems*, 28.

3. The `choix` library: https://github.com/lucasmaystre/choix
