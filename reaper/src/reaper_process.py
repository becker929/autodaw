"""REAPER process management."""

import subprocess
import signal
import time
import os
from pathlib import Path
from typing import Optional
from config import SystemConfig


class ReaperProcessManager:
    """Manages REAPER process lifecycle."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        
    def start_reaper(self, project_file: Optional[Path] = None) -> bool:
        """Start REAPER with optional project file."""
        if self.process and self.process.poll() is None:
            print("REAPER is already running")
            return True
            
        print("Starting REAPER...")
        
        cmd = [str(self.config.reaper_path)]
        if project_file:
            cmd.append(str(project_file))
            
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group
            )
            
            # Give REAPER a moment to start
            print("Waiting for REAPER to start...")
            time.sleep(3)
            
            # Check if process is still running
            if self.process.poll() is not None:
                print("REAPER process exited immediately")
                return False
                
            print("REAPER started successfully")
            return True
            
        except Exception as e:
            print(f"ERROR starting REAPER: {e}")
            return False
    
    def stop_reaper(self) -> bool:
        """Stop REAPER process and ensure all instances are closed."""
        success = True
        
        if self.process:
            print("Stopping REAPER process...")
            try:
                # Send SIGTERM to process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print("REAPER didn't stop gracefully, forcing...")
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    
                self.process = None
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
    
    def is_running(self) -> bool:
        """Check if REAPER process is running."""
        return self.process is not None and self.process.poll() is None
    
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure REAPER is stopped."""
        self.stop_reaper()
