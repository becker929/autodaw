"""
Tests for main.py REAPER integration - these should FAIL before implementation.
"""

import pytest
import tempfile
import subprocess
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import main


class TestMainIntegration:
    """Tests for the main REAPER integration functions"""

    def test_prepare_session_config_works(self):
        """prepare_session_config should work and detect latest session"""
        # Should not raise NotImplementedError after implementation
        try:
            main.prepare_session_config()
            # Should create current_session.txt
            assert Path("current_session.txt").exists()
        except FileNotFoundError:
            # Expected if no session configs exist
            pass

    @patch('main.execute_reaper_with_session')
    def test_start_reaper_launches_reaper_with_session(self, mock_execute):
        """start_reaper should launch REAPER and execute the session"""
        mock_execute.return_value = Mock(returncode=0, stdout="", stderr="")

        # Should not raise NotImplementedError after implementation
        main.start_reaper()
        mock_execute.assert_called_once()

    def test_collect_session_artifacts_finds_rendered_audio(self):
        """collect_session_artifacts should find and return paths to rendered audio"""
        # Should not raise NotImplementedError after implementation
        artifacts = main.collect_session_artifacts()
        assert isinstance(artifacts, list)

    def test_check_session_artifacts_validates_audio_files(self):
        """check_session_artifacts should validate that audio files exist and are valid"""
        # Should not raise NotImplementedError after implementation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            audio_file = temp_path / "test.wav"
            audio_file.write_text("fake audio data")  # Non-empty file

            result = main.check_session_artifacts([audio_file])
            assert isinstance(result, bool)


class TestReaperExecution:
    """Tests for actual REAPER execution functionality"""

    @patch('main.execute_reaper_with_session')
    def test_reaper_execution_with_session_parameter(self, mock_execute):
        """REAPER should be launched with the correct session parameter"""
        mock_execute.return_value = Mock(returncode=0, stdout="", stderr="")

        # Should work after implementation
        main.start_reaper()
        mock_execute.assert_called_once()

    def test_session_file_detection(self):
        """Should detect which session file to use from session-configs directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            session_configs_dir = temp_path / "session-configs"
            session_configs_dir.mkdir()

            # Create a test session file
            test_session = {
                "session_name": "test_session",
                "render_configs": []
            }
            session_file = session_configs_dir / "test_session.json"
            with open(session_file, 'w') as f:
                json.dump(test_session, f)

            # Change to temp directory to test session detection
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                detected_session = main.detect_latest_session()
                assert detected_session == "test_session.json"
            finally:
                os.chdir(original_cwd)


class TestAudioCollection:
    """Tests for audio artifact collection"""

    def test_collect_rendered_audio_files(self):
        """Should collect all rendered audio files from renders directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            renders_dir = temp_path / "renders"
            renders_dir.mkdir()

            # Create mock render directories
            render_dir1 = renders_dir / "session_render1_20241201_120000_params"
            render_dir1.mkdir()
            audio_file1 = render_dir1 / "untitled.wav"
            audio_file1.touch()

            render_dir2 = renders_dir / "session_render2_20241201_120100_params"
            render_dir2.mkdir()
            audio_file2 = render_dir2 / "untitled.wav"
            audio_file2.touch()

            # Change to temp directory to test collection
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                audio_files = main.collect_session_artifacts()
                assert len(audio_files) == 2
                assert any("render1" in str(f) for f in audio_files)
                assert any("render2" in str(f) for f in audio_files)
            finally:
                os.chdir(original_cwd)

    def test_validate_audio_files_exist_and_are_valid(self):
        """Should validate that collected audio files exist and are valid"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a valid audio file (non-empty)
            audio_file = temp_path / "test.wav"
            audio_file.write_text("fake audio data")

            # Should work after implementation
            is_valid = main.check_session_artifacts([audio_file])
            assert is_valid is True


class TestLuaScriptParameterization:
    """Tests for passing parameters to Lua scripts"""

    def test_lua_script_accepts_session_parameter(self):
        """Lua script should accept session filename as parameter"""
        # This test verifies we can pass session name to Lua

        # Mock the Lua script execution
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

            # Should work after implementation
            result = main.execute_reaper_with_session("test_session.json")
            assert result.returncode == 0

    def test_lua_script_supports_parameterization(self):
        """Test that main.lua supports session parameterization via current_session.txt"""
        # Read the current main.lua
        main_lua_path = Path("reascripts/main.lua")
        if main_lua_path.exists():
            content = main_lua_path.read_text()

            # Should now support current_session.txt mechanism
            assert 'current_session.txt' in content, \
                "main.lua should support current_session.txt parameterization"
        else:
            pytest.skip("main.lua not found")


class TestEndToEndIntegration:
    """Tests for complete end-to-end functionality"""

    @patch('main.start_reaper')
    @patch('main.collect_session_artifacts')
    @patch('main.check_session_artifacts')
    @patch('main.prepare_session_config')
    def test_main_function_executes_complete_pipeline(self, mock_prepare, mock_start, mock_collect, mock_check):
        """main() should execute the complete pipeline without NotImplementedError"""
        # Mock all functions to avoid actual REAPER execution
        mock_collect.return_value = [Path("test.wav")]
        mock_check.return_value = True

        # Should work end-to-end after implementation
        main.main()

        # All steps should be called
        mock_prepare.assert_called_once()
        mock_start.assert_called_once()
        mock_collect.assert_called_once()
        mock_check.assert_called_once()

    @patch('main.start_reaper')
    @patch('main.collect_session_artifacts')
    @patch('main.check_session_artifacts')
    def test_main_function_calls_all_steps(self, mock_check, mock_collect, mock_start):
        """main() should call all required steps in order"""
        # Mock the functions to not raise NotImplementedError
        mock_collect.return_value = [Path("test.wav")]
        mock_check.return_value = True

        try:
            main.main()

            # After implementation, these should be called
            mock_start.assert_called_once()
            mock_collect.assert_called_once()
            mock_check.assert_called_once()
        except FileNotFoundError:
            # Expected if no session configs exist
            pass


class TestSessionConfigIntegration:
    """Tests for integration with GA-generated session configs"""

    def test_reads_ga_generated_session_configs(self):
        """Should be able to read and process GA-generated session configs"""
        # Create a GA-style session config
        ga_session_config = {
            "session_name": "basic_demo_gen_001",
            "render_configs": [
                {
                    "render_id": "basic_demo_gen_001_individual_000",
                    "tracks": [
                        {
                            "index": 0,
                            "name": "Serum Track",
                            "fx_chain": [{"name": "Serum", "plugin_name": "Serum"}]
                        }
                    ],
                    "parameters": [
                        {"track": "0", "fx": "Serum", "param": "A Octave", "value": 0.5364},
                        {"track": "0", "fx": "Serum", "param": "A Fine", "value": 0.4424}
                    ],
                    "midi_files": {"0": "test_melody.mid"},
                    "render_options": {"sample_rate": 44100, "channels": 2, "render_format": ""}
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            session_file = temp_path / "session-configs" / "basic_demo_gen_001.json"
            session_file.parent.mkdir(parents=True)

            with open(session_file, 'w') as f:
                json.dump(ga_session_config, f, indent=2)

            # Change to temp directory to test session config processing
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                result = main.process_session_config("basic_demo_gen_001.json")
                assert result is not None
                assert result["session_name"] == "basic_demo_gen_001"
                assert "render_configs" in result
            finally:
                os.chdir(original_cwd)
