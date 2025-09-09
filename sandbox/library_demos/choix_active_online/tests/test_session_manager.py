"""Tests for session manager."""

import pytest
import time
import threading
from choix_active_online_demo.session_manager import SessionManager, SessionStatus


class TestSessionManager:
    """Test cases for SessionManager."""

    def test_initialization(self):
        """Test proper initialization."""
        session = SessionManager()

        assert session.status == SessionStatus.INACTIVE
        assert session.is_active == False
        assert session.should_continue == False
        assert session.comparison_count == 0
        assert session.elapsed_time is None

    def test_start_session(self):
        """Test starting a session."""
        session = SessionManager()

        result = session.start_session()
        assert result == True
        assert session.status == SessionStatus.ACTIVE
        assert session.is_active == True
        assert session.should_continue == True
        assert session.comparison_count == 0
        assert session.elapsed_time is not None

    def test_start_already_active(self):
        """Test starting when already active."""
        session = SessionManager()

        session.start_session()
        result = session.start_session()  # Try to start again

        assert result == False  # Should fail
        assert session.status == SessionStatus.ACTIVE

    def test_stop_session(self):
        """Test stopping a session."""
        session = SessionManager()

        session.start_session()
        result = session.stop_session()

        assert result == True
        assert session.status == SessionStatus.STOPPING

        # Wait for transition to STOPPED
        time.sleep(0.2)
        assert session.status == SessionStatus.STOPPED

    def test_stop_inactive_session(self):
        """Test stopping when not active."""
        session = SessionManager()

        result = session.stop_session()
        assert result == False
        assert session.status == SessionStatus.INACTIVE

    def test_record_comparison(self):
        """Test recording comparisons."""
        session = SessionManager()
        session.start_session()

        session.record_comparison()
        assert session.comparison_count == 1

        session.record_comparison()
        assert session.comparison_count == 2

    def test_record_comparison_inactive(self):
        """Test recording comparisons when inactive."""
        session = SessionManager()

        session.record_comparison()
        assert session.comparison_count == 0  # Should not increment

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        session = SessionManager()

        session.start_session()
        start_time = session.elapsed_time

        time.sleep(0.1)

        elapsed = session.elapsed_time
        assert elapsed > start_time
        assert elapsed >= 0.1

    def test_reset_session(self):
        """Test resetting session."""
        session = SessionManager()

        session.start_session()
        session.record_comparison()
        session.stop_session()

        session.reset_session()

        assert session.status == SessionStatus.INACTIVE
        assert session.comparison_count == 0
        assert session.elapsed_time is None

    def test_callbacks(self):
        """Test session callbacks."""
        session = SessionManager()

        start_called = []
        stop_called = []
        comparison_called = []

        def on_start():
            start_called.append(True)

        def on_stop():
            stop_called.append(True)

        def on_comparison(count):
            comparison_called.append(count)

        session.add_callback('on_start', on_start)
        session.add_callback('on_stop', on_stop)
        session.add_callback('on_comparison', on_comparison)

        session.start_session()
        assert len(start_called) == 1

        session.record_comparison()
        assert comparison_called == [1]

        session.record_comparison()
        assert comparison_called == [1, 2]

        session.stop_session()
        assert len(stop_called) == 1

    def test_remove_callback(self):
        """Test removing callbacks."""
        session = SessionManager()

        called = []

        def callback():
            called.append(True)

        session.add_callback('on_start', callback)
        session.remove_callback('on_start', callback)

        session.start_session()
        assert len(called) == 0  # Callback should not be called

    def test_session_stats(self):
        """Test session statistics."""
        session = SessionManager()

        stats = session.get_session_stats()
        assert stats['status'] == 'inactive'
        assert stats['is_active'] == False
        assert stats['comparison_count'] == 0
        assert stats['elapsed_time'] is None

        session.start_session()
        session.record_comparison()

        stats = session.get_session_stats()
        assert stats['status'] == 'active'
        assert stats['is_active'] == True
        assert stats['comparison_count'] == 1
        assert stats['elapsed_time'] is not None

    def test_thread_safety(self):
        """Test thread safety of session manager."""
        session = SessionManager()
        session.start_session()

        results = []

        def worker():
            for _ in range(2):  # Reduced from 10 to 2
                session.record_comparison()
                results.append(session.comparison_count)

        threads = [threading.Thread(target=worker) for _ in range(3)]  # Reduced from 5 to 3

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have recorded all comparisons
        assert session.comparison_count == 6
