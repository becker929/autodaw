#!/usr/bin/env python3
"""
Simple REAPER Launcher Script
Launches REAPER with a new project and executes a ReaScript

Usage:
    python launch_reaper_with_script.py [script_path] [--background]
"""

import subprocess
import sys
import os
import argparse
import signal
import psutil

def find_reaper_executable():
    """Find REAPER executable on the system"""
    reaper_paths = [
        "/Applications/REAPER.app/Contents/MacOS/REAPER",
        "/Applications/REAPER64.app/Contents/MacOS/REAPER",
        "/usr/local/bin/reaper",
        "/opt/REAPER/reaper"
    ]

    for path in reaper_paths:
        if os.path.exists(path):
            return path

    # Try to find via which command
    try:
        result = subprocess.run(['which', 'reaper'],
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        pass

    return None

def terminate_reaper_instances():
    """Terminate any existing REAPER instances"""
    print("Checking for existing REAPER instances...")
    terminated_count = 0

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'REAPER' in proc.info['name']:
                print(f"Terminating REAPER process (PID: {proc.info['pid']})")
                proc.terminate()
                terminated_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if terminated_count > 0:
        print(f"Terminated {terminated_count} REAPER instance(s)")
        import time
        time.sleep(2)  # Give time for processes to terminate
    else:
        print("No existing REAPER instances found")

def test_reapy_connection():
    """Test if reapy can connect to REAPER"""
    try:
        # Create a minimal test script to check reapy connection
        test_script = '''
import reapy_boost as reapy
try:
    with reapy.inside_reaper():
        project = reapy.Project()
        print("SUCCESS: reapy connected to REAPER")
        exit(0)
except Exception as e:
    print(f"FAILED: {e}")
    exit(1)
'''

        # Write test script to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script_path = f.name

        # Try to run the test script
        result = subprocess.run(
            ["uv", "run", "python", temp_script_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Clean up temp file
        os.unlink(temp_script_path)

        return result.returncode == 0

    except Exception:
        return False

def launch_reaper_with_reapy(script_path):
    """Launch REAPER and then run reapy script externally with retry logic"""
    # First terminate any existing REAPER instances
    terminate_reaper_instances()

    reaper_exe = find_reaper_executable()
    if not reaper_exe:
        print("Error: REAPER executable not found!")
        return False

    print(f"Found REAPER at: {reaper_exe}")
    print("Starting REAPER with new project...")

    # Start REAPER with new project
    cmd = [reaper_exe, "-new"]

    try:
        # Start REAPER in background
        process = subprocess.Popen(cmd)
        print(f"REAPER started with PID: {process.pid}")

        # Wait for REAPER's distant API to become available with retry logic
        import time
        max_retries = 20  # Try for up to 60 seconds (20 * 3 seconds)
        retry_count = 0

        print("Waiting for REAPER's distant API to become available...")

        while retry_count < max_retries:
            print(f"Attempt {retry_count + 1}/{max_retries}: Testing reapy connection...")

            if test_reapy_connection():
                print("✓ REAPER's distant API is ready!")
                break
            else:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"✗ Connection failed, waiting 3 seconds before retry...")
                    time.sleep(3)

        if retry_count >= max_retries:
            print("✗ Failed to connect to REAPER's distant API after maximum retries")
            print("Make sure REAPER has fully loaded and reapy distant API is enabled")
            return False

        # Now run the reapy script
        print(f"Executing reapy script: {script_path}")
        script_abs_path = os.path.abspath(script_path)

        # Run the script using uv
        result = subprocess.run(["uv", "run", "python", script_abs_path], check=True)
        print("reapy script executed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        return False
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return False

def launch_reaper(script_path, background=False, use_reapy=False):
    """Launch REAPER with the specified script"""
    if use_reapy:
        return launch_reaper_with_reapy(script_path)

    reaper_exe = find_reaper_executable()
    if not reaper_exe:
        print("Error: REAPER executable not found!")
        return False

    print(f"Found REAPER at: {reaper_exe}")
    print(f"Executing script: {script_path}")

    script_abs_path = os.path.abspath(script_path)

    # Try different approaches to execute the script
    # First, try with -script parameter
    cmd = [
        reaper_exe,
        "-new",  # Create new project
        "-script", script_abs_path  # Execute script
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        if background:
            # Run in background and return immediately
            process = subprocess.Popen(cmd)
            print(f"REAPER started in background with PID: {process.pid}")
            return True
        else:
            # Run in foreground
            result = subprocess.run(cmd, check=True)
            print("REAPER executed successfully")
            return True

    except subprocess.CalledProcessError as e:
        print(f"Error running REAPER: {e}")
        return False
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Launch REAPER with a ReaScript on a new project"
    )
    parser.add_argument(
        "script_path",
        nargs="?",
        default="reapy_script.py",
        help="Path to the script to execute (default: reapy_script.py)"
    )
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run REAPER in background"
    )
    parser.add_argument(
        "--reapy",
        action="store_true",
        help="Use reapy-boost to execute script externally (recommended)"
    )

    args = parser.parse_args()

    # Check if script exists
    if not os.path.exists(args.script_path):
        print(f"Error: Script file not found: {args.script_path}")
        return 1

    success = launch_reaper(args.script_path, args.background, args.reapy)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
