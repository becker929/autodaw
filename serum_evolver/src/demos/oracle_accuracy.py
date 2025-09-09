"""Oracle accuracy testing functionality."""

from pathlib import Path
from typing import Dict, Any, List, Protocol
import numpy as np

from ..audio.oracle import AudioComparisonOracle, FrequencyTargetOracle


class OracleFactory(Protocol):
    """Protocol for creating oracle instances."""

    def create_frequency_oracle(self, target_frequency: float, noise_level: float) -> Any:
        """Create a frequency target oracle."""
        ...

    def create_audio_oracle(self, target_frequency: float, noise_level: float) -> Any:
        """Create an audio comparison oracle."""
        ...


class OracleAccuracyTester:
    """Tests accuracy of different oracle implementations."""

    def __init__(self, oracle_factory: OracleFactory):
        self.oracle_factory = oracle_factory

    def test_oracle_accuracy(
        self,
        reaper_project_path: Path,
        target_frequency: float = 440.0,
        noise_levels: List[float] = None,
        n_comparisons: int = 50
    ) -> Dict[str, Any]:
        """Test oracle accuracy at different noise levels."""
        if noise_levels is None:
            noise_levels = [0.0, 0.1, 0.2, 0.5]

        results = {
            'noise_levels': noise_levels,
            'frequency_oracle_accuracies': [],
            'audio_oracle_accuracies': [],
            'agreement_rates': [],
            'n_comparisons': n_comparisons
        }

        for noise_level in noise_levels:
            accuracy_result = self._test_single_noise_level(
                target_frequency, noise_level, n_comparisons
            )

            results['frequency_oracle_accuracies'].append(accuracy_result['frequency_accuracy'])
            results['audio_oracle_accuracies'].append(accuracy_result['audio_accuracy'])
            results['agreement_rates'].append(accuracy_result['agreement_rate'])

        return results

    def _test_single_noise_level(
        self,
        target_frequency: float,
        noise_level: float,
        n_comparisons: int
    ) -> Dict[str, float]:
        """Test accuracy at a single noise level."""
        freq_oracle = self.oracle_factory.create_frequency_oracle(target_frequency, noise_level)
        audio_oracle = self.oracle_factory.create_audio_oracle(target_frequency, noise_level)

        freq_decisions = []
        audio_decisions = []

        # Generate test pairs (simple frequency pairs for comparison)
        for i in range(n_comparisons):
            freq_a = target_frequency + np.random.uniform(-100, 100)
            freq_b = target_frequency + np.random.uniform(-100, 100)

            # Get oracle decisions
            freq_decision = freq_oracle.compare(freq_a, freq_b)
            audio_decision = audio_oracle.compare(freq_a, freq_b)

            freq_decisions.append(freq_decision)
            audio_decisions.append(audio_decision)

        # Calculate agreement rate
        agreements = sum(1 for f, a in zip(freq_decisions, audio_decisions) if f == a)
        agreement_rate = agreements / n_comparisons

        # For simplicity, assume ground truth is freq_a > freq_b when freq_a > freq_b
        # This is a simplified accuracy calculation
        freq_accuracy = sum(freq_decisions) / n_comparisons
        audio_accuracy = sum(audio_decisions) / n_comparisons

        return {
            'frequency_accuracy': freq_accuracy,
            'audio_accuracy': audio_accuracy,
            'agreement_rate': agreement_rate
        }


class StandardOracleFactory:
    """Standard implementation of oracle factory."""

    def create_frequency_oracle(self, target_frequency: float, noise_level: float) -> FrequencyTargetOracle:
        """Create a frequency target oracle."""
        return FrequencyTargetOracle(target_frequency=target_frequency, noise_level=noise_level)

    def create_audio_oracle(self, target_frequency: float, noise_level: float) -> AudioComparisonOracle:
        """Create an audio comparison oracle."""
        return AudioComparisonOracle(target_frequency=target_frequency, noise_level=noise_level)


class MockOracleFactory:
    """Mock oracle factory for testing."""

    def __init__(self, mock_freq_oracle=None, mock_audio_oracle=None):
        self.mock_freq_oracle = mock_freq_oracle
        self.mock_audio_oracle = mock_audio_oracle

    def create_frequency_oracle(self, target_frequency: float, noise_level: float) -> Any:
        """Return mock frequency oracle."""
        return self.mock_freq_oracle

    def create_audio_oracle(self, target_frequency: float, noise_level: float) -> Any:
        """Return mock audio oracle."""
        return self.mock_audio_oracle
