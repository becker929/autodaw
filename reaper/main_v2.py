#!/usr/bin/env python3
"""
REAPER Automation System v2 - Clean Architecture
Main entry point with improved separation of concerns and type safety.
"""

import sys
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import SystemConfig, ParameterSpec, SweepConfiguration
from workflow_orchestrator import WorkflowOrchestrator, MultiParameterWorkflowOrchestrator
from parameter_sweep import COMMON_PARAMETERS


def main():
    """Main entry point with clean architecture."""

    # Initialize system configuration
    try:
        system_config = SystemConfig()
        system_config.validate()
    except Exception as e:
        print(f"System configuration error: {e}")
        print("Please check REAPER installation and startup script configuration.")
        return 1

    # Check for vision debug flag
    enable_vision = "--vision-debug" in sys.argv
    if enable_vision:
        sys.argv.remove("--vision-debug")  # Remove flag from args

    # Create orchestrator
    orchestrator = MultiParameterWorkflowOrchestrator(system_config, enable_vision_debug=enable_vision)

    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "octave-sweep":
            # Classic octave sweep (backward compatibility)
            project_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/serum/serum1.RPP")
            if not project_file.exists():
                print(f"Project file not found: {project_file}")
                return 1
            results = orchestrator.run_octave_sweep(project_file)
            return 0 if all(r.success for r in results) else 1

        elif command == "discover":
            # Parameter discovery
            project_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/serum/serum1.RPP")
            if not project_file.exists():
                print(f"Project file not found: {project_file}")
                return 1
            success = orchestrator.discover_parameters(project_file)
            return 0 if success else 1

        elif command == "multi-param":
            # Multi-parameter sweep example
            project_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/serum/serum1.RPP")
            if not project_file.exists():
                print(f"Project file not found: {project_file}")
                return 1
            results = orchestrator.run_filter_and_envelope_sweep(project_file)
            return 0 if all(r.success for r in results) else 1

        elif command == "vision-debug":
            # Standalone vision debugging - pass remaining args to vision debugger
            vision_args = sys.argv[2:]  # Get args after 'vision-debug'
            import sys as vision_sys
            vision_sys.argv = ['vision_debugger.py'] + vision_args
            from src.vision_debugger import main as vision_main
            return vision_main()

        elif command == "custom-sweep":
            # Custom parameter sweep
            if len(sys.argv) < 3:
                print("Usage: main_v2.py custom-sweep <param1:min:max:steps> [param2:min:max:steps] ...")
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
    print("  uv run main_v2.py [command] [options]")
    print()
    print("Commands:")
    print("  octave-sweep [project]           Run octave sweep (-2 to +2, 5 steps)")
    print("  discover [project]               Discover VST parameters")
    print("  multi-param [project]            Run filter cutoff + attack envelope sweep")
    print("  custom-sweep <specs> [options]   Custom parameter sweep")
    print("  vision-debug <subcommand>        Vision debugging tools")
    print()
    print("Custom sweep parameter specs:")
    print("  <param_name>:<min>:<max>:<steps>")
    print("  Example: octave:-2:2:5 filter_cutoff:0:1:10")
    print()
    print("Options:")
    print("  --project <path>                 Project file to use")
    print("  --vision-debug                   Enable vision debugging for all commands")
    print()
    print("Examples:")
    print("  uv run main_v2.py octave-sweep")
    print("  uv run main_v2.py discover data/serum/serum1.RPP")
    print("  uv run main_v2.py custom-sweep octave:-1:1:3 --project data/serum/serum1.RPP")
    print("  uv run main_v2.py multi-param")
    print("  uv run main_v2.py octave-sweep --vision-debug")
    print("  uv run main_v2.py vision-debug screenshot")
    print("  uv run main_v2.py vision-debug reaper")
    print("  uv run main_v2.py vision-debug analyze")
    print()
    print("Available common parameters:")
    for name, spec in COMMON_PARAMETERS.items():
        print(f"  {name:<15} {spec.min_value:>6.1f} to {spec.max_value:<6.1f} ({spec.steps} steps)")


if __name__ == "__main__":
    sys.exit(main())
