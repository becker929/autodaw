"""
Simple demo script to test the GA-REAPER integration.
"""

from pathlib import Path
from ga_frequency_demo.main import demo_basic_optimization, demo_target_frequency


def main():
    """Run integration demos"""
    print("=== GA-REAPER Integration Demo ===")
    print("Testing genetic algorithm optimization with REAPER...")

    # Check if REAPER project exists
    reaper_path = Path("../reaper").resolve()
    if not reaper_path.exists():
        print(f"Error: REAPER project not found at {reaper_path}")
        print("Please ensure the reaper project is available at the expected location.")
        return 1

    try:
        print("\n1. Running basic frequency optimization demo...")
        basic_result = demo_basic_optimization()

        if basic_result and 'best_info' in basic_result:
            print("Basic demo completed successfully!")
            best_info = basic_result['best_info']
            if best_info:
                print(f"Best solution found: {best_info['solution']}")
                print(f"Best fitness: {best_info['fitness']:.6f}")
        else:
            print("Basic demo completed but no results available.")

        print("\n" + "="*50)

        print("\n2. Running target frequency optimization demo...")
        target_result = demo_target_frequency()

        if target_result and 'best_info' in target_result:
            print("Target frequency demo completed successfully!")
            best_info = target_result['best_info']
            if best_info:
                print(f"Best solution found: {best_info['solution']}")
                print(f"Target frequency ratio: {target_result['target_ratio']:.6f}")
                print(f"Achieved frequency ratio: {best_info['frequency_ratio']:.6f}")
                print(f"Best fitness: {best_info['fitness']:.6f}")
        else:
            print("Target frequency demo completed but no results available.")

        print("\n=== Demo Complete ===")
        print("Check the reaper/renders/ directory for generated audio files.")

        return 0

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
