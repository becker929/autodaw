#!/usr/bin/env python3
"""
Fully Automated SerumEvolver Experiment.

Complete workflow:
1. Generate random FX parameter constraints
2. Generate random target individual within constraints  
3. Render target individual through REAPER
4. Extract features from target audio
5. Run GA evolution to match target features
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
)
from serum_evolver.session_manager import ExperimentSessionManager
from serum_evolver.ga_engine import AdaptiveSerumEvolver
from artifact_manager import ArtifactManager
from experiment_config_generator import ExperimentConfigGenerator
from target_audio_generator import TargetAudioGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_automated_experiment(complexity: str = 'medium', 
                            feature_profile: str = 'random',
                            experiment_name: str = None) -> dict:
    """
    Run complete automated SerumEvolver experiment.
    
    Args:
        complexity: 'simple', 'medium', or 'complex'
        feature_profile: 'random', 'bright_sound', 'warm_sound', 'balanced', 'dynamic_range'
        experiment_name: Optional custom experiment name
        
    Returns:
        Dictionary containing experiment results
    """
    start_time = time.time()
    
    logger.info("="*60)
    logger.info("STARTING AUTOMATED SERUMEVOLVER EXPERIMENT")
    logger.info("="*60)
    
    # Initialize core components
    logger.info("Initializing core components...")
    fx_params_path = Path("/tmp/test_fx_parameters_single.json")
    reaper_project_path = project_root / "reaper"
    
    param_manager = SerumParameterManager(fx_params_path)
    feature_extractor = LibrosaFeatureExtractor()
    
    # STEP 1: Generate random experiment configuration
    logger.info("\n" + "="*40)
    logger.info("STEP 1: GENERATING EXPERIMENT CONFIGURATION")
    logger.info("="*40)
    
    config_generator = ExperimentConfigGenerator(param_manager)
    config = config_generator.generate_experiment_config(
        experiment_name=experiment_name,
        complexity=complexity,
        feature_profile=feature_profile
    )
    
    logger.info(f"Generated experiment: {config.name}")
    logger.info(f"Complexity level: {complexity}")
    logger.info(f"Feature profile: {feature_profile}")
    logger.info(f"Parameters to evolve: {list(config.constraint_set.keys())}")
    
    param_names = []
    for param_id in config.constraint_set.keys():
        if param_id in config_generator.available_params:
            param_names.append(config_generator.available_params[param_id]['name'])
    logger.info(f"Parameter names: {param_names}")
    
    logger.info(f"Target parameters: {config.target_parameters}")
    logger.info(f"Population size: {config.population_size}")
    logger.info(f"Generations: {config.n_generations}")
    
    # STEP 2: Initialize experiment management
    logger.info("\n" + "="*40)
    logger.info("STEP 2: INITIALIZING EXPERIMENT MANAGEMENT")
    logger.info("="*40)
    
    # Initialize ArtifactManager for organized results
    artifact_manager = ArtifactManager(config.name)
    logger.info(f"ArtifactManager initialized: {artifact_manager.experiment_dir}")
    
    # Save experiment configuration
    config_path = artifact_manager.experiment_dir / "experiment_config.json"
    config_generator.save_config(config, config_path)
    logger.info(f"Experiment config saved: {config_path}")
    
    # STEP 3: Generate and render target audio
    logger.info("\n" + "="*40)
    logger.info("STEP 3: GENERATING TARGET AUDIO")
    logger.info("="*40)
    
    target_generator = TargetAudioGenerator(reaper_project_path, param_manager)
    
    try:
        target_audio_path, target_features = target_generator.generate_complete_target(
            target_parameters=config.target_parameters,
            experiment_name=config.name,
            feature_extractor=feature_extractor,
            feature_weights=config.feature_weights,
            artifact_manager=artifact_manager
        )
        
        logger.info(f"✓ Target audio generated: {target_audio_path}")
        logger.info(f"✓ Target features extracted: {target_features}")
        
    except Exception as e:
        logger.error(f"✗ Target generation failed: {e}")
        raise RuntimeError(f"Target generation failed: {e}")
    
    # STEP 4: Initialize evolution components
    logger.info("\n" + "="*40) 
    logger.info("STEP 4: INITIALIZING EVOLUTION SYSTEM")
    logger.info("="*40)
    
    # Create session manager with target audio and artifact manager
    session_manager = ExperimentSessionManager(
        reaper_project_path=reaper_project_path,
        param_manager=param_manager,
        experiment_name=config.name,
        target_audio_path=target_audio_path,  # Use generated target audio
        artifact_manager=artifact_manager
    )
    
    # Create evolutionary optimizer
    evolver = AdaptiveSerumEvolver(
        session_manager=session_manager,
        feature_extractor=feature_extractor,
        param_manager=param_manager
    )
    
    logger.info("✓ Evolution system initialized")
    
    # STEP 5: Run evolutionary optimization
    logger.info("\n" + "="*40)
    logger.info("STEP 5: RUNNING EVOLUTIONARY OPTIMIZATION")
    logger.info("="*40)
    
    logger.info(f"Target to match: {target_features}")
    logger.info(f"Using {config.population_size} individuals over {config.n_generations} generations")
    logger.info("Starting evolution...")
    
    evolution_start = time.time()
    
    try:
        result = evolver.evolve(
            constraint_set=config.constraint_set,
            target_features=target_features,
            feature_weights=config.feature_weights,
            n_generations=config.n_generations,
            population_size=config.population_size,
            session_dir=session_manager.experiment_dir  # Enable generation logging
        )
        
        evolution_duration = time.time() - evolution_start
        
        logger.info("✓ Evolution completed successfully")
        logger.info(f"Evolution took: {evolution_duration:.1f} seconds")
        
    except Exception as e:
        logger.error(f"✗ Evolution failed: {e}")
        raise RuntimeError(f"Evolution failed: {e}")
    
    # STEP 6: Analyze and report results
    logger.info("\n" + "="*40)
    logger.info("STEP 6: ANALYZING RESULTS") 
    logger.info("="*40)
    
    total_duration = time.time() - start_time
    
    logger.info("EXPERIMENT COMPLETED SUCCESSFULLY!")
    logger.info(f"Total experiment time: {total_duration:.1f} seconds ({total_duration/60:.1f} minutes)")
    logger.info(f"Best fitness achieved: {result['best_fitness']:.6f}")
    
    # Compare target vs best evolved parameters
    logger.info("\nParameter Comparison:")
    logger.info("Target Parameters -> Best Evolved Parameters")
    best_params = result['best_individual']
    for param_id in config.constraint_set.keys():
        target_val = config.target_parameters.get(param_id, 'N/A')
        evolved_val = best_params.get(param_id, 'N/A')
        param_name = config_generator.available_params.get(param_id, {}).get('name', param_id)
        logger.info(f"  {param_name} ({param_id}): {target_val:.4f} -> {evolved_val:.4f}")
    
    # Show experiment structure
    logger.info("\nGenerated Experiment Structure:")
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
    
    logger.info(f"  📋 experiment_config.json")
    logger.info(f"\nExperiment results saved to: {artifact_manager.experiment_dir}")
    
    # Prepare comprehensive result summary
    experiment_summary = {
        'experiment_name': config.name,
        'configuration': {
            'complexity': complexity,
            'feature_profile': feature_profile,
            'constraint_set': config.constraint_set,
            'target_parameters': config.target_parameters,
            'population_size': config.population_size,
            'n_generations': config.n_generations
        },
        'target_audio_path': str(target_audio_path),
        'target_features': target_features.__dict__ if hasattr(target_features, '__dict__') else target_features,
        'evolution_results': result,
        'timing': {
            'total_duration': total_duration,
            'evolution_duration': evolution_duration
        },
        'experiment_directory': str(artifact_manager.experiment_dir)
    }
    
    return experiment_summary


def main():
    """Run automated experiment with command line options."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run automated SerumEvolver experiment')
    parser.add_argument('--complexity', choices=['simple', 'medium', 'complex'], 
                       default='medium', help='Parameter complexity level')
    parser.add_argument('--profile', choices=['random', 'bright_sound', 'warm_sound', 'balanced', 'dynamic_range'],
                       default='random', help='Feature weighting profile')
    parser.add_argument('--name', type=str, help='Custom experiment name')
    
    args = parser.parse_args()
    
    try:
        result = run_automated_experiment(
            complexity=args.complexity,
            feature_profile=args.profile,
            experiment_name=args.name
        )
        
        print(f"\n{'='*60}")
        print("EXPERIMENT SUMMARY")
        print(f"{'='*60}")
        print(f"Experiment: {result['experiment_name']}")
        print(f"Best fitness: {result['evolution_results']['best_fitness']:.6f}")
        print(f"Total time: {result['timing']['total_duration']:.1f}s")
        print(f"Results: {result['experiment_directory']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Experiment failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())