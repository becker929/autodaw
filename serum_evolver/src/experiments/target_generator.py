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

from ..genetics.genetics import Solution
from .artifact_manager import ArtifactManager
from typing import Protocol

logger = logging.getLogger(__name__)


class AudioRenderer(Protocol):
    """Protocol for audio rendering backends."""

    def render_audio(self, parameters: Solution, experiment_name: str) -> Tuple[bool, list[Path]]:
        """Render audio for given parameters.

        Returns:
            Tuple of (success, list_of_rendered_paths)
        """
        ...


class TargetAudioGenerator:
    """Generates target audio by rendering specific parameter configurations."""

    def __init__(self, audio_renderer: AudioRenderer, param_manager=None):
        """
        Initialize target audio generator.

        Args:
            audio_renderer: Audio rendering backend (injected dependency)
            param_manager: Parameter manager for validation
        """
        self.audio_renderer = audio_renderer
        self.param_manager = param_manager

        logger.info(f"Initialized TargetAudioGenerator with renderer: {type(audio_renderer).__name__}")

    def render_target_audio(self,
                           target_parameters: Solution,
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

        try:
            # Use injected audio renderer
            success, audio_paths = self.audio_renderer.render_audio(target_parameters, experiment_name)

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
                raise RuntimeError(f"Target audio rendering failed: {len(audio_paths) if audio_paths else 0} files rendered")

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
                               target_parameters: Solution,
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


class MockAudioRenderer:
    """Mock audio renderer for testing and demos."""

    def render_audio(self, parameters: Solution, experiment_name: str) -> Tuple[bool, list[Path]]:
        """Mock render implementation."""
        mock_path = Path(f"/tmp/mock_audio_{experiment_name}_{parameters.octave}_{parameters.fine}.wav")
        return True, [mock_path]


def main():
    """Demo target audio generation."""
    from pathlib import Path

    # Create mock components using dependency injection
    from ..genetics.genetics import Solution
    from .artifact_manager import ArtifactManager

    # Mock test data
    target_parameters = Solution(octave=0.5, fine=0.2)
    experiment_name = "target_test_experiment"

    # Initialize components with dependency injection
    mock_renderer = MockAudioRenderer()
    target_generator = TargetAudioGenerator(audio_renderer=mock_renderer)
    artifact_manager = ArtifactManager(experiment_name)

    print(f"Target parameters: {target_parameters}")
    print(f"Experiment: {experiment_name}")
    print(f"Demo complete - using proper dependency injection")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
