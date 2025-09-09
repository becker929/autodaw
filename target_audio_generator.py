#!/usr/bin/env python3
"""
Target Audio Generator for SerumEvolver experiments.

Renders target audio from parameter configurations using REAPER.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Tuple, Dict
import json

from serum_evolver import SerumParameters
from serum_evolver.session_manager import ExperimentSessionManager
from artifact_manager import ArtifactManager

logger = logging.getLogger(__name__)


class TargetAudioGenerator:
    """Generates target audio by rendering specific parameter configurations."""
    
    def __init__(self, reaper_project_path: Path, param_manager):
        """
        Initialize target audio generator.
        
        Args:
            reaper_project_path: Path to REAPER project directory
            param_manager: Parameter manager for validation
        """
        self.reaper_project_path = Path(reaper_project_path)
        self.param_manager = param_manager
        
        logger.info(f"Initialized TargetAudioGenerator with REAPER project: {reaper_project_path}")
    
    def render_target_audio(self, 
                           target_parameters: SerumParameters,
                           experiment_name: str,
                           artifact_manager: Optional[ArtifactManager] = None) -> Tuple[Path, Dict]:
        """
        Render target audio from parameter configuration.
        
        Args:
            target_parameters: Serum parameters to render
            experiment_name: Name for the rendering session
            artifact_manager: Optional artifact manager for organization
            
        Returns:
            Tuple of (audio_file_path, target_features_dict)
        """
        logger.info(f"Rendering target audio for experiment: {experiment_name}")
        logger.info(f"Target parameters: {target_parameters}")
        
        # Create temporary session manager for target rendering (without artifact manager to avoid conflicts)
        target_session_name = f"{experiment_name}_target"
        
        temp_session_manager = ExperimentSessionManager(
            reaper_project_path=self.reaper_project_path,
            param_manager=self.param_manager,
            experiment_name=target_session_name,
            target_audio_path=None,  # We're generating the target, not using existing
            artifact_manager=None  # Don't use artifact manager for target generation
        )
        
        try:
            # Create single-individual session for target rendering
            target_session_dir = temp_session_manager.create_generation_session(
                generation=0,  # Use generation 0 for target
                population_params=[target_parameters]
            )
            
            # Execute target rendering session
            success, audio_paths = temp_session_manager.execute_session(target_session_dir)
            
            if success and audio_paths:
                target_audio_path = audio_paths[0]
                logger.info(f"Target audio rendered successfully: {target_audio_path}")
                
                # Copy target audio to proper location using ArtifactManager
                final_target_path = target_audio_path
                if artifact_manager:
                    final_target_path = artifact_manager.set_target_audio(
                        target_audio_path=target_audio_path,
                        target_features=None  # Will be extracted later
                    )
                    logger.info(f"Target audio copied to: {final_target_path}")
                
                return final_target_path, target_parameters
                
            else:
                raise RuntimeError(f"Target audio rendering failed: {len(audio_paths)} files rendered")
                
        except Exception as e:
            logger.error(f"Error rendering target audio: {e}")
            raise
    
    def extract_target_features(self, target_audio_path: Path, 
                              feature_extractor, 
                              feature_weights) -> Dict:
        """
        Extract features from rendered target audio.
        
        Args:
            target_audio_path: Path to target audio file
            feature_extractor: Feature extraction interface
            feature_weights: Feature weighting configuration
            
        Returns:
            Dictionary of extracted features
        """
        logger.info(f"Extracting features from target audio: {target_audio_path}")
        
        if not target_audio_path.exists():
            raise FileNotFoundError(f"Target audio file not found: {target_audio_path}")
        
        try:
            # Extract scalar features
            target_features = feature_extractor.extract_scalar_features(
                audio_path=target_audio_path,
                feature_weights=feature_weights
            )
            
            logger.info(f"Extracted target features: {target_features}")
            return target_features
            
        except Exception as e:
            logger.error(f"Error extracting target features: {e}")
            raise
    
    def generate_complete_target(self,
                               target_parameters: SerumParameters,
                               experiment_name: str,
                               feature_extractor,
                               feature_weights,
                               artifact_manager: Optional[ArtifactManager] = None) -> Tuple[Path, Dict]:
        """
        Complete target generation workflow: render audio + extract features.
        
        Args:
            target_parameters: Serum parameters to render
            experiment_name: Name for the experiment
            feature_extractor: Feature extraction interface  
            feature_weights: Feature weighting configuration
            artifact_manager: Optional artifact manager for organization
            
        Returns:
            Tuple of (target_audio_path, target_features)
        """
        logger.info(f"Starting complete target generation for: {experiment_name}")
        
        # Step 1: Render target audio
        target_audio_path, rendered_params = self.render_target_audio(
            target_parameters=target_parameters,
            experiment_name=experiment_name,
            artifact_manager=artifact_manager
        )
        
        # Step 2: Extract features from target audio
        target_features = self.extract_target_features(
            target_audio_path=target_audio_path,
            feature_extractor=feature_extractor,
            feature_weights=feature_weights
        )
        
        # Step 3: Save target features to artifact manager if available (only if not already saved)
        if artifact_manager and "target" not in str(target_audio_path):
            target_audio_path = artifact_manager.set_target_audio(
                target_audio_path=target_audio_path,
                target_features=target_features.__dict__ if hasattr(target_features, '__dict__') else target_features
            )
        elif artifact_manager:
            # Just update the features if audio is already in target directory
            features_path = artifact_manager.target_dir / "features.json"
            import json
            with open(features_path, 'w') as f:
                json.dump(target_features.__dict__ if hasattr(target_features, '__dict__') else target_features, f, indent=2)
        
        logger.info(f"Complete target generation finished:")
        logger.info(f"  - Target audio: {target_audio_path}")
        logger.info(f"  - Target features: {target_features}")
        
        return target_audio_path, target_features


def main():
    """Test target audio generation."""
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    from serum_evolver import SerumParameterManager, LibrosaFeatureExtractor, FeatureWeights
    from experiment_config_generator import ExperimentConfigGenerator
    from artifact_manager import ArtifactManager
    
    # Initialize components
    fx_params_path = Path("/tmp/test_fx_parameters_single.json")
    reaper_project_path = project_root / "reaper"
    
    param_manager = SerumParameterManager(fx_params_path)
    feature_extractor = LibrosaFeatureExtractor()
    
    # Generate test experiment configuration
    config_generator = ExperimentConfigGenerator(param_manager)
    config = config_generator.generate_experiment_config(
        experiment_name="target_test_experiment",
        complexity="simple",
        feature_profile="balanced"
    )
    
    print(f"Generated config: {config.name}")
    print(f"Target parameters: {config.target_parameters}")
    
    # Initialize components for target generation
    target_generator = TargetAudioGenerator(reaper_project_path, param_manager)
    artifact_manager = ArtifactManager(config.name)
    
    # Generate complete target
    try:
        target_audio_path, target_features = target_generator.generate_complete_target(
            target_parameters=config.target_parameters,
            experiment_name=config.name,
            feature_extractor=feature_extractor,
            feature_weights=config.feature_weights,
            artifact_manager=artifact_manager
        )
        
        print(f"\n=== Target Generation Complete ===")
        print(f"Target audio: {target_audio_path}")
        print(f"Target features: {target_features}")
        print(f"Experiment structure: {artifact_manager.experiment_dir}")
        
    except Exception as e:
        print(f"Target generation failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()