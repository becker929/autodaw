"""PyQt5-based human audio comparison oracle."""

import sys
import pygame
from pathlib import Path
from typing import Any

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                QHBoxLayout, QPushButton, QLabel, QFrame, QMessageBox)
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

sys.path.append(str(Path(__file__).parent.parent.parent / "choix_active_online"))
from choix_active_online_demo.comparison_oracle import ComparisonOracle


class PyQtAudioComparisonOracle(ComparisonOracle):
    """PyQt5-based human audio comparison oracle."""
    
    def __init__(self, window_title: str = "Audio Comparison"):
        """Initialize PyQt audio comparison oracle.
        
        Args:
            window_title: Title for the comparison window
        """
        self.window_title = window_title
        self.comparison_count = 0
        self._result = None
        self._app = None
        self._window = None
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        if not PYQT_AVAILABLE:
            raise ImportError("PyQt5 is not available")

    def compare(self, item_a: Any, item_b: Any) -> bool:
        """Compare two audio items by presenting them to the user.

        Args:
            item_a: Path to first audio file
            item_b: Path to second audio file

        Returns:
            True if user selects item_a as better, False if item_b
        """
        self.comparison_count += 1

        # Convert to Path objects if needed
        path_a = Path(item_a) if not isinstance(item_a, Path) else item_a
        path_b = Path(item_b) if not isinstance(item_b, Path) else item_b

        # Validate files exist
        if not path_a.exists():
            print(f"Warning: Audio file A not found: {path_a}")
            return False
        if not path_b.exists():
            print(f"Warning: Audio file B not found: {path_b}")
            return True

        print(f"\n=== Audio Comparison #{self.comparison_count} ===")
        print(f"Option A: {path_a.name}")
        print(f"Option B: {path_b.name}")

                # Create and run the comparison GUI
        return self._run_comparison_gui(path_a, path_b)
    
    def _run_comparison_gui(self, path_a: Path, path_b: Path) -> bool:
        """Run the PyQt GUI for audio comparison.
        
        Args:
            path_a: Path to first audio file
            path_b: Path to second audio file
            
        Returns:
            True if user selects A, False if user selects B
        """
        self._result = None
        
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            self._app = QApplication([])  # Use empty list instead of sys.argv
        else:
            self._app = QApplication.instance()
        
        # Create the main window
        self._window = AudioComparisonWindow(path_a, path_b, self.comparison_count)
        self._window.choice_made.connect(self._on_choice_made)
        self._window.show()
        
        # Run the event loop until choice is made
        while self._result is None:
            self._app.processEvents()
            if not self._window.isVisible():
                # Window was closed without choice
                self._result = True  # Default to A
                break
        
        # Clean up
        if self._window:
            self._window.close()
            self._window.deleteLater()
            self._window = None
        
        # Don't store the app reference to avoid pickle issues
        self._app = None
        
        return self._result

    def _on_choice_made(self, chose_a: bool):
        """Handle choice signal from window.

        Args:
            chose_a: True if user chose A, False if chose B
        """
        self._result = chose_a
        choice_label = "A" if chose_a else "B"
        print(f"User selected: Option {choice_label}")

    def get_comparison_count(self) -> int:
        """Get the number of comparisons made.

        Returns:
            Number of comparisons performed
        """
        return self.comparison_count

    def reset_count(self) -> None:
        """Reset the comparison counter."""
        self.comparison_count = 0


class AudioComparisonWindow(QMainWindow):
    """PyQt5 window for audio comparison."""

    from PyQt5.QtCore import pyqtSignal
    choice_made = pyqtSignal(bool)

    def __init__(self, path_a: Path, path_b: Path, comparison_num: int):
        """Initialize the comparison window.

        Args:
            path_a: Path to first audio file
            path_b: Path to second audio file
            comparison_num: Comparison number for display
        """
        super().__init__()
        self.path_a = path_a
        self.path_b = path_b
        self.comparison_num = comparison_num
        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Audio Evolution - Make Your Choice")
        self.setFixedSize(600, 400)
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QLabel { color: white; }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #606060;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #505050; }
            QPushButton:pressed { background-color: #303030; }
            QFrame {
                background-color: #353535;
                border: 1px solid #606060;
                border-radius: 8px;
                margin: 5px;
            }
        """)

        # Center the window
        self._center_window()

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Title
        title_label = QLabel(f"Audio Comparison #{self.comparison_num}")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Instructions
        instructions = QLabel("Listen to both audio samples and choose which one you prefer:")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        # Options layout
        options_layout = QHBoxLayout()
        options_layout.setSpacing(20)

        # Option A frame
        a_frame = QFrame()
        a_layout = QVBoxLayout(a_frame)
        a_layout.setSpacing(10)
        a_layout.setContentsMargins(20, 20, 20, 20)

        a_title = QLabel("Option A")
        a_title.setAlignment(Qt.AlignCenter)
        a_title_font = QFont()
        a_title_font.setPointSize(14)
        a_title_font.setBold(True)
        a_title.setFont(a_title_font)
        a_layout.addWidget(a_title)

        a_filename = QLabel(self.path_a.name)
        a_filename.setAlignment(Qt.AlignCenter)
        a_filename.setWordWrap(True)
        a_layout.addWidget(a_filename)

        a_play_btn = QPushButton("▶ Play A")
        a_play_btn.clicked.connect(lambda: self._play_audio(self.path_a))
        a_layout.addWidget(a_play_btn)

        a_choose_btn = QPushButton("Choose A")
        a_choose_btn.setStyleSheet("QPushButton { background-color: #2d5a2d; } QPushButton:hover { background-color: #3d6a3d; }")
        a_choose_btn.clicked.connect(lambda: self._make_choice(True))
        a_layout.addWidget(a_choose_btn)

        options_layout.addWidget(a_frame)

        # Option B frame
        b_frame = QFrame()
        b_layout = QVBoxLayout(b_frame)
        b_layout.setSpacing(10)
        b_layout.setContentsMargins(20, 20, 20, 20)

        b_title = QLabel("Option B")
        b_title.setAlignment(Qt.AlignCenter)
        b_title_font = QFont()
        b_title_font.setPointSize(14)
        b_title_font.setBold(True)
        b_title.setFont(b_title_font)
        b_layout.addWidget(b_title)

        b_filename = QLabel(self.path_b.name)
        b_filename.setAlignment(Qt.AlignCenter)
        b_filename.setWordWrap(True)
        b_layout.addWidget(b_filename)

        b_play_btn = QPushButton("▶ Play B")
        b_play_btn.clicked.connect(lambda: self._play_audio(self.path_b))
        b_layout.addWidget(b_play_btn)

        b_choose_btn = QPushButton("Choose B")
        b_choose_btn.setStyleSheet("QPushButton { background-color: #2d5a2d; } QPushButton:hover { background-color: #3d6a3d; }")
        b_choose_btn.clicked.connect(lambda: self._make_choice(False))
        b_layout.addWidget(b_choose_btn)

        options_layout.addWidget(b_frame)
        main_layout.addLayout(options_layout)

        # Stop button
        stop_btn = QPushButton("⏹ Stop Audio")
        stop_btn.setStyleSheet("QPushButton { background-color: #5a2d2d; } QPushButton:hover { background-color: #6a3d3d; }")
        stop_btn.clicked.connect(self._stop_audio)
        main_layout.addWidget(stop_btn)

    def _center_window(self):
        """Center the window on screen."""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def _play_audio(self, audio_path: Path):
        """Play an audio file using pygame.

        Args:
            audio_path: Path to audio file to play
        """
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(audio_path))
            pygame.mixer.music.play()
            print(f"Playing: {audio_path.name}")
        except pygame.error as e:
            print(f"Error playing audio {audio_path.name}: {e}")
            QMessageBox.warning(self, "Audio Error", f"Could not play {audio_path.name}: {e}")

    def _stop_audio(self):
        """Stop any currently playing audio."""
        try:
            pygame.mixer.music.stop()
            print("Audio stopped")
        except pygame.error as e:
            print(f"Error stopping audio: {e}")

    def _make_choice(self, chose_a: bool):
        """Handle user's choice.

        Args:
            chose_a: True if user chose option A, False for option B
        """
        self._stop_audio()
        self.choice_made.emit(chose_a)
        self.close()

    def closeEvent(self, event):
        """Handle window close event."""
        self._stop_audio()
        # Always emit a choice when closing (default to A if no choice made)
        self.choice_made.emit(True)
        event.accept()
