"""Simple test to check basic imports."""

def test_basic_import():
    """Test that we can import basic modules."""
    try:
        from serum_evolver.src.genetics.genetics import Solution
        assert Solution is not None
    except ImportError as e:
        pytest.fail(f"Failed to import Solution: {e}")


def test_arithmetic():
    """Simple test that should always pass."""
    assert 1 + 1 == 2
