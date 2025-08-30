"""REAPER process management."""

import subprocess
import signal
import time
import os
import logging
from pathlib import Path
from typing import Optional
from config import SystemConfig, get_logger

# Set up module logger
logger = get_logger(__name__)


class ReaperProcessManager:
    """Manages REAPER process lifecycle."""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        logger.info(f"ReaperProcessManager initialized with REAPER path: {config.reaper_path}")
        logger.debug(f"REAPER path exists: {config.reaper_path.exists()}")

    def start_reaper(self, project_file: Optional[Path] = None) -> bool:
        """Start REAPER with optional project file."""
        logger.debug(f"Attempting to start REAPER with project: {project_file}")

        if self.process and self.process.poll() is None:
            logger.warning("REAPER is already running")
            print("REAPER is already running")
            return True

        logger.info("Starting REAPER process")
        print("Starting REAPER...")

        cmd = [str(self.config.reaper_path)]
        if project_file:
            cmd.append(str(project_file))
            logger.debug(f"Command with project file: {cmd}")
        else:
            logger.debug(f"Command without project file: {cmd}")

        try:
            logger.debug(f"Executing subprocess.Popen with command: {cmd}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            logger.debug(f"REAPER process started with PID: {self.process.pid}")

            # Give REAPER a moment to start
            logger.debug("Waiting 3 seconds for REAPER to initialize")
            print("Waiting for REAPER to start...")
            time.sleep(3)

            # Check if process is still running
            poll_result = self.process.poll()
            logger.debug(f"Process poll result after startup: {poll_result}")

            if poll_result is not None:
                logger.error(f"REAPER process exited immediately with code: {poll_result}")
                print("REAPER process exited immediately")
                return False

            logger.info(f"REAPER started successfully with PID: {self.process.pid}")
            print("REAPER started successfully")
            return True

        except Exception as e:
            logger.exception(f"Exception starting REAPER: {e}")
            print(f"ERROR starting REAPER: {e}")
            return False

    def stop_reaper(self) -> bool:
        """Stop REAPER process and ensure all instances are closed."""
        logger.info("Stopping REAPER process")
        success = True

        if self.process:
            logger.debug(f"Stopping REAPER process with PID: {self.process.pid}")
            print("Stopping REAPER process...")
            try:
                # Send SIGTERM to process group
                process_group = os.getpgid(self.process.pid)
                logger.debug(f"Sending SIGTERM to process group: {process_group}")
                os.killpg(process_group, signal.SIGTERM)

                # Wait for graceful shutdown
                try:
                    logger.debug("Waiting up to 10 seconds for graceful shutdown")
                    self.process.wait(timeout=10)
                    logger.debug("REAPER shut down gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("REAPER didn't stop gracefully within 10 seconds, forcing termination")
                    print("REAPER didn't stop gracefully, forcing...")
                    os.killpg(process_group, signal.SIGKILL)
                    logger.debug("Sent SIGKILL to force termination")

                self.process = None
                logger.info("REAPER process stopped successfully")
                print("REAPER process stopped")

            except Exception as e:
                logger.exception(f"Exception stopping REAPER process: {e}")
                print(f"ERROR stopping REAPER process: {e}")
                success = False
        else:
            logger.debug("No REAPER process to stop")

        # Additional cleanup: kill any remaining REAPER processes
        try:
            logger.debug("Checking for remaining REAPER instances with pkill")
            print("Checking for remaining REAPER instances...")
            result = subprocess.run(['pkill', '-f', 'REAPER'], capture_output=True, text=True)
            logger.debug(f"pkill result: returncode={result.returncode}, stdout='{result.stdout}', stderr='{result.stderr}'")

            if result.returncode == 0:
                logger.info("Killed remaining REAPER instances")
                print("Killed remaining REAPER instances")
            else:
                logger.debug("No additional REAPER instances found to kill")

            logger.debug("Sleeping 2 seconds to allow process termination")
            time.sleep(2)  # Give time for processes to terminate
        except Exception as e:
            logger.warning(f"Could not kill remaining REAPER instances: {e}")
            print(f"Warning: Could not kill remaining REAPER instances: {e}")

        logger.debug(f"stop_reaper returning: {success}")
        return success

    def is_running(self) -> bool:
        """Check if REAPER process is running."""
        running = self.process is not None and self.process.poll() is None
        logger.debug(f"REAPER is_running check: {running}")
        return running

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure REAPER is stopped."""
        self.stop_reaper()
