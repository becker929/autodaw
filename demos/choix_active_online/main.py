#!/usr/bin/env python3
"""Main entry point for 'Just Sort It' active learning ranking demo."""

import sys
import time
import argparse
import numpy as np
from rich.console import Console
from rich.columns import Columns
from choix_active_online_demo.comparison_oracle import SimulatedOracle, HumanOracle
from choix_active_online_demo.ranking_tracker import SimpleRankingTracker
from choix_active_online_demo.jsi_engine import JSIAdaptiveQuicksort
from choix_active_online_demo.display_utils import create_ranking_table, create_stats_panel
from choix_active_online_demo.fitness_normalizer import FitnessNormalizer


def get_user_choice(prompt: str, options: list) -> int:
    """Get user choice from a list of options."""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")

    while True:
        try:
            choice = int(input("Enter choice (number): ").strip())
            if 1 <= choice <= len(options):
                return choice - 1
            else:
                print(f"Invalid choice. Please enter 1-{len(options)}")
        except ValueError:
            print("Invalid input. Please enter a number")


def human_comparison_callback(item_a: str, item_b: str) -> bool:
    """Simple CLI callback for human comparisons."""
    print(f"\nWhich is better?")
    print(f"1. {item_a}")
    print(f"2. {item_b}")

    while True:
        try:
            choice = input("Enter choice (1 or 2): ").strip()
            if choice == "1":
                return True  # item_a wins
            elif choice == "2":
                return False  # item_b wins
            else:
                print("Invalid choice. Enter 1 or 2")
        except (ValueError, KeyboardInterrupt):
            print("Invalid input. Enter 1 or 2")


def main():
    """Run the 'Just Sort It' active learning demonstration."""
    parser = argparse.ArgumentParser(description='Just Sort It - Active Learning Ranking Demo')
    parser.add_argument('--simulated', action='store_true',
                       help='Run with simulated oracle (no user input required)')
    parser.add_argument('items', nargs='*',
                       help='Items to rank (default: programming languages)')

    args = parser.parse_args()

    console = Console()

    # Default items - can be customized
    default_items = [
        "Python", "JavaScript", "Rust", "Go", "Java",
        "C++", "TypeScript", "Swift", "Kotlin", "Ruby"
    ]

    # Use provided items or default
    items = args.items if args.items else default_items

    console.print("🎯 Just Sort It - Active Learning Ranking", style="bold magenta")
    console.print("="*50)
    console.print(f"Items to rank: {', '.join(items)}")
    console.print(f"Total items: {len(items)}")
    console.print("\n🧠 Using: JSI Adaptive Quicksort + Bradley-Terry Analysis")

    # Choose oracle type based on flag or user input
    if args.simulated:
        oracle_choice = 0
        console.print("\n🤖 Using Simulated Oracle (--simulated flag)")
    else:
        oracle_choice = get_user_choice(
            "Choose oracle type:",
            ["Simulated Oracle (automated demo)", "Human Oracle (you make comparisons)"]
        )

    # Initialize components
    ranking_tracker = SimpleRankingTracker(items)

    # Create oracle based on selection
    if oracle_choice == 0:
        # Simulated oracle
        np.random.seed(42)
        strengths = {item: np.random.exponential(1.0) for item in items}
        oracle = SimulatedOracle(strengths, noise_level=0.1)
        console.print("\n🤖 Using Simulated Oracle")
        console.print("Generated random strengths for items")
    else:
        # Human oracle
        oracle = HumanOracle(human_comparison_callback)
        console.print("\n👤 Using Human Oracle")
        console.print("You will be asked to make comparisons between items")

    # Create JSI engine
    jsi_engine = JSIAdaptiveQuicksort(oracle, ranking_tracker)

    console.print("\n🚀 Starting JSI active learning...")
    console.print("Press Ctrl+C to stop at any time\n")

    try:
        start_time = time.time()

        # Run learning iterations
        max_iterations = 10
        for iteration in range(1, max_iterations + 1):
            console.print(f"\n--- Iteration {iteration} ---", style="bold yellow")
            console.print("Starting quicksort iteration...")

            # Run JSI adaptive quicksort with live display
            if oracle_choice == 0:  # Simulated - show live updates
                sorted_items = jsi_engine.adaptive_quicksort(items, console)
            else:  # Human - no live display to avoid confusion during input
                sorted_items = jsi_engine.adaptive_quicksort(items)

            elapsed_time = time.time() - start_time

            # At iteration end: run full BT analysis with real confidence
            ranking, confidence, strengths = ranking_tracker.get_bt_ranking_with_confidence()

            console.print(f"\nCompleted iteration. Quicksort result: {sorted_items[:3]}...")

            # Show full BT analysis
            stats_panel = create_stats_panel(
                jsi_engine.comparison_count,
                elapsed_time,
                ranking[0] if ranking else None,
                confidence
            )
            ranking_table = create_ranking_table(ranking, strengths, f"Bradley-Terry Analysis (Iteration {iteration})")

            console.print(Columns([stats_panel, ranking_table]))

            # For human oracle, ask if they want to continue
            if oracle_choice == 1 and iteration < max_iterations:
                continue_choice = input(f"\nRun iteration {iteration + 1}? (y/n): ").strip().lower()
                if continue_choice != 'y':
                    break

        # Final results
        console.print("\n" + "="*50, style="bold green")
        console.print("FINAL RESULTS", style="bold green")
        console.print("="*50, style="bold green")

        final_ranking, final_confidence, final_strengths = ranking_tracker.get_bt_ranking_with_confidence()
        final_stats = create_stats_panel(
            jsi_engine.comparison_count,
            time.time() - start_time,
            final_ranking[0] if final_ranking else None,
            final_confidence
        )
        final_table = create_ranking_table(final_ranking, final_strengths, "Final Bradley-Terry Ranking")

        console.print(Columns([final_stats, final_table]))

        # Fitness normalization for GA integration
        if final_strengths:
            console.print("\n" + "="*50, style="bold cyan")
            console.print("FITNESS NORMALIZATION FOR GA", style="bold cyan")
            console.print("="*50, style="bold cyan")

            normalizer = FitnessNormalizer(temperature=1.0)
            fitness_summary = normalizer.get_fitness_summary(final_strengths)

            # Display softmax normalized values (recommended for GA)
            console.print("\n🎯 Softmax Normalized Fitness Values (recommended for GA):")
            softmax_fitness = fitness_summary['softmax']
            for item, fitness in normalizer.rank_by_fitness(softmax_fitness):
                console.print(f"  {item:12}: {fitness:.4f}")

            # Display other normalization options
            console.print("\n📊 Alternative Normalization Methods:")

            console.print("\n  Exponential (preserves Bradley-Terry ratios):")
            exp_fitness = fitness_summary['exponential']
            for item, fitness in normalizer.rank_by_fitness(exp_fitness):
                console.print(f"    {item:12}: {fitness:.4f}")

            console.print("\n  Min-Max Normalized [0,1]:")
            minmax_fitness = fitness_summary['min_max']
            for item, fitness in normalizer.rank_by_fitness(minmax_fitness):
                console.print(f"    {item:12}: {fitness:.4f}")

    except KeyboardInterrupt:
        console.print("\n\n👋 Learning interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Error: {e}")
        sys.exit(1)

    console.print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
