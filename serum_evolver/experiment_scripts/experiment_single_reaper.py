#!/usr/bin/env python3
"""
Single REAPER Instance Test
============================

Test the SerumEvolver with a single REAPER instance, small population,
and sequential processing to see the full pipeline working.
"""

import json
import logging
import time
from pathlib import Path

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
    """Create test parameters for REAPER integration."""
    test_params = {
        "fx_data": {
            "serum_vst": {
                "parameters": {
                    # Basic volume/amplitude controls  
                    "1": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.8, "name": "Master Volume"},
                    "4": {"min_value": 0.0, "max_value": 2.0, "default_value": 1.0, "name": "Oscillator A Level"},
                    
                    # Filter controls (these will affect spectral features)
                    "12": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.8, "name": "Filter Cutoff"},
                    "16": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Filter Resonance"},
                    
                    # Envelope controls
                    "24": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.0, "name": "Env Attack"},
                    "32": {"min_value": 0.0, "max_value": 1.0, "default_value": 0.7, "name": "Env Sustain"},
                }
            }
        }
    }
    
    test_file = Path("/tmp/test_fx_parameters_single.json")
    with open(test_file, 'w') as f:
        json.dump(test_params, f, indent=2)
    
    return test_file

def main():
    """Run single REAPER test."""
    
    logger.info("🚀 Starting Single REAPER SerumEvolver Test")
    
    # Initialize components
    fx_params_file = create_test_fx_params()
    param_manager = SerumParameterManager(fx_params_file)
    feature_extractor = LibrosaFeatureExtractor()
    
    # Use current working directory as REAPER project
    reaper_project = Path.cwd() / "reaper"
    audio_generator = SerumAudioGenerator(reaper_project, param_manager)
    
    # Create GA engine with NO PARALLEL PROCESSING
    ga_engine = AdaptiveSerumEvolver(
        audio_generator,
        feature_extractor, 
        param_manager,
        use_parallel_evaluation=False  # SINGLE THREADED
    )
    
    # Simple test: 2 parameters, 2 individuals, 2 generations
    logger.info("🧪 Test Configuration:")
    logger.info("   Parameters: Master Volume + Filter Cutoff") 
    logger.info("   Population: 2 individuals")
    logger.info("   Generations: 2")
    logger.info("   Processing: Sequential (no parallel)")
    
    constraint_set = {
        "1": (0.3, 1.0),   # Master volume 
        "12": (0.0, 1.0)   # Filter cutoff
    }
    
    target_features = ScalarFeatures(spectral_centroid=1500.0)
    feature_weights = FeatureWeights(spectral_centroid=1.0)
    
    start_time = time.time()
    
    try:
        logger.info("🎯 Starting evolution...")
        result = ga_engine.evolve(
            constraint_set=constraint_set,
            target_features=target_features,
            feature_weights=feature_weights,
            n_generations=2,
            population_size=2
        )
        
        experiment_time = time.time() - start_time
        
        logger.info("✅ Evolution completed!")
        logger.info(f"   Time: {experiment_time:.1f} seconds")
        logger.info(f"   Best fitness: {result['best_fitness']:.4f}")
        logger.info(f"   Best parameters: {result['best_parameters']}")
        
        # Show if we got valid results
        if result['best_fitness'] != float('inf'):
            logger.info("🎉 SUCCESS: Got finite fitness - REAPER integration working!")
        else:
            logger.info("⚠️  Got infinite fitness - check REAPER execution")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()