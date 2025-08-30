#!/usr/bin/env python3
"""
REAPER Automation System v2 - Clean Architecture
Main entry point with improved separation of concerns and type safety.
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (SystemConfig, ParameterSpec, SweepConfiguration, ConfigManager,
                   SessionConfig, setup_session_logging, get_logger)
from workflow_orchestrator import WorkflowOrchestrator, MultiParameterWorkflowOrchestrator
from parameter_sweep import COMMON_PARAMETERS

# Initially set up console-only logging (session-specific logging happens later)
setup_session_logging(log_level="DEBUG", enable_file_logging=False)
logger = get_logger(__name__)


def run_session_workflow(orchestrator: MultiParameterWorkflowOrchestrator, session_name: str) -> int:
    """Run a complete session-based workflow."""
    logger.info(f"Starting session-based workflow: {session_name}")
    logger.debug(f"Orchestrator type: {type(orchestrator).__name__}")

    print(f"Running session-based workflow: {session_name}")
    print("=" * 60)

    try:
        logger.debug("Initializing ConfigManager")
        # Load session configuration
        config_manager = ConfigManager()
        logger.debug(f"Loading session config for: {session_name}")
        session_config = config_manager.load_session_config(session_name)

        logger.info(f"Session config loaded successfully", {
            'session_name': session_config.session_name,
            'session_id': session_config.session_id,
            'project_file': session_config.project_file,
            'render_count': len(session_config.renders)
        })

        print(f"Loaded session: {session_config.session_name}")
        print(f"Session ID: {session_config.session_id}")
        print(f"Project file: {session_config.project_file}")
        print(f"Number of renders: {len(session_config.renders)}")

        # Verify project file exists
        if session_config.project_file and not Path(session_config.project_file).exists():
            logger.error(f"Project file not found: {session_config.project_file}")
            print(f"Error: Project file not found: {session_config.project_file}")
            return 1

        logger.debug("Project file verification passed")

        # Set up session structure with timestamp-based naming
        session_run_name = session_config.get_session_run_dir()
        base_session_dir = Path("./sessions/runs")
        session_dir = base_session_dir / session_run_name
        session_dir.mkdir(parents=True, exist_ok=True)

        # Create organized subdirectories
        (session_dir / "midi").mkdir(exist_ok=True)
        (session_dir / "params").mkdir(exist_ok=True)
        (session_dir / "audio").mkdir(exist_ok=True)

        # Set up session-specific logging (all logs go in session directory)
        from config import setup_session_logging
        setup_session_logging(log_level="DEBUG", session_dir=session_dir, enable_file_logging=True)

        # Get session-specific logger
        session_logger = logging.getLogger(f"session_{session_config.session_id}")

        logger.info(f"Starting session workflow: {session_name}")
        logger.info(f"Session config: {len(session_config.renders)} renders")
        logger.info(f"Session directory: {session_dir}")
        session_logger.info(f"Session-specific logging initialized for {session_name}")

        # Process each render
        results = []
        logger.debug(f"Processing {len(session_config.renders)} renders")

        for i, render_config in enumerate(session_config.renders, 1):
            logger.info(f"Starting render {i}/{len(session_config.renders)}: {render_config.name}")
            session_logger.info(f"Processing render {i}: {render_config.name}")

            print(f"\n--- Processing Render {i}/{len(session_config.renders)}: {render_config.name} ---")

            # Convert render config to parameter dict
            parameters = {}
            for param_name, param_config in render_config.parameters.items():
                parameters[param_name] = param_config.value

            logger.debug(f"Render {render_config.name} parameters: {parameters}")
            session_logger.debug(f"Parameters for {render_config.name}: {parameters}")
            print(f"Parameters: {parameters}")

            # Set up automation config for this render
            logger.debug(f"Creating automation config for render {render_config.name}")
            from config import AutomationConfig
            automation_config = AutomationConfig(
                workflow_mode="full",
                target_parameter="session_render",  # Generic target
                parameter_value=0.0,  # Not used in session mode
                session_id=session_config.session_id,
                output_dir=session_dir
            )

            # Save automation config for Lua scripts to read
            config_file_path = Path("automation_config.txt")
            logger.debug(f"Saving automation config to {config_file_path}")
            automation_config.save_to_file(config_file_path)
            session_logger.debug(f"Automation config saved for {render_config.name}")

            # Add render name to config for Lua scripts
            logger.debug(f"Appending render-specific config for {render_config.name}")
            with open("automation_config.txt", "a") as f:
                f.write(f"render_name={render_config.name}\n")
                if session_config.global_midi_config and session_config.global_midi_config.midi_files:
                    logger.debug(f"Processing MIDI config for render {render_config.name}")
                    # Create a simple JSON config for MIDI files in session root
                    import json
                    midi_config_file = session_dir / f"midi_config_{render_config.name}.json"
                    midi_data = {
                        "midi_files": session_config.global_midi_config.midi_files,
                        "track_index": session_config.global_midi_config.track_index,
                        "clear_existing": session_config.global_midi_config.clear_existing
                    }
                    logger.debug(f"Writing MIDI config to session root: {midi_config_file}")
                    session_logger.debug(f"MIDI files for {render_config.name}: {midi_data['midi_files']}")
                    with open(midi_config_file, 'w') as midi_f:
                        json.dump(midi_data, midi_f, indent=2)
                    f.write(f"midi_config={midi_config_file}\n")

            # Run the workflow for this render
            try:
                logger.info(f"Executing workflow for render {render_config.name}")
                session_logger.info(f"Starting workflow execution for {render_config.name}")

                result = orchestrator.run_single_parameter_session(
                    session_id=f"{session_config.session_id}_{render_config.name}",
                    parameters=parameters,
                    project_file=Path(session_config.project_file) if session_config.project_file else None
                )
                results.append(result)

                if result.success:
                    logger.info(f"Render {render_config.name} completed successfully")
                    session_logger.info(f"Render {render_config.name} SUCCESS - execution time: {result.execution_time_seconds:.2f}s, artifacts: {result.artifacts_created}")
                    print(f"✅ Render {render_config.name} completed successfully")
                else:
                    logger.error(f"Render {render_config.name} failed: {result.error_message}")
                    session_logger.error(f"Render {render_config.name} FAILED: {result.error_message}")
                    print(f"❌ Render {render_config.name} failed: {result.error_message}")

            except Exception as e:
                logger.exception(f"Exception processing render {render_config.name}: {e}")
                session_logger.exception(f"Exception in render {render_config.name}: {e}")
                print(f"❌ Error processing render {render_config.name}: {e}")
                results.append(None)

        # Summary
        successful_renders = sum(1 for r in results if r and r.success)
        total_renders = len(session_config.renders)

        logger.info(f"Session workflow completed: {successful_renders}/{total_renders} successful renders")
        session_logger.info(f"Session summary: {successful_renders}/{total_renders} successful, output: {session_config.output_directory}")

        print(f"\n" + "=" * 60)
        print("SESSION SUMMARY")
        print("=" * 60)
        print(f"Session: {session_config.session_name} ({session_config.session_id})")
        print(f"Successful renders: {successful_renders}/{total_renders}")
        print(f"Session directory: {session_dir}")
        print(f"Log file: {log_file}")

        # Log detailed results
        for i, result in enumerate(results):
            if result:
                logger.debug(f"Result {i+1}: success={result.success}, time={result.execution_time_seconds:.2f}s, artifacts={result.artifacts_created}")

        return_code = 0 if successful_renders == total_renders else 1
        logger.info(f"Session workflow returning exit code: {return_code}")
        return return_code

    except FileNotFoundError as e:
        logger.error(f"File not found error in session workflow: {e}")
        print(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error in session workflow: {e}")
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point with clean architecture."""
    logger.info("=== REAPER Automation System v2 Starting ===")
    logger.debug(f"Command line arguments: {sys.argv}")

    # Initialize system configuration
    try:
        logger.debug("Initializing system configuration")
        system_config = SystemConfig()
        logger.debug(f"System config created: reaper_path={system_config.reaper_path}")
        system_config.validate()
        logger.info("System configuration validated successfully")
    except Exception as e:
        logger.error(f"System configuration error: {e}")
        print(f"System configuration error: {e}")
        print("Please check REAPER installation and startup script configuration.")
        return 1

    # Create orchestrator
    logger.debug("Creating MultiParameterWorkflowOrchestrator")
    orchestrator = MultiParameterWorkflowOrchestrator(system_config)
    logger.info("Workflow orchestrator initialized")

    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        logger.info(f"Executing command: {command}")

        if command == "octave-sweep":
            # Classic octave sweep (backward compatibility)
            project_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/serum/serum1.RPP")
            logger.info(f"Running octave sweep with project file: {project_file}")
            if not project_file.exists():
                logger.error(f"Project file not found: {project_file}")
                print(f"Project file not found: {project_file}")
                return 1
            logger.debug("Starting octave sweep execution")
            results = orchestrator.run_octave_sweep(project_file)
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Octave sweep completed: {success_count}/{len(results)} successful")
            return 0 if all(r.success for r in results) else 1

        elif command == "discover":
            # Parameter discovery
            project_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/serum/serum1.RPP")
            logger.info(f"Running parameter discovery with project file: {project_file}")
            if not project_file.exists():
                logger.error(f"Project file not found for discovery: {project_file}")
                print(f"Project file not found: {project_file}")
                return 1
            logger.debug("Starting parameter discovery")
            success = orchestrator.discover_parameters(project_file)
            logger.info(f"Parameter discovery completed: {'success' if success else 'failed'}")
            return 0 if success else 1

        elif command == "multi-param":
            # Multi-parameter sweep example
            project_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/serum/serum1.RPP")
            logger.info(f"Running multi-parameter sweep with project file: {project_file}")
            if not project_file.exists():
                logger.error(f"Project file not found for multi-param: {project_file}")
                print(f"Project file not found: {project_file}")
                return 1
            logger.debug("Starting filter and envelope sweep")
            results = orchestrator.run_filter_and_envelope_sweep(project_file)
            success_count = sum(1 for r in results if r.success)
            logger.info(f"Multi-parameter sweep completed: {success_count}/{len(results)} successful")
            return 0 if all(r.success for r in results) else 1



        elif command == "custom-sweep":
            # Custom parameter sweep
            if len(sys.argv) < 3:
                print("Usage: main.py custom-sweep <param1:min:max:steps> [param2:min:max:steps] ...")
                return 1

            try:
                parameters = []
                for param_spec in sys.argv[2:]:
                    if param_spec.startswith("--"):
                        break  # Stop at options

                    parts = param_spec.split(":")
                    if len(parts) != 4:
                        raise ValueError(f"Invalid parameter spec: {param_spec}")

                    name, min_val, max_val, steps = parts
                    parameters.append(ParameterSpec(
                        name=name,
                        min_value=float(min_val),
                        max_value=float(max_val),
                        steps=int(steps)
                    ))

                # Look for project file option
                project_file = Path("data/serum/serum1.RPP")  # Default
                for i, arg in enumerate(sys.argv):
                    if arg == "--project" and i + 1 < len(sys.argv):
                        project_file = Path(sys.argv[i + 1])
                        break

                if not project_file.exists():
                    print(f"Project file not found: {project_file}")
                    return 1

                results = orchestrator.run_multi_parameter_sweep(
                    parameters=parameters,
                    project_file=project_file
                )
                return 0 if all(r.success for r in results) else 1

            except Exception as e:
                print(f"Error parsing custom sweep parameters: {e}")
                return 1

        elif command == "session":
            # Run session-based workflow
            if len(sys.argv) < 3:
                print("Usage: main.py session <session_name>")
                return 1

            session_name = sys.argv[2]
            return run_session_workflow(orchestrator, session_name)

        else:
            print_usage()
            return 1
    else:
        # Default: run octave sweep with default project
        default_project = Path("data/serum/serum1.RPP")
        if not default_project.exists():
            print(f"Default project file not found: {default_project}")
            print("Please specify a project file or ensure the default project exists.")
            return 1
        results = orchestrator.run_octave_sweep(default_project)
        return 0 if all(r.success for r in results) else 1


def print_usage():
    """Print usage information."""
    print("REAPER Automation System v2")
    print("===========================")
    print()
    print("Usage:")
    print("  uv run main.py [command] [options]")
    print()
    print("Commands:")
    print("  octave-sweep [project]           Run octave sweep (-2 to +2, 5 steps)")
    print("  discover [project]               Discover VST parameters")
    print("  multi-param [project]            Run filter cutoff + attack envelope sweep")
    print("  custom-sweep <specs> [options]   Custom parameter sweep")
    print("  session <session_name>           Run session-based workflow with JSON config")
    print()
    print("Custom sweep parameter specs:")
    print("  <param_name>:<min>:<max>:<steps>")
    print("  Example: octave:-2:2:5 filter_cutoff:0:1:10")
    print()
    print("Options:")
    print("  --project <path>                 Project file to use")
    print()
    print("Examples:")
    print("  uv run main.py octave-sweep")
    print("  uv run main.py discover data/serum/serum1.RPP")
    print("  uv run main.py custom-sweep octave:-1:1:3 --project data/serum/serum1.RPP")
    print("  uv run main.py multi-param")
    print()
    print("Available common parameters:")
    for name, spec in COMMON_PARAMETERS.items():
        print(f"  {name:<15} {spec.min_value:>6.1f} to {spec.max_value:<6.1f} ({spec.steps} steps)")


if __name__ == "__main__":
    sys.exit(main())
