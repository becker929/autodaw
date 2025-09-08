#!/usr/bin/env python3
"""Simple example of Bradley-Terry algorithm without GUI plots."""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

from choix_demo.bradley_terry import BradleyTerryDemo
from choix_demo.visualization import BradleyTerryVisualizer


def main():
    """Run a simple Bradley-Terry demonstration."""
    print("Bradley-Terry Algorithm - Simple Example")
    print("=======================================")

    # Create demo with 6 items
    demo = BradleyTerryDemo(n_items=6, random_seed=42)

    print(f"\nTrue item strengths: {demo.true_strengths}")
    print(f"Item names: {demo.item_names}")

    # Run demonstration with different numbers of comparisons
    for n_comp in [50, 100, 200]:
        print(f"\n--- Results with {n_comp} comparisons ---")

        try:
            results = demo.run_full_demo(n_comparisons=n_comp)
            rankings = results['rankings']
            metrics = results['accuracy_metrics']

            print(f"True ranking:      {rankings['true_ranking']}")
            print(f"Estimated ranking: {rankings['estimated_ranking']}")
            print(f"Kendall's τ:       {metrics['kendall_tau']:.3f}")
            print(f"Top-1 accuracy:    {metrics['top_1_accuracy']:.3f}")
            print(f"Top-3 accuracy:    {metrics['top_3_accuracy']:.3f}")

        except ValueError as e:
            print(f"Model failed: {e}")

    print("\nDemo complete. Run 'uv run python demo.py' for full visualization.")


if __name__ == "__main__":
    main()
