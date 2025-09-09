"""
main.py prepares the session config and starts Reaper,
which executes its __startup.lua, which calls main.lua,
which calls the ReaScripts for the session, which control Reaper to produce audio.
main.py collects the session artifacts and checks them.
"""

import subprocess
import os
import time
import shutil
import threading
import signal
from pathlib import Path
from typing import List, Dict, Optional
import json


def main():
    """
    main.py prepares the session config and starts Reaper,
    which executes its __startup.lua, which calls main.lua,
    which calls the ReaScripts for the session, which control Reaper to produce audio.
    main.py collects the session artifacts and checks them.
    """
    prepare_session_config()
    start_reaper()
    artifacts = collect_session_artifacts()
    check_session_artifacts(artifacts)


def prepare_session_config():
    """
    Prepares the session config file used by main.lua.
    Since the GA system already generates the session configs,
    this just needs to detect which session to run.
    """
    # Detect the latest session config file
    session_file = detect_latest_session()

    # Write the session filename to current_session.txt for Lua script
    with open("current_session.txt", "w") as f:
        f.write(session_file)

    print(f"Prepared session config: {session_file}")


def detect_latest_session() -> str:
    """
    Detect the most recent session config file to process.
    """
    session_configs_dir = Path("session-configs")

    if not session_configs_dir.exists():
        raise FileNotFoundError("session-configs directory not found")

    # Find all JSON files
    json_files = list(session_configs_dir.glob("*.json"))

    if not json_files:
        raise FileNotFoundError("No session config files found")

    # Sort by modification time, get the most recent
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

    print(f"Detected latest session: {latest_file.name}")
    return latest_file.name


def ensure_reaper_closed():
    """
    Ensure REAPER is not running before starting new session.
    """
    import psutil

    reaper_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'REAPER' in proc.info['name'] or 'reaper' in proc.info['name'].lower():
                reaper_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if reaper_processes:
        print(f"Found {len(reaper_processes)} REAPER process(es) running")
        for proc in reaper_processes:
            try:
                print(f"Terminating REAPER process {proc.pid}")
                proc.terminate()
                proc.wait(timeout=10)  # Wait up to 10 seconds for graceful shutdown
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                try:
                    proc.kill()  # Force kill if graceful shutdown fails
                except psutil.NoSuchProcess:
                    pass
        print("REAPER processes closed")
    else:
        print("No REAPER processes found running")


def start_reaper():
    """
    Starts REAPER and executes the session.
    """
    print("Starting REAPER...")

    # Ensure REAPER is closed before starting
    ensure_reaper_closed()

    # Execute REAPER with the main.lua script
    result = execute_reaper_with_session()

    if result.returncode != 0:
        raise RuntimeError(f"REAPER execution failed with code {result.returncode}: {result.stderr}")

    print("REAPER execution completed successfully")


def execute_reaper_with_session(session_file: str = None) -> subprocess.CompletedProcess:
    """
    Execute REAPER with the specified session using log monitoring and process management.
    """
    # Write the session filename to current_session.txt for Lua script
    if session_file:
        with open("current_session.txt", "w") as f:
            f.write(session_file)
        print(f"Set session file: {session_file}")
    else:
        # Fallback to detecting latest session
        session_file = detect_latest_session()
        with open("current_session.txt", "w") as f:
            f.write(session_file)
        print(f"Auto-detected session file: {session_file}")
    
    # Determine REAPER executable path based on platform
    import platform
    system = platform.system()

    if system == "Darwin":  # macOS
        reaper_exe = "/Applications/REAPER.app/Contents/MacOS/REAPER"
    elif system == "Windows":
        reaper_exe = "C:\\Program Files\\REAPER\\reaper.exe"
    elif system == "Linux":
        reaper_exe = "/opt/REAPER/reaper"  # Common Linux path
    else:
        # Fallback - try to find REAPER in PATH
        reaper_exe = "reaper"

    # Build command: REAPER -nosplash -new script.lua
    cmd = [
        reaper_exe,
        "-nosplash",  # Don't show splash screen
        "-new",       # Start with new project
        "reascripts/main.lua"  # Execute our main script
    ]

    print(f"Executing REAPER: {' '.join(cmd)}")

    try:
        # Start REAPER process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Monitor logs and kill process when complete
        result = monitor_reaper_execution(process, timeout=120)
        return result

    except FileNotFoundError:
        print(f"ERROR: REAPER executable not found at {reaper_exe}")
        print("Please ensure REAPER is installed or adjust the path in the script")
        return subprocess.CompletedProcess(cmd, 1, "", f"REAPER not found at {reaper_exe}")


def monitor_reaper_execution(process: subprocess.Popen, timeout: int = 120) -> subprocess.CompletedProcess:
    """
    Monitor REAPER execution by watching log files for completion signals.
    Kill REAPER when session is complete or timeout is reached.
    """
    print("Monitoring REAPER execution...")

    start_time = time.time()
    session_complete = False
    log_file_path = None
    initial_log_count = 0

    # Look for log file in session-results directory
    session_results_dir = Path("session-results")

    # Count existing log files to detect new ones
    if session_results_dir.exists():
        initial_log_count = len(list(session_results_dir.glob("*.log")))

    # Monitor for session completion
    while time.time() - start_time < timeout:
        # Check if process has terminated naturally
        if process.poll() is not None:
            print("REAPER process terminated naturally")
            break

        # Look for NEW log files created after we started
        if log_file_path is None and session_results_dir.exists():
            log_files = list(session_results_dir.glob("*.log"))
            if len(log_files) > initial_log_count:
                # Get the most recent log file (should be the new one)
                log_file_path = max(log_files, key=lambda f: f.stat().st_mtime)
                print(f"Found new log file: {log_file_path}")

        # Check log file for completion signal
        if log_file_path and log_file_path.exists():
            try:
                with open(log_file_path, 'r') as f:
                    content = f.read()
                    if "SESSION_COMPLETE" in content:
                        print("Session completion detected in logs")
                        session_complete = True
                        break
            except Exception as e:
                print(f"Error reading log file: {e}")

        # Check for individual render timeouts (10s max per render)
        if log_file_path and log_file_path.exists():
            if check_render_timeout(log_file_path, max_render_time=15):  # Increased to 15s
                print("Render timeout detected - killing REAPER")
                break

        time.sleep(1.0)  # Check every 1 second (less frequent)

    # Kill REAPER process
    print("Terminating REAPER process...")
    try:
        # Try graceful termination first
        process.terminate()
        try:
            process.wait(timeout=5)
            print("REAPER terminated gracefully")
        except subprocess.TimeoutExpired:
            # Force kill if needed
            process.kill()
            process.wait()
            print("REAPER force killed")
    except Exception as e:
        print(f"Error terminating REAPER: {e}")

    # Get final output
    try:
        stdout, stderr = process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        stdout, stderr = "", ""

    elapsed_time = time.time() - start_time
    print(f"REAPER execution completed in {elapsed_time:.1f}s")

    if session_complete:
        print("Session completed successfully")
        return subprocess.CompletedProcess([], 0, stdout, stderr)
    else:
        print("Session terminated by timeout or error")
        return subprocess.CompletedProcess([], 1, stdout, stderr)


def check_render_timeout(log_file_path: Path, max_render_time: int = 10) -> bool:
    """
    Check if any individual render is taking too long.
    """
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()

        render_start_times = {}
        current_time = time.time()

        for line in lines:
            if "RENDER_START:" in line:
                # Extract render ID and timestamp
                parts = line.split("RENDER_START:")
                if len(parts) > 1:
                    render_id = parts[1].strip()
                    # Extract timestamp from log line
                    if "] [" in line:
                        timestamp_str = line.split("] [")[0].split("[")[1]
                        try:
                            import datetime
                            timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            render_start_times[render_id] = timestamp.timestamp()
                        except:
                            pass

            elif "RENDER_COMPLETE:" in line:
                # Remove completed renders from tracking
                parts = line.split("RENDER_COMPLETE:")
                if len(parts) > 1:
                    render_id = parts[1].split(":")[0].strip()
                    if render_id in render_start_times:
                        del render_start_times[render_id]

        # Check for timeouts
        for render_id, start_time in render_start_times.items():
            if current_time - start_time > max_render_time:
                print(f"Render timeout: {render_id} has been running for {current_time - start_time:.1f}s")
                return True

        return False

    except Exception as e:
        print(f"Error checking render timeouts: {e}")
        return False


def collect_session_artifacts() -> List[Path]:
    """
    Collects the session artifacts (rendered audio files).
    """
    renders_dir = Path("renders")

    if not renders_dir.exists():
        print("No renders directory found")
        return []

    # Find all audio files in render directories
    audio_files = []

    for render_dir in renders_dir.iterdir():
        if render_dir.is_dir():
            # Look for audio files in this render directory
            for audio_file in render_dir.glob("*.wav"):
                audio_files.append(audio_file)
                print(f"Found audio artifact: {audio_file}")

    print(f"Collected {len(audio_files)} audio artifacts")
    return audio_files


def check_session_artifacts(artifacts: List[Path]) -> bool:
    """
    Checks the session artifacts to ensure they are valid.
    """
    if not artifacts:
        print("Warning: No artifacts found to check")
        return False

    valid_artifacts = 0

    for artifact in artifacts:
        if artifact.exists() and artifact.stat().st_size > 0:
            valid_artifacts += 1
            print(f"Valid artifact: {artifact}")
        else:
            print(f"Invalid artifact: {artifact}")

    success = valid_artifacts == len(artifacts)
    print(f"Artifact validation: {valid_artifacts}/{len(artifacts)} valid")

    return success


def process_session_config(session_filename: str) -> Dict:
    """
    Process a specific session configuration file.
    """
    session_path = Path("session-configs") / session_filename

    if not session_path.exists():
        raise FileNotFoundError(f"Session config not found: {session_path}")

    with open(session_path, 'r') as f:
        session_data = json.load(f)

    print(f"Processed session config: {session_filename}")
    print(f"Session name: {session_data.get('session_name', 'Unknown')}")
    print(f"Render configs: {len(session_data.get('render_configs', []))}")

    return session_data


if __name__ == "__main__":
    main()
