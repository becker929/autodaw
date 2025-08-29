"""Parameter sweep generation and management."""

import itertools
import random
from typing import Iterator, Dict, List, Protocol
from config import ParameterSpec, SweepConfiguration


class ParameterSweepStrategy(Protocol):
    """Protocol for parameter sweep strategies."""

    def generate_combinations(self, config: SweepConfiguration) -> Iterator[Dict[str, float]]:
        """Generate parameter combinations according to strategy."""
        ...


class GridSweepStrategy:
    """Generate all combinations in a grid pattern."""

    def generate_combinations(self, config: SweepConfiguration) -> Iterator[Dict[str, float]]:
        """Generate grid search combinations."""
        param_values = []
        param_names = []

        for param in config.parameters:
            param_names.append(param.name)
            values = self._generate_parameter_values(param)
            param_values.append(values)

        total_combinations = 1
        for values in param_values:
            total_combinations *= len(values)

        if total_combinations > config.max_combinations:
            print(f"Warning: Grid search would generate {total_combinations} combinations, "
                  f"limiting to {config.max_combinations}")

        count = 0
        for combination in itertools.product(*param_values):
            if count >= config.max_combinations:
                break
            yield dict(zip(param_names, combination))
            count += 1

    def _generate_parameter_values(self, param: ParameterSpec) -> List[float]:
        """Generate values for a single parameter."""
        if param.steps == 1:
            return [param.min_value]

        step_size = (param.max_value - param.min_value) / (param.steps - 1)
        return [param.min_value + i * step_size for i in range(param.steps)]


class RandomSweepStrategy:
    """Generate random combinations within parameter ranges."""

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

    def generate_combinations(self, config: SweepConfiguration) -> Iterator[Dict[str, float]]:
        """Generate random combinations."""
        for _ in range(config.max_combinations):
            combination = {}
            for param in config.parameters:
                value = random.uniform(param.min_value, param.max_value)
                combination[param.name] = value
            yield combination


class ParameterSweepEngine:
    """Engine for generating parameter sweep combinations."""

    def __init__(self):
        self.strategies = {
            'grid': GridSweepStrategy(),
            'random': RandomSweepStrategy()
        }

    def add_strategy(self, name: str, strategy: ParameterSweepStrategy) -> None:
        """Add a custom sweep strategy."""
        self.strategies[name] = strategy

    def generate_sweep(self, config: SweepConfiguration) -> Iterator[Dict[str, float]]:
        """Generate parameter sweep according to configuration."""
        if config.strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {config.strategy}")

        strategy = self.strategies[config.strategy]
        return strategy.generate_combinations(config)

    def estimate_combinations(self, config: SweepConfiguration) -> int:
        """Estimate number of combinations that will be generated."""
        if config.strategy == 'grid':
            total = 1
            for param in config.parameters:
                total *= param.steps
            return min(total, config.max_combinations)
        elif config.strategy == 'random':
            return config.max_combinations
        else:
            return config.max_combinations  # Conservative estimate


class ParameterValidator:
    """Validates parameter specifications and values."""

    @staticmethod
    def validate_parameter_spec(spec: ParameterSpec) -> None:
        """Validate a parameter specification."""
        if spec.steps < 1:
            raise ValueError(f"Parameter {spec.name}: steps must be at least 1")

        if spec.min_value >= spec.max_value:
            raise ValueError(f"Parameter {spec.name}: min_value must be less than max_value")

        if not spec.name.strip():
            raise ValueError("Parameter name cannot be empty")

    @staticmethod
    def validate_parameter_value(spec: ParameterSpec, value: float) -> float:
        """Validate and clamp a parameter value to spec range."""
        if value < spec.min_value:
            print(f"Warning: {spec.name} value {value} below minimum {spec.min_value}, clamping")
            return spec.min_value

        if value > spec.max_value:
            print(f"Warning: {spec.name} value {value} above maximum {spec.max_value}, clamping")
            return spec.max_value

        return value

    @staticmethod
    def validate_sweep_config(config: SweepConfiguration) -> None:
        """Validate a sweep configuration."""
        if not config.parameters:
            raise ValueError("Sweep configuration must have at least one parameter")

        for param in config.parameters:
            ParameterValidator.validate_parameter_spec(param)

        if config.max_combinations < 1:
            raise ValueError("max_combinations must be at least 1")


# Common parameter specifications
COMMON_PARAMETERS = {
    'octave': ParameterSpec('octave', -4.0, 4.0, 9),  # -4 to +4 octaves, 9 steps
    'filter_cutoff': ParameterSpec('filter_cutoff', 0.0, 1.0, 10),  # 0 to 100%, 10 steps
    'resonance': ParameterSpec('resonance', 0.0, 1.0, 5),  # 0 to 100%, 5 steps
    'attack': ParameterSpec('attack', 0.0, 1.0, 5),  # 0 to 100%, 5 steps
    'decay': ParameterSpec('decay', 0.0, 1.0, 5),  # 0 to 100%, 5 steps
    'sustain': ParameterSpec('sustain', 0.0, 1.0, 5),  # 0 to 100%, 5 steps
    'release': ParameterSpec('release', 0.0, 1.0, 5),  # 0 to 100%, 5 steps
}
