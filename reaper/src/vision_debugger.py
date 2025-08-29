"""Vision-based debugging system for REAPER automation."""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

try:
    import pyautogui
    import PIL.Image
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False
    print("Warning: Vision debugging requires 'pip install pyautogui pillow'")


@dataclass
class ScreenshotMetadata:
    """Metadata for captured screenshots."""
    timestamp: str
    session_id: str
    window_title: Optional[str] = None
    window_bounds: Optional[Tuple[int, int, int, int]] = None
    automation_status: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None


class VisionDebugger:
    """Vision-based debugging system for REAPER automation."""

    def __init__(self, debug_dir: Optional[Path] = None):
        """Initialize vision debugger.

        Args:
            debug_dir: Directory to save debug screenshots and data
        """
        if not VISION_AVAILABLE:
            raise ImportError("Vision debugging requires pyautogui and pillow packages")

        self.debug_dir = debug_dir or Path.home() / "Desktop" / "reaper_debug"
        self.debug_dir.mkdir(exist_ok=True)

        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

        # Screenshot history
        self.screenshots: List[ScreenshotMetadata] = []

    def capture_screenshot(self,
                         session_id: str = "debug",
                         description: str = "Debug screenshot",
                         region: Optional[Tuple[int, int, int, int]] = None) -> ScreenshotMetadata:
        """Capture a screenshot with metadata.

        Args:
            session_id: Session identifier
            description: Description of what's being captured
            region: Optional region (x, y, width, height) to capture

        Returns:
            Screenshot metadata
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{session_id}_{timestamp}.png"
        file_path = self.debug_dir / filename

        try:
            # Capture screenshot
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            # Save screenshot
            screenshot.save(file_path)

            # Get active window info
            window_info = self._get_active_window_info()

            # Create metadata
            metadata = ScreenshotMetadata(
                timestamp=timestamp,
                session_id=session_id,
                description=description,
                file_path=str(file_path),
                window_title=window_info.get('title'),
                window_bounds=window_info.get('bounds')
            )

            self.screenshots.append(metadata)

            print(f"Screenshot captured: {file_path}")
            return metadata

        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            raise

    def capture_reaper_window(self, session_id: str = "reaper") -> Optional[ScreenshotMetadata]:
        """Capture screenshot of REAPER window specifically.

        Args:
            session_id: Session identifier

        Returns:
            Screenshot metadata if REAPER window found, None otherwise
        """
        reaper_bounds = self._find_reaper_window()
        if not reaper_bounds:
            print("REAPER window not found")
            return None

        return self.capture_screenshot(
            session_id=session_id,
            description="REAPER window capture",
            region=reaper_bounds
        )

    def capture_automation_sequence(self,
                                  session_id: str,
                                  steps: List[str],
                                  delay_between_steps: float = 2.0) -> List[ScreenshotMetadata]:
        """Capture screenshots during automation sequence.

        Args:
            session_id: Session identifier
            steps: List of step descriptions
            delay_between_steps: Delay between captures

        Returns:
            List of screenshot metadata
        """
        captures = []

        for i, step_description in enumerate(steps):
            if i > 0:
                time.sleep(delay_between_steps)

            metadata = self.capture_screenshot(
                session_id=f"{session_id}_step{i+1}",
                description=f"Step {i+1}: {step_description}"
            )
            captures.append(metadata)

        return captures

    def monitor_beacon_and_capture(self,
                                 beacon_file: Path,
                                 session_id: str,
                                 capture_interval: float = 5.0,
                                 timeout: float = 120.0) -> List[ScreenshotMetadata]:
        """Monitor beacon file and capture screenshots on status changes.

        Args:
            beacon_file: Path to beacon file to monitor
            session_id: Session identifier
            capture_interval: How often to check beacon (seconds)
            timeout: Maximum time to monitor (seconds)

        Returns:
            List of screenshot metadata
        """
        captures = []
        start_time = time.time()
        last_status = None

        print(f"Monitoring beacon file: {beacon_file}")

        while time.time() - start_time < timeout:
            # Check beacon file
            beacon_data = self._read_beacon_file(beacon_file)
            current_status = beacon_data.get('status', 'UNKNOWN') if beacon_data else 'NO_BEACON'

            # Capture on status change or first iteration
            if current_status != last_status:
                description = f"Status: {current_status}"
                if beacon_data:
                    script = beacon_data.get('script', 'unknown')
                    message = beacon_data.get('message', '')
                    description += f" - {script}"
                    if message:
                        description += f" ({message})"

                metadata = self.capture_screenshot(
                    session_id=f"{session_id}_beacon",
                    description=description
                )
                metadata.automation_status = current_status
                captures.append(metadata)

                print(f"Status change detected: {current_status}")
                last_status = current_status

                # Stop if completed or error
                if current_status in ['COMPLETED', 'ERROR']:
                    break

            time.sleep(capture_interval)

        return captures

    def analyze_reaper_state(self) -> Dict[str, any]:
        """Analyze current REAPER state from screenshot.

        Returns:
            Dictionary with analysis results
        """
        # Capture current state
        metadata = self.capture_reaper_window("analysis")
        if not metadata or not metadata.file_path:
            return {"error": "Could not capture REAPER window"}

        # Basic analysis (can be extended with computer vision)
        analysis = {
            "timestamp": metadata.timestamp,
            "window_detected": metadata.window_title is not None,
            "window_title": metadata.window_title,
            "screenshot_path": metadata.file_path
        }

        # Check if REAPER window is responsive
        if metadata.window_title and "REAPER" in metadata.window_title:
            analysis["reaper_responsive"] = True
        else:
            analysis["reaper_responsive"] = False

        return analysis

    def create_debug_report(self, session_id: str) -> Path:
        """Create a debug report with all screenshots and metadata.

        Args:
            session_id: Session to create report for

        Returns:
            Path to generated report
        """
        # Filter screenshots for this session
        session_screenshots = [s for s in self.screenshots if s.session_id.startswith(session_id)]

        # Create report data
        report_data = {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "total_screenshots": len(session_screenshots),
            "screenshots": []
        }

        for screenshot in session_screenshots:
            screenshot_data = {
                "timestamp": screenshot.timestamp,
                "description": screenshot.description,
                "file_path": screenshot.file_path,
                "window_title": screenshot.window_title,
                "automation_status": screenshot.automation_status
            }
            report_data["screenshots"].append(screenshot_data)

        # Save report
        report_file = self.debug_dir / f"{session_id}_debug_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"Debug report created: {report_file}")
        return report_file

    def cleanup_old_screenshots(self, days_old: int = 7):
        """Clean up screenshots older than specified days.

        Args:
            days_old: Remove screenshots older than this many days
        """
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        removed_count = 0

        for file_path in self.debug_dir.glob("*.png"):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                removed_count += 1

        # Also clean up metadata
        self.screenshots = [
            s for s in self.screenshots
            if s.file_path and Path(s.file_path).exists()
        ]

        print(f"Cleaned up {removed_count} old screenshots")

    def _get_active_window_info(self) -> Dict[str, any]:
        """Get information about the active window."""
        try:
            # Try to get window info using AppleScript on macOS
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontWindow to name of front window of first application process whose frontmost is true
                return frontApp & "|" & frontWindow
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                app_name, window_name = result.stdout.strip().split('|', 1)
                return {
                    'title': f"{app_name} - {window_name}",
                    'app': app_name,
                    'window': window_name
                }
        except Exception as e:
            print(f"Could not get window info: {e}")

        return {}

    def _find_reaper_window(self) -> Optional[Tuple[int, int, int, int]]:
        """Find REAPER window bounds.

        Returns:
            Window bounds as (x, y, width, height) or None if not found
        """
        try:
            # Try to find REAPER window using AppleScript
            script = '''
            tell application "System Events"
                set reaperProcess to first application process whose name contains "REAPER"
                set reaperWindow to front window of reaperProcess
                set windowPosition to position of reaperWindow
                set windowSize to size of reaperWindow
                return (item 1 of windowPosition) & "," & (item 2 of windowPosition) & "," & (item 1 of windowSize) & "," & (item 2 of windowSize)
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                x, y, width, height = map(int, result.stdout.strip().split(','))
                return (x, y, width, height)

        except Exception as e:
            print(f"Could not find REAPER window: {e}")

        return None

    def _read_beacon_file(self, beacon_file: Path) -> Optional[Dict[str, str]]:
        """Read and parse beacon file contents."""
        try:
            if not beacon_file.exists():
                return None

            with open(beacon_file, 'r') as f:
                content = f.read().strip()

            # Parse key=value lines
            beacon_data = {}
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    beacon_data[key] = value

            return beacon_data

        except Exception as e:
            print(f"Error reading beacon file: {e}")
            return None


def main():
    """CLI interface for vision debugging."""
    import sys

    if not VISION_AVAILABLE:
        print("Error: Vision debugging requires 'pip install pyautogui pillow'")
        return 1

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python vision_debugger.py screenshot [description]")
        print("  python vision_debugger.py reaper")
        print("  python vision_debugger.py analyze")
        print("  python vision_debugger.py monitor <beacon_file> [session_id]")
        return 1

    command = sys.argv[1]
    debugger = VisionDebugger()

    if command == "screenshot":
        description = sys.argv[2] if len(sys.argv) > 2 else "Manual screenshot"
        metadata = debugger.capture_screenshot(description=description)
        print(f"Screenshot saved: {metadata.file_path}")

    elif command == "reaper":
        metadata = debugger.capture_reaper_window()
        if metadata:
            print(f"REAPER screenshot saved: {metadata.file_path}")
        else:
            print("Could not capture REAPER window")

    elif command == "analyze":
        analysis = debugger.analyze_reaper_state()
        print("REAPER State Analysis:")
        for key, value in analysis.items():
            print(f"  {key}: {value}")

    elif command == "monitor":
        if len(sys.argv) < 3:
            print("Usage: python vision_debugger.py monitor <beacon_file> [session_id]")
            return 1

        beacon_file = Path(sys.argv[2])
        session_id = sys.argv[3] if len(sys.argv) > 3 else "monitor"

        print(f"Monitoring beacon file: {beacon_file}")
        captures = debugger.monitor_beacon_and_capture(beacon_file, session_id)
        print(f"Captured {len(captures)} screenshots during monitoring")

        # Create debug report
        debugger.create_debug_report(session_id)

    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

