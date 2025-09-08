#!/usr/bin/env python3
"""Quick test script to verify the GA + JSI + Audio Oracle integration."""

import sys
from pathlib import Path

# Add the demo to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from ga_jsi_audio_oracle.audio_oracle import AudioComparisonOracle, FrequencyTargetOracle
        print("✓ Audio oracle imports successful")
    except ImportError as e:
        print(f"✗ Audio oracle import failed: {e}")
        return False

    try:
        from ga_jsi_audio_oracle.jsi_ga_integration import GAPopulationRanker, JSIFitnessEvaluator
        print("✓ JSI integration imports successful")
    except ImportError as e:
        print(f"✗ JSI integration import failed: {e}")
        return False

    try:
        from ga_jsi_audio_oracle.ga_problem import JSIAudioOptimizationProblem
        print("✓ GA problem imports successful")
    except ImportError as e:
        print(f"✗ GA problem import failed: {e}")
        return False

    try:
        from ga_jsi_audio_oracle.main import demo_jsi_audio_optimization
        print("✓ Main demo imports successful")
    except ImportError as e:
        print(f"✗ Main demo import failed: {e}")
        return False

    return True


def test_audio_oracle():
    """Test basic audio oracle functionality."""
    print("\nTesting audio oracle...")

    try:
        from ga_jsi_audio_oracle.audio_oracle import AudioComparisonOracle

        # Create oracle
        oracle = AudioComparisonOracle(target_frequency=440.0, noise_level=0.0)

        # Test basic functionality
        oracle.set_target_frequency(523.25)
        assert oracle.target_frequency == 523.25

        cache_info = oracle.get_cache_info()
        assert cache_info['cached_files'] == 0

        oracle.clear_cache()

        print("✓ Audio oracle basic functionality works")
        return True

    except Exception as e:
        print(f"✗ Audio oracle test failed: {e}")
        return False


def test_jsi_integration():
    """Test JSI integration components."""
    print("\nTesting JSI integration...")

    try:
        from ga_jsi_audio_oracle.jsi_ga_integration import GAPopulationRanker
        from ga_jsi_audio_oracle.audio_oracle import AudioComparisonOracle

        # Create components
        oracle = AudioComparisonOracle(target_frequency=440.0)
        ranker = GAPopulationRanker(oracle, show_live_ranking=False)

        assert ranker.comparison_count == 0
        assert ranker.generation_count == 0

        # Test path matching
        audio_paths = {'sol_001': Path('test1.wav'), 'sol_002': Path('test2.wav')}
        result = ranker._find_matching_audio_path('sol_001', audio_paths)
        assert result == Path('test1.wav')

        print("✓ JSI integration basic functionality works")
        return True

    except Exception as e:
        print(f"✗ JSI integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("GA + JSI + Audio Oracle Integration Test")
    print("=" * 60)

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False

    # Test components
    if not test_audio_oracle():
        all_passed = False

    if not test_jsi_integration():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - Integration is ready!")
        print("Run 'uv run python main.py' to execute the full demo.")
    else:
        print("✗ Some tests failed - check the output above")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
