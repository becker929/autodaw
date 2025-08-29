#!/usr/bin/env python3
"""
Simple REAPER Project Reporter
A streamlined script to report basic project state from a running REAPER instance.
"""

import reapy_boost as reapy
import json
from datetime import datetime

def report_project_state():
    """Report the current state of the REAPER project"""
    print("=== REAPER Project State Report ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        with reapy.inside_reaper():
            print("✓ Connected to REAPER")

            project = reapy.Project()

            # Basic project info
            print(f"\nProject Name: {project.name}")
            print(f"Project Path: {project.path}")
            print(f"Number of Tracks: {len(project.tracks)}")
            print(f"Number of Items: {len(project.items)}")
            print(f"Project Length: {project.length:.3f} seconds")

            # Track information
            print(f"\n{'='*50}")
            print("TRACKS")
            print(f"{'='*50}")

            for i, track in enumerate(project.tracks):
                print(f"\nTrack {i}: '{track.name}'")

                # Safely get track properties
                try:
                    print(f"  • Muted: {track.is_muted}")
                except:
                    print(f"  • Muted: N/A")

                try:
                    print(f"  • Soloed: {track.solo()}")
                except:
                    try:
                        print(f"  • Soloed: {track.is_solo}")
                    except:
                        print(f"  • Soloed: N/A")

                try:
                    print(f"  • Volume: {track.volume:.3f}")
                except:
                    print(f"  • Volume: N/A")

                try:
                    print(f"  • Pan: {track.pan:.3f}")
                except:
                    print(f"  • Pan: N/A")

                try:
                    print(f"  • Record Armed: {track.is_record_armed}")
                except:
                    try:
                        print(f"  • Record Armed: {track.record_arm}")
                    except:
                        print(f"  • Record Armed: N/A")

                try:
                    print(f"  • Items: {len(track.items)}")
                except:
                    print(f"  • Items: N/A")

                try:
                    print(f"  • FX Count: {len(track.fxs)}")
                except:
                    print(f"  • FX Count: N/A")

                # FX information
                if track.fxs:
                    print("  • FX:")
                    for j, fx in enumerate(track.fxs):
                        try:
                            enabled_status = "Enabled" if fx.is_enabled else "Disabled"
                            print(f"    [{j}] {fx.name} ({enabled_status})")

                            # Try to get parameter count
                            try:
                                param_count = fx.n_params
                                print(f"        Parameters: {param_count}")

                                # Show first 5 parameters as example
                                if param_count > 0:
                                    print("        Sample parameters:")
                                    for k in range(min(5, param_count)):
                                        try:
                                            param = fx.params[k]
                                            print(f"          [{k}] {param.name}: {param.formatted_value}")
                                        except:
                                            try:
                                                # Try alternative parameter access
                                                param_name = fx.get_param_name(k)
                                                param_value = fx.get_param_formatted(k)
                                                print(f"          [{k}] {param_name}: {param_value}")
                                            except:
                                                print(f"          [{k}] Parameter {k}: (unable to read)")

                                    if param_count > 5:
                                        print(f"          ... and {param_count - 5} more parameters")

                            except Exception as e:
                                print(f"        Error reading parameters: {e}")

                        except Exception as e:
                            print(f"    [{j}] Error reading FX: {e}")

            print(f"\n{'='*50}")
            print("REPORT COMPLETE")
            print(f"{'='*50}")

            return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = report_project_state()
    exit(0 if success else 1)
