"""Basic tests that don't require complex imports."""

import pytest
import numpy as np


def test_arithmetic():
    """Simple test that should always pass."""
    assert 1 + 1 == 2


def test_numpy_available():
    """Test that numpy is available."""
    arr = np.array([1, 2, 3])
    assert len(arr) == 3


def test_pathlib_available():
    """Test that pathlib is available."""
    from pathlib import Path
    p = Path("test.txt")
    assert p.suffix == ".txt"


if __name__ == "__main__":
    pytest.main([__file__])
