"""Tests for src/core/__init__.py module."""

import pytest
from unittest.mock import patch, MagicMock

from serum_evolver.src import core


class TestCoreModule:
    """Test the core module initialization and exports."""

    def test_module_imports(self):
        """Test that all expected classes are importable from core module."""
        # Test direct access to imported classes
        assert hasattr(core, 'JSIAudioOptimizationProblem')
        assert hasattr(core, 'MultiTargetJSIOptimizationProblem')

        # Test that classes are actually classes (not None or other types)
        assert core.JSIAudioOptimizationProblem is not None
        assert core.MultiTargetJSIOptimizationProblem is not None

        # Test that they're callable (classes)
        assert callable(core.JSIAudioOptimizationProblem)
        assert callable(core.MultiTargetJSIOptimizationProblem)

    def test_all_exports(self):
        """Test that __all__ contains the expected exports."""
        expected_exports = [
            'JSIAudioOptimizationProblem',
            'MultiTargetJSIOptimizationProblem',
        ]

        assert hasattr(core, '__all__')
        assert set(core.__all__) == set(expected_exports)

        # Test that all items in __all__ are actually available in module
        for export_name in core.__all__:
            assert hasattr(core, export_name)

    def test_class_inheritance(self):
        """Test that imported classes maintain their expected inheritance."""
        # These should be the actual classes, not proxies
        from serum_evolver.src.genetics.jsi_problems import JSIAudioOptimizationProblem, MultiTargetJSIOptimizationProblem

        assert core.JSIAudioOptimizationProblem is JSIAudioOptimizationProblem
        assert core.MultiTargetJSIOptimizationProblem is MultiTargetJSIOptimizationProblem

    def test_jsi_audio_optimization_problem_access(self):
        """Test that JSIAudioOptimizationProblem is accessible through core module."""
        # Just test that the class is accessible and has expected attributes
        assert hasattr(core.JSIAudioOptimizationProblem, '__init__')
        assert hasattr(core.JSIAudioOptimizationProblem, '__doc__')
        assert 'jsi' in core.JSIAudioOptimizationProblem.__doc__.lower()
        assert 'audio oracle' in core.JSIAudioOptimizationProblem.__doc__.lower()

    def test_multi_target_jsi_optimization_problem_access(self):
        """Test that MultiTargetJSIOptimizationProblem is accessible through core module."""
        # Just test that the class is accessible and has expected attributes
        assert hasattr(core.MultiTargetJSIOptimizationProblem, '__init__')
        assert hasattr(core.MultiTargetJSIOptimizationProblem, '__doc__')
        assert 'multi' in core.MultiTargetJSIOptimizationProblem.__doc__.lower()

    def test_module_docstring(self):
        """Test that the core module has proper documentation."""
        assert core.__doc__ is not None
        assert "Core optimization components" in core.__doc__
        assert "JSI" in core.__doc__
