#!/usr/bin/env python3
"""
Install vision debugging dependencies.
This script will install pyautogui and pillow for vision debugging functionality.
"""

import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required dependencies for vision debugging."""
    dependencies = [
        "pyautogui>=0.9.54",
        "pillow>=9.0.0"
    ]

    print("Installing vision debugging dependencies...")
    print("Dependencies:", dependencies)

    try:
        # Use uv to add dependencies
        for dep in dependencies:
            print(f"Installing {dep}...")
            result = subprocess.run(
                ["uv", "add", dep],
                check=True,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            print(f"✓ {dep} installed successfully")

        print("\n✓ All vision debugging dependencies installed!")
        print("\nYou can now use vision debugging features:")
        print("  uv run main_v2.py octave-sweep --vision-debug")
        print("  uv run main_v2.py vision-debug screenshot")
        print("  uv run main_v2.py vision-debug reaper")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print("Error output:", e.stderr)
        return False
    except FileNotFoundError:
        print("Error: 'uv' command not found. Please install uv first.")
        return False

if __name__ == "__main__":
    success = install_dependencies()
    sys.exit(0 if success else 1)

