#!/usr/bin/env python3
"""
Session-based SerumEvolver experiment with proper directory structure.

This script runs evolution using batch rendering and organized file structure:
renders/<experiment>/<generation>/renders/<individual>/untitled.wav
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
    ScalarFeatures,
    FeatureWeights
)
from serum_evolver.session_manager import ExperimentSessionManager
from serum_evolver.ga_engine import AdaptiveSerumEvolver
from artifact_manager import ArtifactManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run session-based SerumEvolver experiment."""
    logger.info("Starting session-based SerumEvolver experiment")
    
    # Create session directory with timestamp
    session_timestamp = int(time.time())
    experiment_name = f"session_based_experiment_{session_timestamp}"
    
    logger.info(f"Experiment: {experiment_name}")
    
    # Initialize components
    logger.info("Initializing SerumEvolver components...")
    fx_params_path = Path("/tmp/test_fx_parameters_single.json")
    reaper_project_path = project_root / "reaper"
    
    param_manager = SerumParameterManager(fx_params_path)
    feature_extractor = LibrosaFeatureExtractor()
    
    # Initialize ArtifactManager for organized experiment results
    artifact_manager = ArtifactManager(experiment_name)
    logger.info(f"ArtifactManager initialized: {artifact_manager}")
    
    # Create session manager with ArtifactManager integration
    session_manager = ExperimentSessionManager(
        reaper_project_path=reaper_project_path,
        param_manager=param_manager,
        experiment_name=experiment_name,
        target_audio_path=None,  # TODO: Add real target audio
        artifact_manager=artifact_manager
    )
    
    # Create evolver with session-based processing
    evolver = AdaptiveSerumEvolver(
        session_manager=session_manager,
        feature_extractor=feature_extractor,
        param_manager=param_manager
    )
    
    # Define experiment parameters (same as before but smaller for testing)
    constraint_set = {
        '1': (0.0, 1.0),    # Master Volume
        '12': (0.0, 1.0),   # Filter Cutoff  
        '16': (0.0, 1.0),   # Filter Resonance
    }
    
    # Target features for bright, punchy sound (still synthetic for now)
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
    
    # Smaller experiment parameters for testing
    population_size = 4   # Small population for testing
    n_generations = 3     # Few generations for testing
    
    logger.info(f"Experiment parameters:")
    logger.info(f"  - Population size: {population_size}")
    logger.info(f"  - Generations: {n_generations}")
    logger.info(f"  - Parameters to evolve: {list(constraint_set.keys())}")
    logger.info(f"  - Processing mode: Session-based batch rendering")
    
    # Create fitness log directory at experiment level
    session_dir = session_manager.experiment_dir
    fitness_log_path = session_dir / "fitness_log.txt"
    
    logger.info("Starting evolution...")
    logger.info(f"Experiment directory: {session_dir}")
    logger.info(f"Fitness log: {fitness_log_path}")
    
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
        
        # Show both REAPER working directory and organized experiment results
        logger.info("Generated directory structures:")
        logger.info("1. REAPER working directory (temporary):")
        for path in sorted(session_dir.rglob("*")):
            if path.is_dir():
                logger.info(f"  📁 {path.relative_to(session_dir)}/")
            elif path.suffix == ".wav":
                logger.info(f"  🔊 {path.relative_to(session_dir)}")
            elif path.name in ["fitness_log.txt"]:
                logger.info(f"  📊 {path.relative_to(session_dir)}")
        
        logger.info(f"REAPER session files: {session_dir}")
        
        # Show ArtifactManager structure
        if artifact_manager:
            logger.info("2. Organized experiment results:")
            structure = artifact_manager.list_experiment_structure()
            
            logger.info(f"📁 {artifact_manager.experiment_dir}/")
            for item in structure.get("target", []):
                logger.info(f"  📁 target/{item}")
            
            for gen_info in structure.get("generations", []):
                logger.info(f"  📁 {gen_info['name']}/ ({gen_info['individuals']} individuals)")
                if gen_info["has_stats"]:
                    logger.info(f"    📊 generation_stats.json")
                if gen_info["has_config"]:
                    logger.info(f"    ⚙️  session_config.json")
            
            for log_file in structure.get("logs", []):
                logger.info(f"  📊 {log_file}")
            
            logger.info(f"Organized results: {artifact_manager.experiment_dir}")
        
        return result
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        raise

if __name__ == "__main__":
    main()