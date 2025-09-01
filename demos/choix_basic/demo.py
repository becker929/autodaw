#!/usr/bin/env python3
"""Main demonstration script for Bradley-Terry algorithm."""

from choix_demo.bradley_terry import BradleyTerryDemo
from choix_demo.visualization import BradleyTerryVisualizer


def main():
    """Run the Bradley-Terry demonstration."""
    print("Bradley-Terry Algorithm Demonstration")
    print("====================================")

    # Create demo instance
    demo = BradleyTerryDemo(n_items=8, random_seed=42)

    # Run the complete demonstration
    print("\nRunning Bradley-Terry model with 200 comparisons...")
    results = demo.run_full_demo(n_comparisons=200)

    # Create visualizer
    visualizer = BradleyTerryVisualizer()

    # Print summary report
    print(visualizer.create_summary_report(results))

    # Create visualizations
    print("Generating visualizations...")

    print("\n1. Strength comparison plot...")
    visualizer.plot_strength_comparison(results)

    print("\n2. Comparison matrix heatmap...")
    visualizer.plot_comparison_matrix(results)

    print("\n3. Ranking comparison plot...")
    visualizer.plot_ranking_comparison(results)

    print("\n4. Convergence analysis...")
    visualizer.plot_convergence_analysis(demo, [25, 50, 100, 200, 400])

    print("\nDemonstration complete.")


if __name__ == "__main__":
    main()
