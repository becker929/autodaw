#!/usr/bin/env python3
"""
SerumEvolver Mock Convergence Experiments
==========================================

Test the SerumEvolver system with MOCKED audio generation to verify
GA convergence behavior without requiring REAPER integration.

This allows us to test:
- Parameter constraint handling
- Feature distance calculations  
- GA evolution convergence
- Different population sizes and generations
"""

import json
import logging
import time
import tempfile
import wave
import struct
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np

# Set up logging
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
                    
                    # Filter controls (these will affect spectral features)
                    "12": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.8, "name": "Filter Cutoff"},
                    "16": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Filter Resonance"},
                    "20": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Filter Drive"},
                    
                    # Envelope controls (these will affect RMS energy and temporal features)
                    "24": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Env Attack"},
                    "28": {"min_value": 0.0, "max_value": 1.0, "default_value": 1.0, "name": "Env Decay"},
                    "32": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.7, "name": "Env Sustain"},
                    "36": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.3, "name": "Env Release"},
                    
                    # LFO controls
                    "40": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.5, "name": "LFO Rate"},
                    "44": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "LFO Amount"},
                }
            }
        }
    }
    
    test_file = Path("/tmp/test_fx_parameters.json")
    with open(test_file, 'w') as f:
        json.dump(test_params, f, indent=2)
    
    return test_file


class MockSerumAudioGenerator:
    """Mock audio generator that creates synthetic audio based on parameter values."""
    
    def __init__(self, reaper_project_path: Path, param_manager):
        self.reaper_project_path = reaper_project_path
        self.param_manager = param_manager
        logger.info("Initialized Mock Audio Generator")
    
    def create_random_patch(self, constraint_set: ParameterConstraintSet) -> Tuple[Dict[str, float], Path]:
        """Generate random patch within constraints and create mock audio."""
        # Generate random values within constraint ranges
        serum_params = {}
        for param_id, (min_val, max_val) in constraint_set.items():
            serum_params[param_id] = np.random.uniform(min_val, max_val)
        
        # Create mock audio file
        session_name = f"random_{int(time.time() * 1000000) % 1000000}"
        audio_path = self.render_patch(serum_params, session_name)
        
        return serum_params, audio_path
    
    def render_patch(self, serum_params: Dict[str, float], session_name: str) -> Path:
        """Create synthetic audio based on parameter values."""
        # Create deterministic synthetic audio based on parameter values
        audio_data = self._synthesize_audio(serum_params)
        
        # Save to temporary WAV file
        audio_path = Path(tempfile.mktemp(suffix='.wav'))
        self._save_wav(audio_data, audio_path)
        
        return audio_path
    
    def _synthesize_audio(self, params: Dict[str, float]) -> np.ndarray:
        """
        Create synthetic audio that correlates with parameter values.
        This allows the GA to learn meaningful parameter->feature relationships.
        """
        duration = 2.0  # 2 seconds
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Base frequency influenced by filter cutoff (param 12)
        cutoff = params.get('12', 0.5)  # Filter cutoff 0-1
        base_freq = 200 + cutoff * 1800  # 200-2000 Hz range
        
        # Volume influenced by master volume (param 1) and oscillator levels
        master_vol = params.get('1', 0.8)
        osc_a_level = params.get('4', 1.0) 
        osc_b_level = params.get('8', 0.0)
        
        # Generate oscillator A (sine wave)
        osc_a = np.sin(2 * np.pi * base_freq * t) * osc_a_level
        
        # Generate oscillator B (higher frequency)
        osc_b_freq = base_freq * 1.5
        osc_b = np.sin(2 * np.pi * osc_b_freq * t) * osc_b_level
        
        # Mix oscillators
        signal = (osc_a + osc_b) * master_vol
        
        # Apply envelope shaping (affects RMS energy)
        attack = params.get('24', 0.0)   # Attack time
        decay = params.get('28', 1.0)    # Decay time  
        sustain = params.get('32', 0.7)  # Sustain level
        release = params.get('36', 0.3)  # Release time
        
        envelope = self._create_adsr_envelope(len(signal), attack, decay, sustain, release)
        signal = signal * envelope
        
        # Add some harmonic content based on filter resonance (param 16)
        resonance = params.get('16', 0.0)
        if resonance > 0:
            # Add harmonics that affect spectral features
            harmonic2 = np.sin(2 * np.pi * base_freq * 2 * t) * resonance * 0.3
            harmonic3 = np.sin(2 * np.pi * base_freq * 3 * t) * resonance * 0.2
            signal = signal + harmonic2 + harmonic3
        
        # Normalize and add slight noise
        signal = signal / (np.max(np.abs(signal)) + 1e-10)  # Avoid div by zero
        signal = signal * 0.8  # Leave some headroom
        signal = signal + np.random.normal(0, 0.01, len(signal))  # Add noise
        
        return signal.astype(np.float32)
    
    def _create_adsr_envelope(self, length: int, attack: float, decay: float, 
                            sustain: float, release: float) -> np.ndarray:
        """Create ADSR envelope that affects temporal features."""
        envelope = np.ones(length)
        
        # Convert normalized values to sample indices
        attack_samples = int(length * attack * 0.1)  # Attack is up to 10% of signal
        decay_samples = int(length * decay * 0.2)    # Decay is up to 20% of signal
        release_samples = int(length * release * 0.3) # Release is up to 30% of signal
        
        # Attack phase
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay phase  
        if decay_samples > 0:
            decay_start = attack_samples
            decay_end = min(decay_start + decay_samples, length)
            envelope[decay_start:decay_end] = np.linspace(1, sustain, decay_end - decay_start)
        
        # Sustain phase (middle of signal)
        sustain_start = attack_samples + decay_samples
        sustain_end = max(sustain_start, length - release_samples)
        if sustain_end > sustain_start:
            envelope[sustain_start:sustain_end] = sustain
        
        # Release phase
        if release_samples > 0:
            release_start = length - release_samples
            envelope[release_start:] = np.linspace(sustain, 0, release_samples)
        
        return envelope
    
    def _save_wav(self, audio_data: np.ndarray, path: Path):
        """Save numpy array as WAV file."""
        # Convert to 16-bit PCM
        audio_16bit = (audio_data * 32767).astype(np.int16)
        
        with wave.open(str(path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(44100)
            wav_file.writeframes(audio_16bit.tobytes())


class MockConvergenceExperiment:
    """Run controlled convergence experiments with mocked audio generation."""
    
    def __init__(self, results_dir: Path):
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.fx_params_file = create_test_fx_params()
        self.param_manager = SerumParameterManager(self.fx_params_file)
        self.feature_extractor = LibrosaFeatureExtractor()
        
        # Use mock audio generator instead of real REAPER integration
        self.audio_generator = MockSerumAudioGenerator(
            Path("/tmp/mock_reaper"), self.param_manager
        )
        
    def run_experiment(self,
                      name: str,
                      constraint_set: ParameterConstraintSet,
                      target_features: ScalarFeatures,
                      feature_weights: FeatureWeights,
                      population_size: int = 8,
                      n_generations: int = 10) -> Dict[str, Any]:
        """Run a single convergence experiment."""
        
        logger.info(f"\n🧪 Starting experiment: {name}")
        logger.info(f"   Parameters: {list(constraint_set.keys())}")
        logger.info(f"   Active features: {list(feature_weights.get_active_features().keys())}")
        logger.info(f"   Population size: {population_size}, Generations: {n_generations}")
        
        # Create GA engine
        ga_engine = AdaptiveSerumEvolver(
            self.audio_generator,
            self.feature_extractor, 
            self.param_manager,
            use_parallel_evaluation=True
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
            
            # Analyze results
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
                    'n_generations': n_generations
                }
            }
            
            logger.info(f"✅ Experiment completed: fitness={final_fitness:.4f}, "
                       f"converged={converged}, improvement={improvement:.1f}%, time={experiment_time:.1f}s")
            
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
        """Check if evolution converged to a reasonable solution."""
        if not fitness_history or final_fitness == float('inf'):
            return False
            
        # Check if fitness improved and reached reasonable values
        initial_fitness = fitness_history[0] if fitness_history else float('inf')
        improvement = (initial_fitness - final_fitness) / max(initial_fitness, 1.0)
        
        # Consider converged if:
        # 1. Final fitness is reasonable (< 5.0 for our mock system)
        # 2. We saw at least 20% improvement
        # 3. Fitness is decreasing in later generations
        recent_trend = self._check_recent_improvement(fitness_history[-5:]) if len(fitness_history) >= 5 else True
        
        return final_fitness < 5.0 and improvement > 0.2 and recent_trend
    
    def _check_recent_improvement(self, recent_fitness: List[float]) -> bool:
        """Check if fitness improved in recent generations."""
        if len(recent_fitness) < 3:
            return True
        return recent_fitness[-1] <= recent_fitness[0]  # Latest <= earliest in recent history
    
    def _calculate_improvement(self, fitness_history: List[float]) -> float:
        """Calculate percentage improvement in fitness."""
        if len(fitness_history) < 2:
            return 0.0
            
        initial = fitness_history[0]
        final = fitness_history[-1]
        
        if initial == 0 or initial == float('inf'):
            return 0.0
            
        return ((initial - final) / initial) * 100.0
    
    def run_all_experiments(self) -> List[Dict[str, Any]]:
        """Run comprehensive convergence experiments with different parameters."""
        
        logger.info("🚀 Starting Mock SerumEvolver Convergence Experiments")
        
        experiments = []
        
        # Experiment 1: Simple volume optimization
        # Target: Higher spectral centroid (brighter sound)
        experiments.append(self.run_experiment(
            name="Simple Volume Control",
            constraint_set={"1": (0.1, 1.0), "4": (0.3, 1.8)},  # Master + Osc A
            target_features=ScalarFeatures(spectral_centroid=1500.0),
            feature_weights=FeatureWeights(spectral_centroid=1.0),
            population_size=8,
            n_generations=10
        ))
        
        # Experiment 2: Filter optimization
        # Target: Bright filtered sound with good energy
        experiments.append(self.run_experiment(
            name="Filter Optimization",
            constraint_set={"12": (0.0, 1.0), "16": (0.0, 0.7)},  # Cutoff + Resonance
            target_features=ScalarFeatures(spectral_centroid=2000.0, rms_energy=0.6),
            feature_weights=FeatureWeights(spectral_centroid=0.7, rms_energy=0.3),
            population_size=10,
            n_generations=12
        ))
        
        # Experiment 3: Envelope shaping 
        # Target: Punchy attack with controlled sustain
        experiments.append(self.run_experiment(
            name="Envelope Shaping",
            constraint_set={
                "24": (0.0, 0.4),  # Attack
                "32": (0.3, 1.0),  # Sustain
                "36": (0.1, 0.8)   # Release
            },
            target_features=ScalarFeatures(rms_energy=0.7, spectral_centroid=1200.0),
            feature_weights=FeatureWeights(rms_energy=0.6, spectral_centroid=0.4),
            population_size=10,
            n_generations=15
        ))
        
        # Experiment 4: Complex multi-parameter
        # Target: Complex sound with multiple features
        experiments.append(self.run_experiment(
            name="Complex Multi-Parameter",
            constraint_set={
                "1": (0.4, 1.0),    # Master volume
                "4": (0.8, 2.0),    # Osc A level
                "8": (0.0, 1.2),    # Osc B level
                "12": (0.2, 0.9),   # Filter cutoff
                "16": (0.0, 0.6)    # Filter resonance
            },
            target_features=ScalarFeatures(
                spectral_centroid=1800.0,
                rms_energy=0.8,
                spectral_bandwidth=800.0
            ),
            feature_weights=FeatureWeights(
                spectral_centroid=0.5,
                rms_energy=0.3,
                spectral_bandwidth=0.2
            ),
            population_size=12,
            n_generations=15
        ))
        
        # Experiment 5: Large population test
        experiments.append(self.run_experiment(
            name="Large Population Test",
            constraint_set={"1": (0.2, 1.0), "4": (0.5, 2.0), "12": (0.3, 1.0)},
            target_features=ScalarFeatures(spectral_centroid=1600.0, rms_energy=0.7),
            feature_weights=FeatureWeights(spectral_centroid=0.8, rms_energy=0.2),
            population_size=24,  # Large population
            n_generations=8
        ))
        
        # Experiment 6: Long evolution test  
        experiments.append(self.run_experiment(
            name="Long Evolution Test",
            constraint_set={"12": (0.0, 1.0), "16": (0.0, 1.0)},
            target_features=ScalarFeatures(spectral_centroid=2200.0),
            feature_weights=FeatureWeights(spectral_centroid=1.0),
            population_size=8,
            n_generations=30  # Many generations
        ))
        
        return experiments


def analyze_results(experiments: List[Dict[str, Any]]) -> None:
    """Analyze and report experiment results."""
    
    logger.info("\n📊 MOCK CONVERGENCE EXPERIMENT RESULTS")
    logger.info("=" * 60)
    
    successful = [exp for exp in experiments if exp.get('success', False)]
    converged = [exp for exp in successful if exp.get('converged', False)]
    
    logger.info(f"Total experiments: {len(experiments)}")
    logger.info(f"Successful runs: {len(successful)}")
    logger.info(f"Converged experiments: {len(converged)}")
    
    if successful:
        success_rate = len(successful) / len(experiments) * 100
        convergence_rate = len(converged) / len(successful) * 100
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Convergence rate: {convergence_rate:.1f}%")
        
        avg_time = np.mean([exp['experiment_time'] for exp in successful])
        avg_improvement = np.mean([exp.get('fitness_improvement', 0) for exp in successful])
        best_fitness = min([exp['final_fitness'] for exp in successful])
        
        logger.info(f"Average experiment time: {avg_time:.1f}s")
        logger.info(f"Average fitness improvement: {avg_improvement:.1f}%")
        logger.info(f"Best fitness achieved: {best_fitness:.4f}")
    
    logger.info("\n📋 Individual Results:")
    logger.info(f"{'Experiment':<25} | {'Status':<15} | {'Fitness':<10} | {'Improvement':<12} | {'Time':<8}")
    logger.info("-" * 80)
    
    for exp in experiments:
        if exp.get('success'):
            status = "✅ CONVERGED" if exp.get('converged') else "⚠️  NO CONVERGE" 
            improvement = exp.get('fitness_improvement', 0)
            logger.info(f"{exp['name']:<25} | {status:<15} | "
                       f"{exp['final_fitness']:8.4f} | {improvement:8.1f}% | "
                       f"{exp['experiment_time']:6.1f}s")
        else:
            logger.info(f"{exp['name']:<25} | {'❌ FAILED':<15} | {'N/A':<10} | {'N/A':<12} | "
                       f"{exp.get('experiment_time', 0):6.1f}s")


def main():
    """Run the mock convergence experiments."""
    
    # Create results directory
    results_dir = Path("experiment_results") / f"mock_convergence_{int(time.time())}"
    
    # Run experiments
    experiment_runner = MockConvergenceExperiment(results_dir)
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
    logger.info("🎯 Mock convergence experiments completed!")
    
    # Show best performing experiment
    successful = [e for e in experiments if e.get('success')]
    if successful:
        best_exp = min(successful, key=lambda x: x['final_fitness'])
        logger.info(f"\n🏆 Best performing experiment: {best_exp['name']}")
        logger.info(f"   Final fitness: {best_exp['final_fitness']:.4f}")
        logger.info(f"   Improvement: {best_exp['fitness_improvement']:.1f}%")
        logger.info(f"   Best parameters: {best_exp['best_parameters']}")


if __name__ == "__main__":
    main()