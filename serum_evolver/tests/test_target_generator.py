"""Unit tests for target audio generator."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from serum_evolver.src.experiments.target_generator import TargetAudioGenerator


class TestTargetAudioGenerator:
    """Test cases for TargetAudioGenerator."""

    def test_initialization(self):
        """Test target generator initialization."""
        mock_renderer = Mock()
        param_manager = Mock()

        generator = TargetAudioGenerator(mock_renderer, param_manager)

        assert generator.audio_renderer == mock_renderer
        assert generator.param_manager == param_manager

    def test_render_target_audio_success(self):
        """Test successful target audio rendering."""
        mock_renderer = Mock()
        mock_renderer.render_audio.return_value = (True, [Path("/test/audio.wav")])

        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        target_params = Mock()
        experiment_name = "test_experiment"

        result_path, result_params = generator.render_target_audio(
            target_parameters=target_params,
            experiment_name=experiment_name
        )

        assert result_path == Path("/test/audio.wav")
        assert result_params == target_params
        mock_renderer.render_audio.assert_called_once_with(target_params, experiment_name)

    def test_render_target_audio_with_artifact_manager(self):
        """Test target audio rendering with artifact manager."""
        mock_renderer = Mock()
        mock_renderer.render_audio.return_value = (True, [Path("/test/audio.wav")])

        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        # Mock artifact manager
        artifact_manager = Mock()
        artifact_manager.set_target_audio.return_value = Path("/test/target/reference.wav")

        target_params = Mock()
        experiment_name = "test_experiment"

        result_path, result_params = generator.render_target_audio(
            target_parameters=target_params,
            experiment_name=experiment_name,
            artifact_manager=artifact_manager
        )

        assert result_path == Path("/test/target/reference.wav")
        artifact_manager.set_target_audio.assert_called_once_with(
            target_audio_path=Path("/test/audio.wav"),
            target_features=None
        )

    def test_render_target_audio_failure(self):
        """Test target audio rendering failure."""
        mock_renderer = Mock()
        mock_renderer.render_audio.return_value = (False, [])  # Render failure

        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        target_params = Mock()
        experiment_name = "test_experiment"

        with pytest.raises(RuntimeError, match="Target audio rendering failed"):
            generator.render_target_audio(
                target_parameters=target_params,
                experiment_name=experiment_name
            )

    def test_extract_target_features_success(self):
        """Test successful feature extraction."""
        mock_renderer = Mock()
        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        # Mock target audio path
        target_audio_path = Mock()
        target_audio_path.exists.return_value = True

        # Mock feature extractor
        feature_extractor = Mock()
        expected_features = {"spectral_centroid": 2000.0, "mfcc": [1, 2, 3]}
        feature_extractor.extract_scalar_features.return_value = expected_features

        feature_weights = Mock()

        result = generator.extract_target_features(
            target_audio_path=target_audio_path,
            feature_extractor=feature_extractor,
            feature_weights=feature_weights
        )

        assert result == expected_features
        feature_extractor.extract_scalar_features.assert_called_once_with(
            audio_path=target_audio_path,
            feature_weights=feature_weights
        )

    def test_extract_target_features_file_not_found(self):
        """Test feature extraction with missing file."""
        mock_renderer = Mock()
        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        # Mock target audio path that doesn't exist
        target_audio_path = Mock()
        target_audio_path.exists.return_value = False

        feature_extractor = Mock()
        feature_weights = Mock()

        with pytest.raises(FileNotFoundError):
            generator.extract_target_features(
                target_audio_path=target_audio_path,
                feature_extractor=feature_extractor,
                feature_weights=feature_weights
            )

    def test_extract_target_features_extraction_error(self):
        """Test feature extraction with extraction error."""
        mock_renderer = Mock()
        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        # Mock target audio path
        target_audio_path = Mock()
        target_audio_path.exists.return_value = True

        # Mock feature extractor to raise exception
        feature_extractor = Mock()
        feature_extractor.extract_scalar_features.side_effect = Exception("Extraction failed")

        feature_weights = Mock()

        with pytest.raises(Exception, match="Extraction failed"):
            generator.extract_target_features(
                target_audio_path=target_audio_path,
                feature_extractor=feature_extractor,
                feature_weights=feature_weights
            )

    @patch.object(TargetAudioGenerator, 'render_target_audio')
    @patch.object(TargetAudioGenerator, 'extract_target_features')
    def test_generate_complete_target_success(self, mock_extract, mock_render):
        """Test complete target generation workflow."""
        mock_renderer = Mock()
        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        # Mock render and extract methods
        target_audio_path = Path("/test/target.wav")
        rendered_params = Mock()
        mock_render.return_value = (target_audio_path, rendered_params)

        target_features = {"spectral_centroid": 2000.0}
        mock_extract.return_value = target_features

        target_parameters = Mock()
        experiment_name = "test_experiment"
        feature_extractor = Mock()
        feature_weights = Mock()

        result_path, result_features = generator.generate_complete_target(
            target_parameters=target_parameters,
            experiment_name=experiment_name,
            feature_extractor=feature_extractor,
            feature_weights=feature_weights
        )

        assert result_path == target_audio_path
        assert result_features == target_features

        mock_render.assert_called_once_with(
            target_parameters=target_parameters,
            experiment_name=experiment_name,
            artifact_manager=None
        )
        mock_extract.assert_called_once_with(
            target_audio_path=target_audio_path,
            feature_extractor=feature_extractor,
            feature_weights=feature_weights
        )

    @patch.object(TargetAudioGenerator, 'render_target_audio')
    @patch.object(TargetAudioGenerator, 'extract_target_features')
    @patch('builtins.open')
    @patch('json.dump')
    def test_generate_complete_target_with_artifact_manager(self, mock_json_dump, mock_open, mock_extract, mock_render):
        """Test complete target generation with artifact manager."""
        mock_renderer = Mock()
        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        # Mock render and extract methods
        target_audio_path = Path("/test/target/reference.wav")  # Already in target directory
        rendered_params = Mock()
        mock_render.return_value = (target_audio_path, rendered_params)

        target_features = {"spectral_centroid": 2000.0}
        mock_extract.return_value = target_features

        # Mock artifact manager
        artifact_manager = Mock()
        artifact_manager.target_dir = Path("/test/target")

        target_parameters = Mock()
        experiment_name = "test_experiment"
        feature_extractor = Mock()
        feature_weights = Mock()

        result_path, result_features = generator.generate_complete_target(
            target_parameters=target_parameters,
            experiment_name=experiment_name,
            feature_extractor=feature_extractor,
            feature_weights=feature_weights,
            artifact_manager=artifact_manager
        )

        assert result_path == target_audio_path
        assert result_features == target_features

        # Should save features to artifact manager
        mock_open.assert_called()
        mock_json_dump.assert_called()

    @patch.object(TargetAudioGenerator, 'render_target_audio')
    @patch.object(TargetAudioGenerator, 'extract_target_features')
    def test_generate_complete_target_with_artifact_manager_new_audio(self, mock_extract, mock_render):
        """Test complete target generation with artifact manager for new audio."""
        mock_renderer = Mock()
        param_manager = Mock()
        generator = TargetAudioGenerator(mock_renderer, param_manager)

        # Mock render and extract methods
        original_path = Path("/test/audio.wav")  # Not in target directory
        rendered_params = Mock()
        mock_render.return_value = (original_path, rendered_params)

        target_features = {"spectral_centroid": 2000.0}
        mock_extract.return_value = target_features

        # Mock artifact manager
        artifact_manager = Mock()
        final_path = Path("/test/target/reference.wav")
        artifact_manager.set_target_audio.return_value = final_path

        target_parameters = Mock()
        experiment_name = "test_experiment"
        feature_extractor = Mock()
        feature_weights = Mock()

        result_path, result_features = generator.generate_complete_target(
            target_parameters=target_parameters,
            experiment_name=experiment_name,
            feature_extractor=feature_extractor,
            feature_weights=feature_weights,
            artifact_manager=artifact_manager
        )

        assert result_path == final_path
        assert result_features == target_features

        # Should call set_target_audio
        artifact_manager.set_target_audio.assert_called_once_with(
            target_audio_path=original_path,
            target_features=target_features
        )


if __name__ == "__main__":
    pytest.main([__file__])
