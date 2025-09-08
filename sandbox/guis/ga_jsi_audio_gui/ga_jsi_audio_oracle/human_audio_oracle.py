"""Human audio comparison oracle with PyQt5 GUI interface for user selection."""

import pygame
from pathlib import Path
from typing import Any
import sys

try:
    from .pyqt_audio_oracle import PyQtAudioComparisonOracle
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    PyQtAudioComparisonOracle = None

sys.path.append(str(Path(__file__).parent.parent.parent / "choix_active_online"))
from choix_active_online_demo.comparison_oracle import ComparisonOracle


class HumanAudioComparisonOracle(ComparisonOracle):
    """Oracle that presents audio files to human user for comparison via PyQt5 GUI."""

    def __init__(self, window_title: str = "Audio Comparison"):
        """Initialize human audio comparison oracle.

        Args:
            window_title: Title for the comparison window
        """
        self.window_title = window_title
        self.comparison_count = 0

        if GUI_AVAILABLE:
            # Use PyQt5 implementation
            self._oracle = PyQtAudioComparisonOracle(window_title)
        else:
            # Fallback to console mode
            print("Warning: No GUI libraries available, using console mode")
            self._oracle = None

        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    def compare(self, item_a: Any, item_b: Any) -> bool:
        """Compare two audio items by presenting them to the user.

        Args:
            item_a: Path to first audio file
            item_b: Path to second audio file

        Returns:
            True if user selects item_a as better, False if item_b
        """
        self.comparison_count += 1

        if self._oracle:
            # Use PyQt GUI
            result = self._oracle.compare(item_a, item_b)
            # Sync comparison count (but don't overwrite, just increment)
            self.comparison_count = self._oracle.comparison_count
            return result
        else:
            # Use console fallback
            path_a = Path(item_a) if not isinstance(item_a, Path) else item_a
            path_b = Path(item_b) if not isinstance(item_b, Path) else item_b
            return self._console_fallback_comparison(path_a, path_b)

    def get_comparison_count(self) -> int:
        """Get the number of comparisons made.

        Returns:
            Number of comparisons performed
        """
        if self._oracle:
            return self._oracle.get_comparison_count()
        return self.comparison_count

    def reset_count(self) -> None:
        """Reset the comparison counter."""
        self.comparison_count = 0
        if self._oracle:
            self._oracle.reset_count()

    def _console_fallback_comparison(self, path_a: Path, path_b: Path) -> bool:
        """Fallback console-based comparison when GUI fails.

        Args:
            path_a: Path to first audio file
            path_b: Path to second audio file

        Returns:
            True if user selects A, False if user selects B
        """
        print(f"\n=== Audio Comparison #{self.comparison_count} ===")
        print(f"Option A: {path_a.name}")
        print(f"Option B: {path_b.name}")
        print("\nCommands:")
        print("  'a' - Play option A")
        print("  'b' - Play option B")
        print("  's' - Stop audio")
        print("  '1' - Choose option A")
        print("  '2' - Choose option B")

        while True:
            try:
                response = input("\nEnter command: ").strip().lower()

                if response == 'a':
                    self._play_audio(path_a)
                elif response == 'b':
                    self._play_audio(path_b)
                elif response == 's':
                    self._stop_audio()
                elif response == '1':
                    self._stop_audio()
                    print("Selected: Option A")
                    return True
                elif response == '2':
                    self._stop_audio()
                    print("Selected: Option B")
                    return False
                else:
                    print("Invalid command. Use 'a', 'b', 's', '1', or '2'")

            except KeyboardInterrupt:
                self._stop_audio()
                print("\nComparison interrupted, defaulting to A")
                return True

    def _play_audio(self, audio_path: Path) -> None:
        """Play audio file using pygame."""
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
            print(f"Playing: {audio_path.name}")
        except pygame.error as e:
            print(f"Error playing {audio_path.name}: {e}")

    def _stop_audio(self) -> None:
        """Stop audio playback."""
        try:
            pygame.mixer.music.stop()
            print("Audio stopped")
        except pygame.error as e:
            print(f"Error stopping audio: {e}")
