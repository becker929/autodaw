#!/usr/bin/env python3
"""
SerumEvolver Convergence Experiments
=====================================

Test the SerumEvolver system with different parameter groups and features
to see if we can achieve convergence in evolutionary optimization.

This script runs several small-scale experiments with different:
- Parameter constraint sets (small groups of Serum parameters)
- Target feature combinations (different audio characteristics)  
- Population sizes and generation counts
- Different pymoo GA configurations

"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our SerumEvolver system
from serum_evolver import (
    SerumParameterManager,
    LibrosaFeatureExtractor, 
    SerumAudioGenerator,
    AdaptiveSerumEvolver,
    FeatureWeights,
    ScalarFeatures,
    ParameterConstraintSet
)

def create_test_fx_params() -> Path:
    """Create a minimal fx_parameters.json file for testing."""
    test_params = {
        "fx_data": {
            "serum_vst": {
                "parameters": {
                    # Basic volume/amplitude controls
                    "1": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.8, "name": "Master Volume"},
                    "4": {"min_value": 0.0, "max_value": 2.0, "default_value": 1.0, "name": "Oscillator A Level"},
                    "8": {"min_value": 0.0, "max_value": 2.0, "default_value": 0.0, "name": "Oscillator B Level"},
                    
                    # Filter controls
                    "12": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.8, "name": "Filter Cutoff"},
                    "16": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Filter Resonance"},
                    "20": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Filter Drive"},
                    
                    # Envelope controls
                    "24": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Env Attack"},
                    "28": {"min_value": 0.0, "max_value": 1.0, "default_value": 1.0, "name": "Env Decay"},
                    "32": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.7, "name": "Env Sustain"},
                    "36": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.3, "name": "Env Release"},
                    
                    # LFO controls
                    "40": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.5, "name": "LFO Rate"},
                    "44": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "LFO Amount"},
                    
                    # Effects
                    "48": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Reverb Wet"},
                    "52": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Delay Feedback"},
                    "56": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Distortion Amount"}
                }
            }
        }
    }
    
    test_file = Path("/tmp/test_fx_parameters.json")
    with open(test_file, 'w') as f:
        json.dump(test_params, f, indent=2)
    
    return test_file


class ConvergenceExperiment:
    """Run controlled convergence experiments with the SerumEvolver."""
    
    def __init__(self, results_dir: Path):
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize test components
        self.fx_params_file = create_test_fx_params()
        self.param_manager = SerumParameterManager(self.fx_params_file)
        self.feature_extractor = LibrosaFeatureExtractor()
        self.reaper_project = Path("/tmp/test_reaper_project")
        self.reaper_project.mkdir(exist_ok=True)
        self.audio_generator = SerumAudioGenerator(self.reaper_project, self.param_manager)
        
    def run_experiment(self,
                      name: str,
                      constraint_set: ParameterConstraintSet,
                      target_features: ScalarFeatures,
                      feature_weights: FeatureWeights,
                      population_size: int = 8,
                      n_generations: int = 10,
                      use_parallel: bool = True) -> Dict[str, Any]:
        """Run a single convergence experiment."""
        
        logger.info(f"\n🧪 Starting experiment: {name}")
        logger.info(f"   Parameters: {list(constraint_set.keys())}")
        logger.info(f"   Active features: {list(feature_weights.get_active_features().keys())}")
        logger.info(f"   Population size: {population_size}, Generations: {n_generations}")
        
        # Create GA engine for this experiment
        ga_engine = AdaptiveSerumEvolver(
            self.audio_generator,
            self.feature_extractor,
            self.param_manager,
            use_parallel_evaluation=use_parallel
        )
        
        start_time = time.time()
        
        try:
            # Run evolution
            result = ga_engine.evolve(
                constraint_set=constraint_set,
                target_features=target_features, 
                feature_weights=feature_weights,
                n_generations=n_generations,
                population_size=population_size
            )
            
            experiment_time = time.time() - start_time
            
            # Check if we achieved convergence
            final_fitness = result['best_fitness']
            fitness_history = result['fitness_history']
            
            converged = self._check_convergence(fitness_history, final_fitness)
            improvement = self._calculate_improvement(fitness_history)
            
            experiment_result = {
                'name': name,
                'success': True,
                'converged': converged,
                'final_fitness': final_fitness,
                'fitness_improvement': improvement,
                'generations_run': result.get('generations_run', n_generations),
                'experiment_time': experiment_time,
                'best_parameters': result['best_parameters'],
                'fitness_history': fitness_history,
                'config': {
                    'constraint_set': constraint_set,
                    'target_features': target_features.__dict__,
                    'feature_weights': feature_weights.__dict__,
                    'population_size': population_size,
                    'n_generations': n_generations,
                    'use_parallel': use_parallel
                }
            }
            
            logger.info(f"✅ Experiment completed: fitness={final_fitness:.4f}, "
                       f"converged={converged}, time={experiment_time:.1f}s")
            
        except Exception as e:
            logger.error(f"❌ Experiment failed: {e}")
            experiment_result = {
                'name': name,
                'success': False,
                'error': str(e),
                'experiment_time': time.time() - start_time
            }
        
        # Save results
        result_file = self.results_dir / f"{name.replace(' ', '_').lower()}.json"
        with open(result_file, 'w') as f:
            json.dump(experiment_result, f, indent=2, default=str)
        
        return experiment_result
    
    def _check_convergence(self, fitness_history: List[float], final_fitness: float) -> bool:
        """Check if the evolution converged to a reasonable solution."""
        if not fitness_history or final_fitness == float('inf'):
            return False
        
        # Check if fitness improved significantly from start to end
        initial_fitness = fitness_history[0] if fitness_history else float('inf')
        improvement = (initial_fitness - final_fitness) / max(initial_fitness, 1.0)
        
        # Consider converged if:
        # 1. Final fitness is finite and reasonable (< 10.0)
        # 2. We saw at least 10% improvement from initial fitness
        return final_fitness < 10.0 and improvement > 0.1
    
    def _calculate_improvement(self, fitness_history: List[float]) -> float:
        """Calculate the percentage improvement in fitness."""
        if len(fitness_history) < 2:
            return 0.0
        
        initial = fitness_history[0]
        final = fitness_history[-1]
        
        if initial == 0 or initial == float('inf'):
            return 0.0
            
        return ((initial - final) / initial) * 100.0
    
    def run_all_experiments(self) -> List[Dict[str, Any]]:
        """Run a comprehensive set of convergence experiments."""
        
        logger.info("🚀 Starting SerumEvolver Convergence Experiments")
        
        experiments = []
        
        # Experiment 1: Simple volume optimization
        # Target: Moderate volume with spectral centroid focus
        experiments.append(self.run_experiment(
            name="Simple Volume Control",
            constraint_set={"1": (0.3, 1.0), "4": (0.5, 1.5)},  # Master + Osc A volume
            target_features=ScalarFeatures(spectral_centroid=2000.0),
            feature_weights=FeatureWeights(spectral_centroid=1.0),
            population_size=6,
            n_generations=8
        ))
        
        # Experiment 2: Filter sweep optimization  
        # Target: Bright filtered sound
        experiments.append(self.run_experiment(
            name="Filter Sweep",
            constraint_set={"12": (0.2, 1.0), "16": (0.0, 0.8)},  # Cutoff + Resonance
            target_features=ScalarFeatures(spectral_centroid=3000.0, spectral_bandwidth=1500.0),
            feature_weights=FeatureWeights(spectral_centroid=0.7, spectral_bandwidth=0.3),
            population_size=8,
            n_generations=10
        ))
        
        # Experiment 3: Multi-parameter envelope shaping
        # Target: Punchy attack with good sustain
        experiments.append(self.run_experiment(
            name="Envelope Shaping", 
            constraint_set={
                "24": (0.0, 0.3),  # Fast attack
                "28": (0.2, 0.8),  # Medium decay  
                "32": (0.5, 1.0),  # High sustain
                "36": (0.1, 0.6)   # Medium release
            },
            target_features=ScalarFeatures(rms_energy=0.7, zero_crossing_rate=0.1),
            feature_weights=FeatureWeights(rms_energy=0.6, zero_crossing_rate=0.4),
            population_size=10,
            n_generations=12
        ))
        
        # Experiment 4: Complex multi-feature optimization
        # Target: Warm bass with controlled harmonics
        experiments.append(self.run_experiment(
            name="Complex Multi-Feature",
            constraint_set={
                "1": (0.6, 1.0),    # Master volume
                "4": (0.8, 1.8),    # Osc A level
                "12": (0.1, 0.6),   # Low-pass filter
                "16": (0.0, 0.4),   # Light resonance
                "32": (0.7, 1.0)    # High sustain
            },
            target_features=ScalarFeatures(
                spectral_centroid=800.0,
                rms_energy=0.8,
                spectral_contrast=0.6,
                chroma_mean=0.7
            ),
            feature_weights=FeatureWeights(
                spectral_centroid=0.4,
                rms_energy=0.3, 
                spectral_contrast=0.2,
                chroma_mean=0.1
            ),
            population_size=12,
            n_generations=15
        ))
        
        # Experiment 5: Large population test
        # Test if larger populations help convergence
        experiments.append(self.run_experiment(
            name="Large Population Test",
            constraint_set={"1": (0.2, 1.0), "4": (0.5, 2.0), "12": (0.3, 1.0)},
            target_features=ScalarFeatures(spectral_centroid=1500.0, rms_energy=0.6),
            feature_weights=FeatureWeights(spectral_centroid=0.8, rms_energy=0.2),
            population_size=20,  # Large population
            n_generations=8
        ))
        
        # Experiment 6: Long evolution test
        # Test if more generations help convergence
        experiments.append(self.run_experiment(
            name="Long Evolution Test", 
            constraint_set={"12": (0.0, 1.0), "16": (0.0, 1.0), "20": (0.0, 0.5)},
            target_features=ScalarFeatures(spectral_centroid=2500.0),
            feature_weights=FeatureWeights(spectral_centroid=1.0),
            population_size=8,
            n_generations=25  # Many generations
        ))
        
        return experiments


def analyze_results(experiments: List[Dict[str, Any]]) -> None:
    """Analyze and report on experiment results."""
    
    logger.info("\n📊 CONVERGENCE EXPERIMENT RESULTS")
    logger.info("=" * 50)
    
    successful = [exp for exp in experiments if exp.get('success', False)]
    converged = [exp for exp in successful if exp.get('converged', False)]
    
    logger.info(f"Total experiments: {len(experiments)}")
    logger.info(f"Successful runs: {len(successful)}")
    logger.info(f"Converged experiments: {len(converged)}")
    logger.info(f"Convergence rate: {len(converged)}/{len(successful)} ({len(converged)/len(successful)*100:.1f}%)")
    
    if successful:
        avg_time = np.mean([exp['experiment_time'] for exp in successful])
        logger.info(f"Average experiment time: {avg_time:.1f}s")
        
        best_fitness = min([exp['final_fitness'] for exp in successful])
        logger.info(f"Best fitness achieved: {best_fitness:.4f}")
    
    logger.info("\n📋 Individual Results:")
    for exp in experiments:
        if exp.get('success'):
            status = "✅ CONVERGED" if exp.get('converged') else "⚠️  NO CONVERGENCE" 
            logger.info(f"{exp['name']:25} | {status:15} | "
                       f"Fitness: {exp['final_fitness']:8.4f} | "
                       f"Time: {exp['experiment_time']:6.1f}s")
        else:
            logger.info(f"{exp['name']:25} | ❌ FAILED      | Error: {exp.get('error', 'Unknown')}")


def main():
    """Run the convergence experiments."""
    
    # Create results directory
    results_dir = Path("experiment_results") / f"convergence_{int(time.time())}"
    
    # Run experiments
    experiment_runner = ConvergenceExperiment(results_dir)
    experiments = experiment_runner.run_all_experiments()
    
    # Analyze results
    analyze_results(experiments)
    
    # Save summary
    summary = {
        'timestamp': time.time(),
        'total_experiments': len(experiments),
        'successful': len([e for e in experiments if e.get('success')]),
        'converged': len([e for e in experiments if e.get('converged')]),
        'experiments': experiments
    }
    
    summary_file = results_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"\n💾 Results saved to: {results_dir}")
    logger.info("🎯 Convergence experiments completed!")


if __name__ == "__main__":
    main()