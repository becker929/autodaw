"""Workflow orchestration for automation sessions."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import itertools
import logging
from dataclasses import dataclass

from config import AutomationConfig, SystemConfig, SweepConfiguration, ParameterSpec, get_logger
from reaper_process import ReaperProcessManager
from session_manager import SessionManager
from parameter_sweep import ParameterSweepEngine
from lua_interface import LuaScriptInterface

# Set up module logger
logger = get_logger(__name__)



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
        logger.info("Initializing WorkflowOrchestrator")
        self.system_config = system_config
        logger.debug(f"System config: reaper_path={system_config.reaper_path}")

        logger.debug("Creating ReaperProcessManager")
        self.process_manager = ReaperProcessManager(system_config)

        logger.debug("Creating SessionManager")
        self.session_manager = SessionManager()

        logger.debug(f"Creating LuaScriptInterface with beacon_file={system_config.beacon_file}")
        self.lua_interface = LuaScriptInterface(system_config.beacon_file)

        logger.debug("Creating ParameterSweepEngine")
        self.sweep_engine = ParameterSweepEngine()

        logger.info("WorkflowOrchestrator initialization complete")

    def run_single_parameter_session(self,
                                   session_id: str,
                                   parameters: Dict[str, float],
                                   project_file: Optional[Path] = None) -> WorkflowResult:
        """Run a complete workflow for a single parameter combination."""
        import time
        start_time = time.time()

        logger.info(f"Starting single parameter session: {session_id}")
        logger.debug(f"Parameters: {parameters}")
        logger.debug(f"Project file: {project_file}")

        print(f"\n{'='*60}")
        print(f"SESSION {session_id}: {parameters}")
        print(f"{'='*60}")

        try:
            # Create session directory and config
            logger.debug(f"Creating session directory for {session_id}")
            session_dir = self.session_manager.create_session_directory(session_id)
            logger.info(f"Session directory created: {session_dir}")

            # Create automation config for this session
            primary_param = list(parameters.keys())[0] if parameters else "default"
            primary_value = list(parameters.values())[0] if parameters else 0.0

            logger.debug(f"Creating automation config: primary_param={primary_param}, primary_value={primary_value}")
            automation_config = AutomationConfig(
                workflow_mode="full",
                target_parameter=primary_param,  # Primary parameter
                parameter_value=primary_value,  # Primary value
                session_id=session_id,
                output_dir=session_dir
            )
            logger.debug("Automation config created")

            # Save session metadata
            metadata = {
                'parameters': parameters,
                'project_file': str(project_file) if project_file else None,
                'workflow_mode': 'full'
            }
            logger.debug(f"Saving session metadata: {len(metadata)} keys")
            self.session_manager.save_session_metadata(session_id, metadata)
            logger.debug("Session metadata saved")

            # Create config file for Lua scripts
            logger.debug("Creating config file for Lua scripts")
            self.lua_interface.create_config_for_script(automation_config, parameters)
            logger.debug("Lua script config created")

            # Start REAPER
            logger.info(f"Starting REAPER with project: {project_file}")
            if not self.process_manager.start_reaper(project_file):
                logger.error("Failed to start REAPER process")
                return WorkflowResult(
                    success=False,
                    session_id=session_id,
                    parameters=parameters,
                    error_message="Failed to start REAPER"
                )
            logger.info("REAPER started successfully")

            # Wait for workflow completion
            logger.info("Waiting for workflow completion via beacon file")
            success, beacon_data = self.lua_interface.wait_for_completion(timeout_seconds=120)
            logger.info(f"Workflow completion status: {success}")

            if beacon_data:
                logger.debug(f"Beacon data: status={beacon_data.status}, message={beacon_data.message}")

            # Stop REAPER
            logger.info("Stopping REAPER process")
            self.process_manager.stop_reaper()
            logger.debug("REAPER stopped")

            # Clean up beacon file
            logger.debug("Cleaning up beacon file")
            self.lua_interface.clear_beacon_file()



            # Collect artifacts
            logger.debug("Collecting session artifacts")
            artifacts = self.session_manager.collect_session_artifacts(session_id)
            artifact_count = len(artifacts.parameter_files + artifacts.midi_files +
                               artifacts.render_files + artifacts.audio_files)
            logger.info(f"Collected {artifact_count} artifacts")

            execution_time = time.time() - start_time
            logger.info(f"Session execution completed in {execution_time:.2f} seconds")

            result = WorkflowResult(
                success=success,
                session_id=session_id,
                parameters=parameters,
                artifacts_created=artifact_count,
                execution_time_seconds=execution_time
            )

            logger.info(f"Session {session_id} result: success={success}, artifacts={artifact_count}, time={execution_time:.2f}s")
            return result

        except Exception as e:
            logger.exception(f"Exception in session {session_id}: {e}")
            # Ensure REAPER is stopped even on error
            logger.warning("Ensuring REAPER is stopped due to exception")
            self.process_manager.stop_reaper()

            execution_time = time.time() - start_time
            logger.error(f"Session {session_id} failed after {execution_time:.2f}s: {e}")

            return WorkflowResult(
                success=False,
                session_id=session_id,
                parameters=parameters,
                error_message=str(e),
                execution_time_seconds=execution_time
            )

    def run_parameter_sweep(self,
                           sweep_config: SweepConfiguration,
                           project_file: Optional[Path] = None) -> List[WorkflowResult]:
        """Run a complete parameter sweep."""
        logger.info("Starting parameter sweep automation")
        logger.debug(f"Sweep config: strategy={sweep_config.strategy}, max_combinations={sweep_config.max_combinations}")
        logger.debug(f"Parameters: {[p.name for p in sweep_config.parameters]}")

        print("Starting Parameter Sweep Automation")
        print("===================================")

        # Validate system configuration
        try:
            logger.debug("Validating system configuration")
            self.system_config.validate()
            logger.debug("System configuration validated")
        except Exception as e:
            logger.error(f"System configuration validation failed: {e}")
            print(f"System configuration error: {e}")
            return []

        # Generate parameter combinations
        logger.debug("Generating parameter combinations")
        combinations = list(self.sweep_engine.generate_sweep(sweep_config))
        total_combinations = len(combinations)

        logger.info(f"Generated {total_combinations} parameter combinations")
        logger.debug(f"First few combinations: {combinations[:3] if len(combinations) > 3 else combinations}")

        print(f"Generated {total_combinations} parameter combinations")
        print(f"Strategy: {sweep_config.strategy}")
        print(f"Parameters: {[p.name for p in sweep_config.parameters]}")

        # Execute each combination
        results = []
        logger.info(f"Executing {total_combinations} parameter combinations")

        for i, combination in enumerate(combinations, 1):
            session_id = str(i)
            logger.info(f"Starting combination {i}/{total_combinations}: {combination}")

            result = self.run_single_parameter_session(
                session_id=session_id,
                parameters=combination,
                project_file=project_file
            )

            results.append(result)
            logger.debug(f"Combination {i} completed: success={result.success}")

            # Brief pause between sessions
            import time
            logger.debug("Pausing 2 seconds between sessions")
            time.sleep(2)

        # Print summary
        successful_count = sum(1 for r in results if r.success)
        logger.info(f"Parameter sweep completed: {successful_count}/{total_combinations} successful")
        self._print_sweep_summary(results)

        return results

    def run_octave_sweep(self, project_file: Optional[Path] = None) -> List[WorkflowResult]:
        """Run the classic octave sweep (backward compatibility)."""
        logger.info("Starting classic octave sweep (-2.0 to 2.0, 5 steps)")
        octave_spec = ParameterSpec('octave', -2.0, 2.0, 5)
        sweep_config = SweepConfiguration(
            parameters=[octave_spec],
            strategy='grid'
        )
        logger.debug(f"Octave sweep config: {octave_spec.name}, range=[{octave_spec.min_value}, {octave_spec.max_value}], steps={octave_spec.steps}")

        return self.run_parameter_sweep(sweep_config, project_file)

    def discover_parameters(self, project_file: Optional[Path] = None) -> bool:
        """Run parameter discovery workflow."""
        logger.info("Starting parameter discovery workflow")
        logger.debug(f"Project file for discovery: {project_file}")

        print("Starting Parameter Discovery")
        print("===========================")

        try:
            # Create temporary session for discovery
            session_id = "discovery"
            logger.debug(f"Creating discovery session: {session_id}")
            session_dir = self.session_manager.create_session_directory(session_id)
            logger.info(f"Discovery session directory: {session_dir}")

            config = AutomationConfig(
                workflow_mode="discovery",
                session_id=session_id,
                output_dir=session_dir
            )
            logger.debug("Discovery automation config created")

            # Create config for discovery script
            logger.debug("Creating config for discovery Lua script")
            self.lua_interface.create_config_for_script(config)

            # Start REAPER
            logger.info("Starting REAPER for parameter discovery")
            if not self.process_manager.start_reaper(project_file):
                logger.error("Failed to start REAPER for discovery")
                print("Failed to start REAPER")
                return False
            logger.debug("REAPER started for discovery")

            # Wait for discovery completion
            logger.info("Waiting for parameter discovery completion")
            success, beacon_data = self.lua_interface.wait_for_completion()
            logger.info(f"Parameter discovery completed: success={success}")

            if beacon_data:
                logger.debug(f"Discovery beacon data: {beacon_data.message}")

            # Stop REAPER
            logger.debug("Stopping REAPER after discovery")
            self.process_manager.stop_reaper()
            self.lua_interface.clear_beacon_file()

            if success:
                logger.info(f"Parameter discovery successful, results in: {session_dir}")
                print("✓ Parameter discovery completed successfully!")
                print(f"Results saved in: {session_dir}")
            else:
                logger.warning("Parameter discovery failed")
                print("✗ Parameter discovery failed")

            return success

        except Exception as e:
            logger.exception(f"Exception during parameter discovery: {e}")
            print(f"Parameter discovery error: {e}")
            logger.warning("Ensuring REAPER is stopped after discovery exception")
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

        print(f"\nResults stored in: ./outputs/")


class MultiParameterWorkflowOrchestrator(WorkflowOrchestrator):
    """Extended orchestrator for multi-parameter workflows."""

    def __init__(self, system_config: SystemConfig):
        super().__init__(system_config)

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
