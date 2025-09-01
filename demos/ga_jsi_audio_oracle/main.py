"""Entry point for GA + JSI + Audio Oracle integration demo."""

from pathlib import Path
from ga_jsi_audio_oracle.main import run_full_demo_suite, demo_jsi_audio_optimization


def main():
    """Run the GA + JSI + Audio Oracle demo."""
    print("GA + JSI + Audio Oracle Integration Demo")
    print("=" * 50)

    # Locate REAPER project
    reaper_path = Path("../../reaper").resolve()
    if not reaper_path.exists():
        print(f"Error: REAPER project not found at {reaper_path}")
        print("Please ensure the reaper project is available at the expected location.")
        return 1

    try:
        # Run basic demo first
        print("Running basic JSI audio optimization demo...")

        result = demo_jsi_audio_optimization(
            reaper_project_path=reaper_path,
            target_frequency=440.0,
            n_generations=6,
            population_size=4,  # Small population for quick demo
            oracle_noise_level=0.05,
            show_live_ranking=True
        )

        if result['success']:
            print("\nDemo completed successfully!")
            best_info = result.get('best_info', {})
            if best_info:
                print(f"Best solution: {best_info.get('solution', 'N/A')}")
                print(f"Best fitness: {best_info.get('fitness', 'N/A')}")
                print(f"JSI comparisons: {best_info.get('jsi_comparisons', 'N/A')}")

            print(f"Duration: {result.get('duration_seconds', 'N/A')} seconds")
            print(f"Generations: {result.get('generations_completed', 'N/A')}")
        else:
            print(f"Demo failed: {result.get('error', 'Unknown error')}")
            return 1

        print("\n" + "="*60)
        print("Demo completed! Check reaper/renders/ for generated audio files.")
        print("The JSI algorithm ranked audio samples based on their proximity")
        print("to the target frequency using librosa analysis.")
        print("="*60)

        return 0

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
