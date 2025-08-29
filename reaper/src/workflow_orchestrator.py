"""Workflow orchestration for automation sessions."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import itertools
from dataclasses import dataclass

from config import AutomationConfig, SystemConfig, SweepConfiguration, ParameterSpec
from reaper_process import ReaperProcessManager
from session_manager import SessionManager
from parameter_sweep import ParameterSweepEngine
from lua_interface import LuaScriptInterface


@dataclass
class WorkflowResult:
    """Result of a workflow execution."""
    success: bool
    session_id: str
    parameters: Dict[str, float]
    error_message: Optional[str] = None
    artifacts_created: int = 0
    execution_time_seconds: float = 0.0


class WorkflowOrchestrator:
    """Orchestrates complete automation workflows."""

    def __init__(self, system_config: SystemConfig):
        self.system_config = system_config
        self.process_manager = ReaperProcessManager(system_config)
        self.session_manager = SessionManager()
        self.lua_interface = LuaScriptInterface(system_config.beacon_file)
        self.sweep_engine = ParameterSweepEngine()

    def run_single_parameter_session(self,
                                   session_id: str,
                                   parameters: Dict[str, float],
                                   project_file: Optional[Path] = None) -> WorkflowResult:
        """Run a complete workflow for a single parameter combination."""
        import time
        start_time = time.time()

        print(f"\n{'='*60}")
        print(f"SESSION {session_id}: {parameters}")
        print(f"{'='*60}")

        try:
            # Create session directory and config
            session_dir = self.session_manager.create_session_directory(session_id)

            # Create automation config for this session
            automation_config = AutomationConfig(
                workflow_mode="full",
                target_parameter=list(parameters.keys())[0],  # Primary parameter
                parameter_value=list(parameters.values())[0],  # Primary value
                session_id=session_id,
                output_dir=session_dir
            )

            # Save session metadata
            metadata = {
                'parameters': parameters,
                'project_file': str(project_file) if project_file else None,
                'workflow_mode': 'full'
            }
            self.session_manager.save_session_metadata(session_id, metadata)

            # Create config file for Lua scripts
            self.lua_interface.create_config_for_script(automation_config, parameters)

            # Start REAPER
            if not self.process_manager.start_reaper(project_file):
                return WorkflowResult(
                    success=False,
                    session_id=session_id,
                    parameters=parameters,
                    error_message="Failed to start REAPER"
                )

            # Wait for workflow completion
            success, beacon_data = self.lua_interface.wait_for_completion(timeout_seconds=120)

            # Stop REAPER
            self.process_manager.stop_reaper()

            # Clean up beacon file
            self.lua_interface.clear_beacon_file()

            # Collect artifacts
            artifacts = self.session_manager.collect_session_artifacts(session_id)

            execution_time = time.time() - start_time

            return WorkflowResult(
                success=success,
                session_id=session_id,
                parameters=parameters,
                artifacts_created=len(artifacts.parameter_files + artifacts.midi_files +
                                   artifacts.render_files + artifacts.audio_files),
                execution_time_seconds=execution_time
            )

        except Exception as e:
            # Ensure REAPER is stopped even on error
            self.process_manager.stop_reaper()

            return WorkflowResult(
                success=False,
                session_id=session_id,
                parameters=parameters,
                error_message=str(e),
                execution_time_seconds=time.time() - start_time
            )

    def run_parameter_sweep(self,
                           sweep_config: SweepConfiguration,
                           project_file: Optional[Path] = None) -> List[WorkflowResult]:
        """Run a complete parameter sweep."""
        print("Starting Parameter Sweep Automation")
        print("===================================")

        # Validate system configuration
        try:
            self.system_config.validate()
        except Exception as e:
            print(f"System configuration error: {e}")
            return []

        # Generate parameter combinations
        combinations = list(self.sweep_engine.generate_sweep(sweep_config))
        total_combinations = len(combinations)

        print(f"Generated {total_combinations} parameter combinations")
        print(f"Strategy: {sweep_config.strategy}")
        print(f"Parameters: {[p.name for p in sweep_config.parameters]}")

        # Execute each combination
        results = []
        for i, combination in enumerate(combinations, 1):
            session_id = str(i)

            result = self.run_single_parameter_session(
                session_id=session_id,
                parameters=combination,
                project_file=project_file
            )

            results.append(result)

            # Brief pause between sessions
            import time
            time.sleep(2)

        # Print summary
        self._print_sweep_summary(results)

        return results

    def run_octave_sweep(self, project_file: Optional[Path] = None) -> List[WorkflowResult]:
        """Run the classic octave sweep (backward compatibility)."""
        octave_spec = ParameterSpec('octave', -2.0, 2.0, 5)
        sweep_config = SweepConfiguration(
            parameters=[octave_spec],
            strategy='grid'
        )

        return self.run_parameter_sweep(sweep_config, project_file)

    def discover_parameters(self, project_file: Optional[Path] = None) -> bool:
        """Run parameter discovery workflow."""
        print("Starting Parameter Discovery")
        print("===========================")

        try:
            # Create temporary session for discovery
            session_id = "discovery"
            session_dir = self.session_manager.create_session_directory(session_id)

            config = AutomationConfig(
                workflow_mode="discovery",
                session_id=session_id,
                output_dir=session_dir
            )

            # Create config for discovery script
            self.lua_interface.create_config_for_script(config)

            # Start REAPER
            if not self.process_manager.start_reaper(project_file):
                print("Failed to start REAPER")
                return False

            # Wait for discovery completion
            success, beacon_data = self.lua_interface.wait_for_completion()

            # Stop REAPER
            self.process_manager.stop_reaper()
            self.lua_interface.clear_beacon_file()

            if success:
                print("✓ Parameter discovery completed successfully!")
                print(f"Results saved in: {session_dir}")
            else:
                print("✗ Parameter discovery failed")

            return success

        except Exception as e:
            print(f"Parameter discovery error: {e}")
            self.process_manager.stop_reaper()
            return False

    def _print_sweep_summary(self, results: List[WorkflowResult]) -> None:
        """Print summary of sweep results."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        print(f"\n{'='*60}")
        print("PARAMETER SWEEP COMPLETE - RESULTS:")
        print(f"{'='*60}")

        for result in results:
            status = "✓ SUCCESS" if result.success else "✗ FAILED"
            param_str = ", ".join([f"{k}={v:.2f}" for k, v in result.parameters.items()])
            print(f"Session {result.session_id:<3} ({param_str:<20}) {status}")

            if not result.success and result.error_message:
                print(f"    Error: {result.error_message}")

        print(f"\nSummary:")
        print(f"  Total sessions: {len(results)}")
        print(f"  Successful: {len(successful)}")
        print(f"  Failed: {len(failed)}")
        print(f"  Success rate: {len(successful)/len(results)*100:.1f}%")

        if successful:
            avg_time = sum(r.execution_time_seconds for r in successful) / len(successful)
            total_artifacts = sum(r.artifacts_created for r in successful)
            print(f"  Average execution time: {avg_time:.1f}s")
            print(f"  Total artifacts created: {total_artifacts}")

        print(f"\nResults stored in: /Users/anthonybecker/Desktop/evolver_sessions/")


class MultiParameterWorkflowOrchestrator(WorkflowOrchestrator):
    """Extended orchestrator for multi-parameter workflows."""

    def run_multi_parameter_sweep(self,
                                 parameters: List[ParameterSpec],
                                 strategy: str = 'grid',
                                 max_combinations: int = 100,
                                 project_file: Optional[Path] = None) -> List[WorkflowResult]:
        """Run a multi-parameter sweep with specified parameters."""

        sweep_config = SweepConfiguration(
            parameters=parameters,
            strategy=strategy,
            max_combinations=max_combinations
        )

        # Estimate and confirm large sweeps
        estimated_combinations = self.sweep_engine.estimate_combinations(sweep_config)
        if estimated_combinations > 50:
            print(f"Warning: This will generate {estimated_combinations} combinations")
            print("This may take a long time. Consider reducing parameters or steps.")

        return self.run_parameter_sweep(sweep_config, project_file)

    def run_filter_and_envelope_sweep(self, project_file: Optional[Path] = None) -> List[WorkflowResult]:
        """Example: Run a sweep of filter cutoff and envelope attack."""
        from parameter_sweep import COMMON_PARAMETERS

        parameters = [
            COMMON_PARAMETERS['filter_cutoff'],
            COMMON_PARAMETERS['attack']
        ]

        return self.run_multi_parameter_sweep(
            parameters=parameters,
            strategy='grid',
            max_combinations=25,  # 5x5 grid
            project_file=project_file
        )
