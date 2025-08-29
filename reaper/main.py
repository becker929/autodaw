#!/usr/bin/env python3
"""
REAPER Automation System - Main Entry Point
Manages REAPER application lifecycle and automation workflow
"""

import subprocess
import time
import os
import signal
import sys
from pathlib import Path

class ReaperAutomationSystem:
    def __init__(self):
        self.reaper_process = None
        self.reaper_path = "/Applications/REAPER.app/Contents/MacOS/REAPER"
        self.project_dir = Path(__file__).parent
        self.startup_script = "/Users/anthonybecker/Library/Application Support/REAPER/Scripts/__startup.lua"
        self.beacon_file = "/Users/anthonybecker/Desktop/reaper_automation_beacon.txt"

    def check_reaper_installed(self):
        """Check if REAPER is installed at expected location"""
        if not os.path.exists(self.reaper_path):
            print(f"ERROR: REAPER not found at {self.reaper_path}")
            print("Please install REAPER or update the path in main.py")
            return False
        return True

    def check_startup_script(self):
        """Verify startup script exists and points to our main.lua"""
        if not os.path.exists(self.startup_script):
            print(f"ERROR: Startup script not found at {self.startup_script}")
            return False

        # Check if it calls our main.lua
        with open(self.startup_script, 'r') as f:
            content = f.read()
            if "main.lua" not in content:
                print("WARNING: Startup script may not be configured to call main.lua")
                print(f"Current startup script content:\n{content}")
        return True

    def start_reaper(self, project_file=None):
        """Start REAPER with optional project file"""
        print("Starting REAPER...")

        cmd = [self.reaper_path]
        if project_file:
            cmd.append(str(project_file))

        # Clear any existing beacon file
        self.clear_beacon_file()
        try:
            # Start REAPER in background [[memory:7053637]]
            self.reaper_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            # Give REAPER a moment to start
            print("Waiting for REAPER to start...")
            time.sleep(3)  # Brief delay for REAPER to initialize
            return True
        except Exception as e:
            print(f"ERROR starting REAPER: {e}")
            return False

    def stop_reaper(self):
        """Stop REAPER process and ensure all instances are closed"""
        success = True

        if self.reaper_process:
            print("Stopping REAPER process...")
            try:
                # Send SIGTERM to process group [[memory:7053637]]
                os.killpg(os.getpgid(self.reaper_process.pid), signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    self.reaper_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print("REAPER didn't stop gracefully, forcing...")
                    os.killpg(os.getpgid(self.reaper_process.pid), signal.SIGKILL)

                self.reaper_process = None
                print("REAPER process stopped")

            except Exception as e:
                print(f"ERROR stopping REAPER process: {e}")
                success = False

        # Additional cleanup: kill any remaining REAPER processes
        try:
            print("Checking for remaining REAPER instances...")
            result = subprocess.run(['pkill', '-f', 'REAPER'], capture_output=True, text=True)
            if result.returncode == 0:
                print("Killed remaining REAPER instances")
            time.sleep(2)  # Give time for processes to terminate
        except Exception as e:
            print(f"Warning: Could not kill remaining REAPER instances: {e}")

        return success

    def clear_beacon_file(self):
        """Remove beacon file if it exists"""
        try:
            if os.path.exists(self.beacon_file):
                os.remove(self.beacon_file)
                print("Cleared existing beacon file")
        except Exception as e:
            print(f"Warning: Could not clear beacon file: {e}")

    def read_beacon_file(self):
        """Read and parse beacon file contents"""
        try:
            if not os.path.exists(self.beacon_file):
                return None

            with open(self.beacon_file, 'r') as f:
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

    def wait_for_automation_completion(self, timeout_seconds=60):
        """Monitor beacon file until automation completes or times out"""
        print("Monitoring automation progress via beacon file...")

        start_time = time.time()
        last_status = None

        while time.time() - start_time < timeout_seconds:
            beacon_data = self.read_beacon_file()

            if beacon_data:
                status = beacon_data.get('status', 'UNKNOWN')
                script = beacon_data.get('script', 'unknown')
                message = beacon_data.get('message', '')

                # Print status updates
                if status != last_status:
                    print(f"Status: {status} - {script}")
                    if message:
                        print(f"  Message: {message}")
                    last_status = status

                # Check for completion or error
                if status == 'COMPLETED':
                    print("✓ Automation completed successfully!")
                    return True
                elif status == 'ERROR':
                    print(f"✗ Automation failed: {message}")
                    return False

            # Wait before checking again
            time.sleep(1)

        print(f"⚠ Timeout after {timeout_seconds} seconds - automation may still be running")
        return False

    def run_automation_cycle(self, script_name, project_file=None):
        """Run a complete automation cycle: start REAPER -> run script -> stop REAPER"""
        print(f"\n{'='*60}")
        print(f"Running automation cycle with script: {script_name}")
        print(f"Project file: {project_file or 'default'}")
        print(f"{'='*60}")

        # Update main.lua to use the specified script
        self.update_main_lua_script(script_name)

        # Start REAPER
        if not self.start_reaper(project_file):
            return False

        # Wait for automation to complete by monitoring beacon file
        automation_success = self.wait_for_automation_completion()

        # Stop REAPER
        stop_success = self.stop_reaper()

        # Clean up beacon file
        self.clear_beacon_file()

        overall_success = automation_success and stop_success
        print(f"Automation cycle completed: {'SUCCESS' if overall_success else 'FAILED'}")
        return overall_success

    def update_main_lua_script(self, script_name):
        """Update main.lua to run the specified script"""
        main_lua_path = self.project_dir / "reascripts" / "main.lua"

        if not main_lua_path.exists():
            print(f"ERROR: main.lua not found at {main_lua_path}")
            return False

        # Read current content
        with open(main_lua_path, 'r') as f:
            content = f.read()

        # Replace the current_script line
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'current_script =' in line and 'config' in line:
                lines[i] = f'    current_script = "{script_name}",  -- updated by automation system'
                break

        # Write back
        with open(main_lua_path, 'w') as f:
            f.write('\n'.join(lines))

        print(f"Updated main.lua to use script: {script_name}")
        return True

    def update_config_file(self, session_id, octave_value):
        """Update the automation config file with organized output directory"""
        config_path = self.project_dir / "automation_config.txt"

        # Create session directory
        session_dir = Path("/Users/anthonybecker/Desktop/evolver_sessions") / f"session_{session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)

        config_content = f"""workflow_mode=full
target_parameter=octave
parameter_value={octave_value}
session_id={session_id}
output_dir={session_dir}"""

        with open(config_path, 'w') as f:
            f.write(config_content)

        print(f"Updated config: Session {session_id}, Octave = {octave_value}")
        print(f"Output directory: {session_dir}")

    def run_octave_sweep_workflow(self):
        """Run complete workflow sweeping through octave values"""
        print("Starting REAPER Octave Sweep Automation")
        print("======================================")

        # Check prerequisites
        if not self.check_reaper_installed():
            return False
        if not self.check_startup_script():
            return False

        # Define octave values to sweep through
        octave_values = [-2.0, -1.0, 0.0, 1.0, 2.0]  # Sweep from -2 to +2 octaves
        project_file = self.project_dir / "data/serum/serum1.RPP"

        results = []
        for i, octave_value in enumerate(octave_values, 1):
            print(f"\n{'='*60}")
            print(f"SESSION {i}/5: Octave = {octave_value}")
            print(f"{'='*60}")

            # Update config file for this session
            self.update_config_file(i, octave_value)

            # Run full workflow in single REAPER session
            success = self.run_single_session_workflow(project_file, i, octave_value)
            results.append((f"Session {i} (Octave {octave_value})", success))

            # Brief pause between sessions
            time.sleep(3)

        # Report results
        print(f"\n{'='*60}")
        print("OCTAVE SWEEP COMPLETE - RESULTS:")
        print(f"{'='*60}")
        for session_name, success in results:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{session_name:<25} {status}")

        all_success = all(success for _, success in results)
        print(f"\nOverall result: {'ALL SUCCESSFUL' if all_success else 'SOME FAILED'}")
        return all_success

    def run_single_session_workflow(self, project_file, session_id, octave_value):
        """Run complete workflow (get params → change octave → add MIDI → render) in single session"""
        print(f"Running complete workflow in single REAPER session...")

        # Start REAPER
        if not self.start_reaper(project_file):
            return False

        # Wait for complete workflow to finish
        automation_success = self.wait_for_automation_completion(timeout_seconds=120)  # Longer timeout for full workflow

        # Stop REAPER
        stop_success = self.stop_reaper()

        # Clean up beacon file
        self.clear_beacon_file()

        overall_success = automation_success and stop_success
        print(f"Session {session_id} completed: {'SUCCESS' if overall_success else 'FAILED'}")
        return overall_success

def main():
    """Main entry point"""
    automation = ReaperAutomationSystem()

    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "octave-sweep":
            automation.run_octave_sweep_workflow()
        elif command == "single" and len(sys.argv) > 2:
            script_name = sys.argv[2]
            project_file = sys.argv[3] if len(sys.argv) > 3 else None
            automation.run_automation_cycle(script_name, project_file)
        else:
            print("Usage:")
            print("  uv run main.py octave-sweep               # Run octave sweep workflow (RECOMMENDED)")
            print("  uv run main.py single <script> [project] # Run single automation cycle")
            print("\nNew workflow design:")
            print("  - Each session runs: get_params → change_octave → add_midi → render")
            print("  - Sweeps through octave values: -2, -1, 0, +1, +2")
            print("  - Creates separate audio files for each octave setting")
    else:
        # Default: run octave sweep
        automation.run_octave_sweep_workflow()

if __name__ == "__main__":
    main()
