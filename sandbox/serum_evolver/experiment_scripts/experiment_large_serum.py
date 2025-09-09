#!/usr/bin/env python3
"""
Large-scale SerumEvolver experiment with generation logging.

This script runs a longer evolution with larger population size
and creates a fitness log that can be tailed separately.
"""

import sys
import logging
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from serum_evolver import (
    SerumParameterManager, 
    LibrosaFeatureExtractor, 
    SerumAudioGenerator,
    AdaptiveSerumEvolver,
    ScalarFeatures,
    FeatureWeights
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run large-scale SerumEvolver experiment."""
    logger.info("Starting large-scale SerumEvolver experiment")
    
    # Create session directory with timestamp
    session_timestamp = int(time.time())
    session_dir = project_root / f"experiment_results/large_serum_{session_timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Session directory: {session_dir}")
    logger.info(f"Fitness log will be available at: {session_dir}/fitness_log.txt")
    
    # Initialize components
    logger.info("Initializing SerumEvolver components...")
    fx_params_path = Path("/tmp/test_fx_parameters_single.json")
    reaper_project_path = project_root / "reaper"
    
    param_manager = SerumParameterManager(fx_params_path)
    feature_extractor = LibrosaFeatureExtractor()
    audio_generator = SerumAudioGenerator(reaper_project_path, param_manager)
    
    # Create evolver with sequential processing (no parallel for REAPER)
    evolver = AdaptiveSerumEvolver(
        audio_generator=audio_generator,
        feature_extractor=feature_extractor,
        param_manager=param_manager,
        max_workers=1,  # REAPER runs sequentially
        use_parallel_evaluation=False  # Sequential processing
    )
    
    # Define larger experiment parameters
    constraint_set = {
        '1': (0.0, 1.0),    # Master Volume
        '12': (0.0, 1.0),   # Filter Cutoff  
        '16': (0.0, 1.0),   # Filter Resonance
        '24': (0.0, 1.0),   # Env Attack
        '32': (0.0, 1.0),   # Env Sustain
    }
    
    # Target features for bright, punchy sound
    target_features = ScalarFeatures(
        spectral_centroid=2500.0,
        spectral_rolloff=8000.0, 
        spectral_bandwidth=1500.0,
        spectral_contrast=0.7,
        zero_crossing_rate=0.15,
        rms_energy=0.3,
        mfcc_mean=-12.0
    )
    
    # Equal weighting for all features
    feature_weights = FeatureWeights(
        spectral_centroid=1.0,
        spectral_rolloff=1.0,
        spectral_bandwidth=1.0,
        spectral_contrast=1.0,
        zero_crossing_rate=1.0,
        rms_energy=1.0,
        mfcc_mean=1.0
    )
    
    # Larger experiment parameters
    population_size = 10  # Increased from 4
    n_generations = 15    # Increased from 5
    
    logger.info(f"Experiment parameters:")
    logger.info(f"  - Population size: {population_size}")
    logger.info(f"  - Generations: {n_generations}")
    logger.info(f"  - Parameters to evolve: {list(constraint_set.keys())}")
    logger.info(f"  - Processing mode: Sequential (REAPER-compatible)")
    
    logger.info("Starting evolution...")
    logger.info(f"You can monitor progress with: tail -f {session_dir}/fitness_log.txt")
    
    start_time = time.time()
    
    try:
        # Run evolution with session directory for logging
        result = evolver.evolve(
            constraint_set=constraint_set,
            target_features=target_features,
            feature_weights=feature_weights,
            n_generations=n_generations,
            population_size=population_size,
            session_dir=session_dir  # Enable generation logging
        )
        
        duration = time.time() - start_time
        
        # Print comprehensive results
        logger.info("="*50)
        logger.info("EXPERIMENT COMPLETED")
        logger.info("="*50)
        logger.info(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        logger.info(f"Best fitness: {result['best_fitness']:.4f}")
        logger.info(f"Generations run: {result.get('generations_run', n_generations)}")
        
        logger.info(f"Best parameters found:")
        best_params = result['best_individual']
        for param_id, value in best_params.items():
            if param_id in constraint_set:
                logger.info(f"  {param_id}: {value:.4f}")
        
        logger.info(f"Convergence achieved: {result['evolution_metadata'].get('convergence_achieved', False)}")
        
        if 'performance_metrics' in result:
            metrics = result['performance_metrics']
            logger.info(f"Total evaluations: {metrics.get('total_evaluations', 'N/A')}")
            logger.info(f"Average evaluation time: {metrics.get('avg_evaluation_time', 0):.2f}s")
            
        # Print fitness progression
        fitness_history = result.get('fitness_history', [])
        if fitness_history:
            logger.info(f"Fitness progression:")
            for i, fitness in enumerate(fitness_history):
                logger.info(f"  Generation {i}: {fitness:.4f}")
        
        logger.info(f"Session files saved to: {session_dir}")
        logger.info(f"Fitness log: {session_dir}/fitness_log.txt")
        
        return result
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise

if __name__ == "__main__":
    main()