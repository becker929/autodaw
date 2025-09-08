"""Visualization utilities for Bradley-Terry demonstration."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import seaborn as sns


class BradleyTerryVisualizer:
    """Visualization tools for Bradley-Terry model results."""

    def __init__(self, figsize: tuple = (12, 8)):
        """Initialize the visualizer.

        Args:
            figsize: Default figure size for plots
        """
        self.figsize = figsize
        plt.style.use('default')

    def plot_strength_comparison(self, results: Dict[str, Any],
                               save_path: Optional[str] = None) -> None:
        """Plot true vs estimated item strengths.

        Args:
            results: Results from BradleyTerryDemo.run_full_demo()
            save_path: Optional path to save the plot
        """
        rankings = results['rankings']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize)

        # Plot 1: Bar chart comparison
        x = np.arange(len(rankings['true_ranking']))
        width = 0.35

        ax1.bar(x - width/2, rankings['true_strengths'], width,
                label='True Strengths', alpha=0.8, color='blue')
        ax1.bar(x + width/2, rankings['estimated_strengths'], width,
                label='Estimated Strengths', alpha=0.8, color='red')

        ax1.set_xlabel('Items (ranked by true strength)')
        ax1.set_ylabel('Strength')
        ax1.set_title('True vs Estimated Item Strengths')
        ax1.set_xticks(x)
        ax1.set_xticklabels(rankings['true_ranking'], rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Scatter plot
        ax2.scatter(rankings['true_strengths'], rankings['estimated_strengths'],
                   alpha=0.7, s=100)

        # Add diagonal line for perfect correlation
        min_val = min(min(rankings['true_strengths']), min(rankings['estimated_strengths']))
        max_val = max(max(rankings['true_strengths']), max(rankings['estimated_strengths']))
        ax2.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5,
                label='Perfect Correlation')

        ax2.set_xlabel('True Strengths')
        ax2.set_ylabel('Estimated Strengths')
        ax2.set_title('True vs Estimated Strengths Correlation')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Add correlation coefficient
        corr = np.corrcoef(rankings['true_strengths'], rankings['estimated_strengths'])[0, 1]
        ax2.text(0.05, 0.95, f'Correlation: {corr:.3f}',
                transform=ax2.transAxes, bbox=dict(boxstyle="round", facecolor='wheat'))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_comparison_matrix(self, results: Dict[str, Any],
                              save_path: Optional[str] = None) -> None:
        """Plot the comparison matrix as a heatmap.

        Args:
            results: Results from BradleyTerryDemo.run_full_demo()
            save_path: Optional path to save the plot
        """
        comparison_matrix = results['comparison_matrix']

        plt.figure(figsize=self.figsize)

        # Create heatmap
        sns.heatmap(comparison_matrix, annot=True, fmt='d', cmap='Blues',
                   cbar_kws={'label': 'Number of Wins'})

        plt.title('Pairwise Comparison Matrix\n(Rows beat Columns)')
        plt.xlabel('Loser')
        plt.ylabel('Winner')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_ranking_comparison(self, results: Dict[str, Any],
                               save_path: Optional[str] = None) -> None:
        """Plot true vs estimated rankings.

        Args:
            results: Results from BradleyTerryDemo.run_full_demo()
            save_path: Optional path to save the plot
        """
        rankings = results['rankings']
        accuracy_metrics = results['accuracy_metrics']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize)

        # Plot 1: Ranking comparison
        items = rankings['true_ranking']
        true_positions = list(range(1, len(items) + 1))
        estimated_positions = [rankings['estimated_ranking'].index(item) + 1 for item in items]

        ax1.plot(true_positions, estimated_positions, 'bo-', markersize=8, linewidth=2)
        ax1.plot([1, len(items)], [1, len(items)], 'k--', alpha=0.5,
                label='Perfect Ranking')

        ax1.set_xlabel('True Ranking Position')
        ax1.set_ylabel('Estimated Ranking Position')
        ax1.set_title('Ranking Position Comparison')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(range(1, len(items) + 1))
        ax1.set_yticks(range(1, len(items) + 1))

        # Add Kendall's tau
        tau = accuracy_metrics['kendall_tau']
        ax1.text(0.05, 0.95, f"Kendall's τ: {tau:.3f}",
                transform=ax1.transAxes, bbox=dict(boxstyle="round", facecolor='wheat'))

        # Plot 2: Top-k accuracy
        top_k_keys = [k for k in accuracy_metrics.keys() if k.startswith('top_') and k.endswith('_accuracy')]
        k_values = [int(k.split('_')[1]) for k in top_k_keys]
        accuracies = [accuracy_metrics[k] for k in top_k_keys]

        ax2.bar(k_values, accuracies, alpha=0.7, color='green')
        ax2.set_xlabel('Top-k')
        ax2.set_ylabel('Accuracy')
        ax2.set_title('Top-k Ranking Accuracy')
        ax2.set_ylim(0, 1.1)
        ax2.grid(True, alpha=0.3)

        # Add accuracy values on bars
        for i, (k, acc) in enumerate(zip(k_values, accuracies)):
            ax2.text(k, acc + 0.02, f'{acc:.2f}', ha='center', va='bottom')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_convergence_analysis(self, demo, comparison_counts: list = None,
                                 save_path: Optional[str] = None) -> None:
        """Analyze how estimation accuracy improves with more comparisons.

        Args:
            demo: BradleyTerryDemo instance
            comparison_counts: List of comparison counts to test
            save_path: Optional path to save the plot
        """
        if comparison_counts is None:
            comparison_counts = [10, 25, 50, 100, 200, 500]

        kendall_taus = []
        top_1_accuracies = []

        for n_comp in comparison_counts:
            try:
                results = demo.run_full_demo(n_comp)
                metrics = results['accuracy_metrics']
                kendall_taus.append(metrics['kendall_tau'])
                top_1_accuracies.append(metrics['top_1_accuracy'])
            except ValueError:
                # Model failed to converge with insufficient data
                kendall_taus.append(0.0)
                top_1_accuracies.append(1.0 / demo.n_items)  # Random guess

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize)

        # Plot 1: Kendall's tau vs number of comparisons
        ax1.plot(comparison_counts, kendall_taus, 'bo-', linewidth=2, markersize=8)
        ax1.set_xlabel('Number of Comparisons')
        ax1.set_ylabel("Kendall's τ")
        ax1.set_title('Ranking Correlation vs Sample Size')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)

        # Plot 2: Top-1 accuracy vs number of comparisons
        ax2.plot(comparison_counts, top_1_accuracies, 'ro-', linewidth=2, markersize=8)
        ax2.set_xlabel('Number of Comparisons')
        ax2.set_ylabel('Top-1 Accuracy')
        ax2.set_title('Top Item Identification vs Sample Size')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1.1)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def create_summary_report(self, results: Dict[str, Any]) -> str:
        """Create a text summary of the results.

        Args:
            results: Results from BradleyTerryDemo.run_full_demo()

        Returns:
            Formatted summary string
        """
        rankings = results['rankings']
        metrics = results['accuracy_metrics']

        report = f"""
Bradley-Terry Model Demonstration Results
========================================

Dataset Information:
- Number of items: {results['n_items']}
- Number of comparisons: {results['n_comparisons']}

True Ranking:
{', '.join(f'{i+1}. {item}' for i, item in enumerate(rankings['true_ranking']))}

Estimated Ranking:
{', '.join(f'{i+1}. {item}' for i, item in enumerate(rankings['estimated_ranking']))}

Accuracy Metrics:
- Kendall's τ: {metrics['kendall_tau']:.3f} (p-value: {metrics['kendall_p_value']:.3e})
"""

        # Add top-k accuracies
        for k in range(1, min(6, results['n_items'] + 1)):
            if f'top_{k}_accuracy' in metrics:
                acc = metrics[f'top_{k}_accuracy']
                report += f"- Top-{k} accuracy: {acc:.2f}\n"

        return report
