#!/usr/bin/env python3
"""
Experiment Configuration Generator for SerumEvolver.

Generates random:
- FX parameter constraint sets (which parameters to evolve)
- Target individuals (parameter values within constraints)
- Feature extraction configurations
"""

import random
import json
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass

from serum_evolver import ParameterConstraintSet, SerumParameters, FeatureWeights


@dataclass
class ExperimentConfig:
    """Complete configuration for a SerumEvolver experiment."""
    name: str
    constraint_set: ParameterConstraintSet
    target_parameters: SerumParameters
    feature_weights: FeatureWeights
    population_size: int
    n_generations: int


class ExperimentConfigGenerator:
    """Generates random experiment configurations."""
    
    def __init__(self, param_manager):
        """Initialize with parameter manager for validation."""
        self.param_manager = param_manager
        
        # Available Serum parameters with their semantic meaning
        self.available_params = {
            '1': {'name': 'Master Volume', 'range': (0.0, 1.0), 'importance': 'high'},
            '4': {'name': 'Oscillator A Level', 'range': (0.0, 2.0), 'importance': 'high'},
            '12': {'name': 'Filter Cutoff', 'range': (0.0, 1.0), 'importance': 'high'},
            '16': {'name': 'Filter Resonance', 'range': (0.0, 1.0), 'importance': 'medium'},
            '24': {'name': 'Env Attack', 'range': (0.0, 1.0), 'importance': 'medium'},
            '32': {'name': 'Env Sustain', 'range': (0.0, 1.0), 'importance': 'medium'},
        }
        
        # Feature importance profiles
        self.feature_profiles = {
            'bright_sound': {
                'spectral_centroid': 2.0,
                'spectral_rolloff': 1.5,
                'spectral_bandwidth': 1.0,
                'spectral_contrast': 1.0,
                'zero_crossing_rate': 0.5,
                'rms_energy': 1.0,
                'mfcc_mean': 0.5
            },
            'warm_sound': {
                'spectral_centroid': 0.5,
                'spectral_rolloff': 0.5,
                'spectral_bandwidth': 1.0,
                'spectral_contrast': 1.5,
                'zero_crossing_rate': 0.5,
                'rms_energy': 1.5,
                'mfcc_mean': 1.0
            },
            'balanced': {
                'spectral_centroid': 1.0,
                'spectral_rolloff': 1.0,
                'spectral_bandwidth': 1.0,
                'spectral_contrast': 1.0,
                'zero_crossing_rate': 1.0,
                'rms_energy': 1.0,
                'mfcc_mean': 1.0
            },
            'dynamic_range': {
                'spectral_centroid': 1.0,
                'spectral_rolloff': 1.0,
                'spectral_bandwidth': 2.0,
                'spectral_contrast': 2.0,
                'zero_crossing_rate': 1.0,
                'rms_energy': 0.8,
                'mfcc_mean': 0.8
            }
        }
    
    def generate_constraint_set(self, 
                               num_params: Optional[int] = None,
                               complexity: str = 'medium') -> ParameterConstraintSet:
        """
        Generate random parameter constraint set.
        
        Args:
            num_params: Number of parameters to include (None for random)
            complexity: 'simple' (2-3 params), 'medium' (3-4), 'complex' (4-6)
        
        Returns:
            Random constraint set
        """
        if num_params is None:
            if complexity == 'simple':
                num_params = random.randint(2, 3)
            elif complexity == 'medium':
                num_params = random.randint(3, 4)
            elif complexity == 'complex':
                num_params = random.randint(4, 6)
            else:
                num_params = 3
        
        # Select random parameters, weighted by importance
        param_ids = list(self.available_params.keys())
        
        # Weight selection by importance
        weights = []
        for param_id in param_ids:
            importance = self.available_params[param_id]['importance']
            weight = 3 if importance == 'high' else 2 if importance == 'medium' else 1
            weights.append(weight)
        
        selected_params = random.choices(
            param_ids, 
            weights=weights, 
            k=min(num_params, len(param_ids))
        )
        
        # Remove duplicates while preserving order
        selected_params = list(dict.fromkeys(selected_params))
        
        # Create constraint set with some variation in bounds
        constraint_set = {}
        for param_id in selected_params:
            base_range = self.available_params[param_id]['range']
            min_val, max_val = base_range
            
            # Occasionally tighten the range for more focused evolution
            if random.random() < 0.3:  # 30% chance to tighten range
                range_size = max_val - min_val
                tighten_factor = random.uniform(0.6, 0.9)
                new_range = range_size * tighten_factor
                center = (min_val + max_val) / 2
                
                min_val = max(min_val, center - new_range/2)
                max_val = min(max_val, center + new_range/2)
            
            constraint_set[param_id] = (min_val, max_val)
        
        return constraint_set
    
    def generate_target_parameters(self, constraint_set: ParameterConstraintSet) -> SerumParameters:
        """
        Generate random target parameters within constraint set.
        
        Args:
            constraint_set: Parameter constraints
            
        Returns:
            Random parameter values within constraints
        """
        target_params = {}
        
        for param_id, (min_val, max_val) in constraint_set.items():
            # Generate random value within range
            target_params[param_id] = random.uniform(min_val, max_val)
        
        return target_params
    
    def generate_feature_weights(self, profile: str = 'random') -> FeatureWeights:
        """
        Generate feature weights configuration.
        
        Args:
            profile: 'random', 'bright_sound', 'warm_sound', 'balanced', 'dynamic_range'
            
        Returns:
            Feature weights configuration
        """
        if profile == 'random':
            profile = random.choice(list(self.feature_profiles.keys()))
        
        if profile not in self.feature_profiles:
            profile = 'balanced'
        
        base_weights = self.feature_profiles[profile]
        
        # Add some randomization to the base profile
        feature_weights = {}
        for feature, base_weight in base_weights.items():
            # Add ±20% random variation
            variation = random.uniform(0.8, 1.2)
            feature_weights[feature] = base_weight * variation
        
        return FeatureWeights(**feature_weights)
    
    def generate_experiment_config(self, 
                                  experiment_name: Optional[str] = None,
                                  complexity: str = 'medium',
                                  feature_profile: str = 'random',
                                  population_size: Optional[int] = None,
                                  n_generations: Optional[int] = None) -> ExperimentConfig:
        """
        Generate complete experiment configuration.
        
        Args:
            experiment_name: Name for the experiment (auto-generated if None)
            complexity: Parameter complexity level
            feature_profile: Feature weighting profile
            population_size: GA population size (None for random)
            n_generations: Number of generations (None for random)
            
        Returns:
            Complete experiment configuration
        """
        if experiment_name is None:
            timestamp = int(random.random() * 1000000)
            experiment_name = f"auto_experiment_{timestamp}"
        
        # Generate components
        constraint_set = self.generate_constraint_set(complexity=complexity)
        target_parameters = self.generate_target_parameters(constraint_set)
        feature_weights = self.generate_feature_weights(feature_profile)
        
        # Generate GA parameters
        if population_size is None:
            if complexity == 'simple':
                population_size = random.randint(4, 8)
            elif complexity == 'medium':
                population_size = random.randint(6, 12)
            else:  # complex
                population_size = random.randint(8, 16)
        
        if n_generations is None:
            if complexity == 'simple':
                n_generations = random.randint(3, 6)
            elif complexity == 'medium':
                n_generations = random.randint(5, 10)
            else:  # complex
                n_generations = random.randint(8, 15)
        
        return ExperimentConfig(
            name=experiment_name,
            constraint_set=constraint_set,
            target_parameters=target_parameters,
            feature_weights=feature_weights,
            population_size=population_size,
            n_generations=n_generations
        )
    
    def save_config(self, config: ExperimentConfig, output_path: Path):
        """Save experiment configuration to JSON file."""
        config_data = {
            'name': config.name,
            'constraint_set': config.constraint_set,
            'target_parameters': config.target_parameters,
            'feature_weights': config.feature_weights.__dict__,
            'population_size': config.population_size,
            'n_generations': config.n_generations,
            'parameter_info': {
                param_id: self.available_params[param_id]['name']
                for param_id in config.constraint_set.keys()
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_config(self, config_path: Path) -> ExperimentConfig:
        """Load experiment configuration from JSON file."""
        with open(config_path) as f:
            config_data = json.load(f)
        
        return ExperimentConfig(
            name=config_data['name'],
            constraint_set=config_data['constraint_set'],
            target_parameters=config_data['target_parameters'],
            feature_weights=FeatureWeights(**config_data['feature_weights']),
            population_size=config_data['population_size'],
            n_generations=config_data['n_generations']
        )


def main():
    """Test the configuration generator."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    from serum_evolver import SerumParameterManager
    
    # Initialize parameter manager
    fx_params_path = Path("/tmp/test_fx_parameters_single.json")
    param_manager = SerumParameterManager(fx_params_path)
    
    # Create generator
    generator = ExperimentConfigGenerator(param_manager)
    
    # Generate a few example configurations
    for complexity in ['simple', 'medium', 'complex']:
        for profile in ['bright_sound', 'warm_sound', 'balanced']:
            config = generator.generate_experiment_config(
                experiment_name=f"test_{complexity}_{profile}",
                complexity=complexity,
                feature_profile=profile
            )
            
            print(f"\n=== {config.name} ===")
            print(f"Parameters to evolve: {list(config.constraint_set.keys())}")
            print(f"Target parameters: {config.target_parameters}")
            print(f"Population: {config.population_size}, Generations: {config.n_generations}")
            print(f"Feature profile: {profile}")
            
            # Save config
            output_path = project_root / f"configs/{config.name}.json"
            output_path.parent.mkdir(exist_ok=True)
            generator.save_config(config, output_path)
            print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()