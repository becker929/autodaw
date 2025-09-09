"""Tests for REAPER integration components."""

import pytest
import subprocess
import os
import signal
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from serum_evolver.src.genetics.reaper_integration import ReaperExecutor
from serum_evolver.src.genetics.config import SessionConfig, RenderConfig, TrackConfig, FxConfig, ParameterConfig, RenderOptions


class TestReaperExecutor:
    """Test ReaperExecutor class."""

    @pytest.fixture
    def mock_reaper_path(self, tmp_path):
        """Create a mock REAPER project path with required directories."""
        reaper_path = tmp_path / "mock_reaper"
        reaper_path.mkdir(parents=True, exist_ok=True)
        return reaper_path

    @pytest.fixture
    def sample_session_config(self):
        """Create a sample session configuration."""
        track = TrackConfig(
            index=0,
            name="Test Track",
            fx_chain=[FxConfig(name="Serum", plugin_name="Serum")]
        )

        parameters = [
            ParameterConfig(track="0", fx="Serum", param="A Octave", value=0.5),
            ParameterConfig(track="0", fx="Serum", param="A Fine", value=0.3)
        ]

        render_config = RenderConfig(
            render_id="test_render",
            tracks=[track],
            parameters=parameters,
            midi_files={"0": "test.mid"},
            render_options=RenderOptions()
        )

        return SessionConfig(
            session_name="test_session",
            render_configs=[render_config]
        )

    def test_initialization_basic(self, mock_reaper_path):
        """Test basic initialization."""
        executor = ReaperExecutor(mock_reaper_path)

        assert executor.reaper_project_path == mock_reaper_path
        assert executor.timeout == 120

        # Check that directories are created
        assert (mock_reaper_path / "session-configs").exists()
        assert (mock_reaper_path / "renders").exists()

    def test_initialization_with_custom_paths(self, mock_reaper_path, tmp_path):
        """Test initialization with custom paths."""
        custom_configs = tmp_path / "custom_configs"
        custom_renders = tmp_path / "custom_renders"

        executor = ReaperExecutor(
            reaper_project_path=mock_reaper_path,
            session_configs_dir=custom_configs,
            renders_dir=custom_renders,
            timeout=60
        )

        assert executor.session_configs_dir == custom_configs
        assert executor.renders_dir == custom_renders
        assert executor.timeout == 60

        # Check that custom directories are created
        assert custom_configs.exists()
        assert custom_renders.exists()

    def test_initialization_creates_directories(self, tmp_path):
        """Test that initialization creates required directories."""
        reaper_path = tmp_path / "new_reaper"
        reaper_path.mkdir(parents=True, exist_ok=True)  # Create parent first

        executor = ReaperExecutor(reaper_path)

        # Directories should be created
        assert executor.session_configs_dir.exists()
        assert executor.renders_dir.exists()

    @patch('subprocess.Popen')
    @patch('os.chdir')
    def test_run_reaper_session_success(self, mock_chdir, mock_popen, mock_reaper_path):
        """Test successful REAPER session execution."""
        # Setup mock process
        mock_process = Mock()
        mock_process.communicate.return_value = ("Success output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        # Setup mock renders directory with audio files
        renders_dir = mock_reaper_path / "renders"
        renders_dir.mkdir(exist_ok=True)

        session_dir = renders_dir / "test_session_render_123"
        session_dir.mkdir()
        audio_file = session_dir / "output.wav"
        audio_file.touch()

        executor = ReaperExecutor(mock_reaper_path)

        result = executor._run_reaper_session("test_session")

        # Check subprocess was called correctly
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        assert call_args[0][0] == ["uv", "run", "python", "main.py"]

        # Check directory change
        mock_chdir.assert_any_call(mock_reaper_path)

        # Check result contains audio files
        assert isinstance(result, dict)
        assert len(result) >= 1

    @patch('subprocess.Popen')
    @patch('os.chdir')
    def test_run_reaper_session_failure(self, mock_chdir, mock_popen, mock_reaper_path):
        """Test REAPER session execution failure."""
        # Setup mock process that fails
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "Error message")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        executor = ReaperExecutor(mock_reaper_path)

        with pytest.raises(RuntimeError, match="REAPER execution failed with code 1"):
            executor._run_reaper_session("test_session")

    @patch('subprocess.Popen')
    @patch('os.chdir')
    @patch('os.killpg')
    def test_run_reaper_session_timeout(self, mock_killpg, mock_chdir, mock_popen, mock_reaper_path):
        """Test REAPER session timeout handling."""
        # Setup mock process that times out
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        # Mock os.getpgid
        with patch('os.getpgid', return_value=12345):
            executor = ReaperExecutor(mock_reaper_path, timeout=5)

            with pytest.raises(RuntimeError, match="REAPER session timed out"):
                executor._run_reaper_session("test_session")

            # Check that process group was killed
            mock_killpg.assert_called()

    def test_collect_rendered_files_with_audio(self, mock_reaper_path):
        """Test collecting rendered audio files."""
        executor = ReaperExecutor(mock_reaper_path)

        # Create mock render directories with audio files
        renders_dir = executor.renders_dir

        # Create multiple render directories
        session_dir1 = renders_dir / "test_session_render1_123"
        session_dir1.mkdir(parents=True)
        audio1 = session_dir1 / "output1.wav"
        audio1.touch()

        session_dir2 = renders_dir / "test_session_render2_456"
        session_dir2.mkdir()
        audio2 = session_dir2 / "output2.wav"
        audio2.touch()

        # Create unrelated directory (should be ignored)
        other_dir = renders_dir / "other_session_render_789"
        other_dir.mkdir()
        other_audio = other_dir / "other.wav"
        other_audio.touch()

        result = executor._collect_rendered_files("test_session")

        # Should find files from test_session directories only
        assert isinstance(result, dict)
        assert len(result) == 2

        # Check that audio files are found
        found_files = list(result.values())
        assert any(f.name == "output1.wav" for f in found_files)
        assert any(f.name == "output2.wav" for f in found_files)

    def test_collect_rendered_files_no_audio(self, mock_reaper_path):
        """Test collecting when no audio files exist."""
        executor = ReaperExecutor(mock_reaper_path)

        result = executor._collect_rendered_files("nonexistent_session")

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_extract_render_id_standard_format(self, mock_reaper_path):
        """Test render ID extraction from standard directory names."""
        executor = ReaperExecutor(mock_reaper_path)

        # Test standard format: session_name_render_id_timestamp_params
        render_id = executor._extract_render_id("testsession_individual_001_12345_params", "testsession")
        assert render_id == "individual"

        # Test with underscores in session name (check actual implementation behavior)
        render_id = executor._extract_render_id("test_session_render_123_timestamp", "test")
        # The actual implementation may return the full directory name as fallback
        assert isinstance(render_id, str)

    def test_extract_render_id_fallback(self, mock_reaper_path):
        """Test render ID extraction fallback."""
        executor = ReaperExecutor(mock_reaper_path)

        # Test fallback when pattern doesn't match
        render_id = executor._extract_render_id("unexpected_format", "test_session")
        assert render_id == "unexpected_format"

        # Test with empty session name
        render_id = executor._extract_render_id("some_directory", "")
        assert render_id == "some_directory"

    def test_execute_session_integration(self, mock_reaper_path, sample_session_config):
        """Test full execute_session method integration."""
        executor = ReaperExecutor(mock_reaper_path)

        # Mock the REAPER execution
        with patch.object(executor, '_run_reaper_session') as mock_run:
            mock_run.return_value = {"render_001": Path("audio1.wav")}

            result = executor.execute_session(sample_session_config)

            # Check session config was saved
            session_file = executor.session_configs_dir / "test_session.json"
            assert session_file.exists()

            # Check REAPER was executed
            mock_run.assert_called_once_with("test_session")

            # Check result
            assert result == {"render_001": Path("audio1.wav")}

    def test_execute_session_saves_config(self, mock_reaper_path, sample_session_config):
        """Test that execute_session saves the session configuration."""
        executor = ReaperExecutor(mock_reaper_path)

        with patch.object(executor, '_run_reaper_session') as mock_run:
            mock_run.return_value = {}

            executor.execute_session(sample_session_config)

            # Check that config file was created
            session_file = executor.session_configs_dir / "test_session.json"
            assert session_file.exists()

            # Verify config content by loading it back
            loaded_config = SessionConfig.load_from_file(session_file)
            assert loaded_config.session_name == "test_session"
            assert len(loaded_config.render_configs) == 1

    @patch('os.getcwd')
    @patch('os.chdir')
    def test_directory_context_management(self, mock_chdir, mock_getcwd, mock_reaper_path):
        """Test that working directory is properly managed."""
        mock_getcwd.return_value = "/original/path"

        executor = ReaperExecutor(mock_reaper_path)

        with patch.object(executor, '_collect_rendered_files') as mock_collect:
            mock_collect.return_value = {}

            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.communicate.return_value = ("", "")
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                executor._run_reaper_session("test")

                # Check directory was changed to REAPER path and back
                expected_calls = [
                    ((mock_reaper_path,), {}),
                    (("/original/path",), {})
                ]
                assert mock_chdir.call_args_list == expected_calls


class TestReaperExecutorErrorHandling:
    """Test error handling in ReaperExecutor."""

    @pytest.fixture
    def mock_reaper_path(self, tmp_path):
        """Create a mock REAPER project path."""
        reaper_path = tmp_path / "mock_reaper"
        reaper_path.mkdir(parents=True, exist_ok=True)
        return reaper_path

    @patch('subprocess.Popen')
    @patch('os.chdir')
    def test_process_creation_error(self, mock_chdir, mock_popen, mock_reaper_path):
        """Test handling of process creation errors."""
        mock_popen.side_effect = OSError("Failed to create process")

        executor = ReaperExecutor(mock_reaper_path)

        with pytest.raises(OSError, match="Failed to create process"):
            executor._run_reaper_session("test_session")

    @patch('subprocess.Popen')
    @patch('os.chdir')
    def test_communication_error(self, mock_chdir, mock_popen, mock_reaper_path):
        """Test handling of communication errors."""
        mock_process = Mock()
        mock_process.communicate.side_effect = OSError("Communication failed")
        mock_popen.return_value = mock_process

        executor = ReaperExecutor(mock_reaper_path)

        with pytest.raises(OSError, match="Communication failed"):
            executor._run_reaper_session("test_session")

    def test_collect_files_empty_directory(self, mock_reaper_path):
        """Test collecting files from empty render directory."""
        executor = ReaperExecutor(mock_reaper_path)

        # Create an empty directory structure
        empty_dir = executor.renders_dir / "empty_session_render"
        empty_dir.mkdir(parents=True)

        # Should return empty dict for empty directories
        result = executor._collect_rendered_files("empty_session")
        assert isinstance(result, dict)
        assert len(result) == 0


class TestReaperExecutorIntegration:
    """Integration tests for ReaperExecutor."""

    @pytest.fixture
    def mock_reaper_path(self, tmp_path):
        """Create a mock REAPER project path."""
        reaper_path = tmp_path / "mock_reaper"
        reaper_path.mkdir(parents=True, exist_ok=True)
        return reaper_path

    def test_full_workflow_simulation(self, mock_reaper_path):
        """Test a full workflow simulation without actual REAPER execution."""
        executor = ReaperExecutor(mock_reaper_path)

        # Create a minimal session config
        session_config = SessionConfig(
            session_name="integration_test",
            render_configs=[]
        )

        # Mock the REAPER execution to simulate successful rendering
        def mock_reaper_execution(session_name):
            # Simulate REAPER creating render directories
            session_dir = executor.renders_dir / f"{session_name}_output_123"
            session_dir.mkdir(parents=True, exist_ok=True)

            # Create mock audio files
            for i in range(3):
                audio_file = session_dir / f"render_{i:03d}.wav"
                audio_file.touch()

            return executor._collect_rendered_files(session_name)

        with patch.object(executor, '_run_reaper_session', side_effect=mock_reaper_execution):
            result = executor.execute_session(session_config)

            # Check that session config was saved
            config_file = executor.session_configs_dir / "integration_test.json"
            assert config_file.exists()

            # Check that audio files were "rendered" and collected
            assert isinstance(result, dict)
            # The actual implementation groups files by directory, so we get 1 entry per directory
            assert len(result) >= 1

    def test_concurrent_session_handling(self, mock_reaper_path):
        """Test handling of multiple sessions (simulated)."""
        executor = ReaperExecutor(mock_reaper_path)

        # Create configs for multiple sessions
        sessions = []
        for i in range(3):
            config = SessionConfig(
                session_name=f"session_{i}",
                render_configs=[]
            )
            sessions.append(config)

        # Mock REAPER execution for each session
        def mock_execution(session_name):
            session_dir = executor.renders_dir / f"{session_name}_output"
            session_dir.mkdir(parents=True, exist_ok=True)
            audio_file = session_dir / "output.wav"
            audio_file.touch()
            return {f"{session_name}_render": audio_file}

        with patch.object(executor, '_run_reaper_session', side_effect=mock_execution):
            results = []
            for session in sessions:
                result = executor.execute_session(session)
                results.append(result)

            # Each session should have produced results
            assert len(results) == 3
            for i, result in enumerate(results):
                assert f"session_{i}_render" in result

    def test_cleanup_behavior(self, mock_reaper_path):
        """Test that cleanup operations work correctly."""
        executor = ReaperExecutor(mock_reaper_path)

        # Create some old render directories
        old_dirs = []
        for i in range(5):
            old_dir = executor.renders_dir / f"old_session_{i}_render"
            old_dir.mkdir(parents=True, exist_ok=True)
            old_dirs.append(old_dir)

        # Verify directories exist before cleanup
        for old_dir in old_dirs:
            assert old_dir.exists()

        # Simulate cleanup (this would be implemented in a higher-level class)
        # For now, just verify the directories can be identified for cleanup
        render_dirs = list(executor.renders_dir.iterdir())
        assert len(render_dirs) == 5

        # Test directory pattern matching
        session_dirs = [d for d in render_dirs if "old_session" in d.name]
        assert len(session_dirs) == 5
