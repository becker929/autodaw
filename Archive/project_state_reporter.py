#!/usr/bin/env python3
"""
REAPER Project State Reporter
This script connects to a running REAPER instance and reports comprehensive project state,
including tracks, effects, and their parameters.
"""

import reapy_boost as reapy
import json
import time
from datetime import datetime

def get_fx_parameters(fx):
    """Get all parameters for an FX plugin"""
    parameters = {}
    try:
        # Get parameter count
        param_count = fx.n_params
        print(f"    Found {param_count} parameters")

        # Only sample first 10 parameters to avoid overwhelming output
        sample_count = min(10, param_count)
        print(f"    Sampling first {sample_count} parameters")

        for i in range(sample_count):
            try:
                # Try different methods to access parameter info
                param_info = {
                    "name": f"Parameter {i}",
                    "value": "N/A",
                    "formatted_value": "N/A",
                    "index": i
                }

                # Method 1: Try direct parameter object access with parent context
                try:
                    param = fx.params[i]

                    # Try to set parent context
                    if hasattr(param, 'parent') and not param.parent:
                        param.parent = fx
                    elif hasattr(param, 'parent_id') and not getattr(param, 'parent_id', None):
                        param.parent_id = getattr(fx, 'id', fx)

                    if hasattr(param, 'name'):
                        param_info["name"] = param.name
                    if hasattr(param, 'value'):
                        param_info["value"] = param.value
                    if hasattr(param, 'formatted_value'):
                        param_info["formatted_value"] = param.formatted_value

                except Exception as e1:
                    param_info["method1_error"] = str(e1)

                    # Method 2: Try direct FX methods if they exist
                    try:
                        if hasattr(fx, 'get_param'):
                            param_info["value"] = fx.get_param(i)
                        if hasattr(fx, 'get_param_name'):
                            param_info["name"] = fx.get_param_name(i)
                        if hasattr(fx, 'get_param_text'):
                            param_info["formatted_value"] = fx.get_param_text(i)
                    except Exception as e2:
                        param_info["method2_error"] = str(e2)

                        # Method 3: Try using reapy's native parameter access
                        try:
                            # Access via the track's FX parameter interface
                            param_info["raw_access_attempted"] = True
                        except Exception as e3:
                            param_info["method3_error"] = str(e3)

                parameters[str(i)] = param_info

            except Exception as e:
                parameters[str(i)] = {
                    "name": f"Parameter {i}",
                    "value": "N/A",
                    "formatted_value": "N/A",
                    "error": str(e),
                    "index": i
                }

        # Add summary info
        parameters["_summary"] = {
            "total_params": param_count,
            "sampled_params": sample_count,
            "note": "Only first 10 parameters sampled to avoid overwhelming output"
        }

    except Exception as e:
        print(f"    Error getting parameters: {e}")
        parameters = {"error": str(e)}

    return parameters

def get_fx_info(fx, fx_index):
    """Get comprehensive information about an FX plugin"""
    fx_info = {
        "index": fx_index,
        "name": "Unknown",
        "is_enabled": False,
        "preset": "Unknown",
        "parameters": {}
    }

    try:
        fx_info["name"] = fx.name
        fx_info["is_enabled"] = fx.is_enabled

        # Try to get preset information
        try:
            fx_info["preset"] = fx.preset
        except:
            fx_info["preset"] = "N/A"

        print(f"  FX {fx_index}: {fx_info['name']} ({'Enabled' if fx_info['is_enabled'] else 'Disabled'})")

        # Get parameters
        fx_info["parameters"] = get_fx_parameters(fx)

    except Exception as e:
        print(f"  Error getting FX {fx_index} info: {e}")
        fx_info["error"] = str(e)

    return fx_info

def get_track_info(track, track_index):
    """Get comprehensive information about a track"""
    track_info = {
        "index": track_index,
        "name": "Unknown",
        "is_muted": False,
        "is_soloed": False,
        "volume": 0.0,
        "pan": 0.0,
        "is_record_armed": False,
        "n_items": 0,
        "fx": []
    }

    try:
        track_info["name"] = track.name

        try:
            track_info["is_muted"] = track.is_muted
        except:
            track_info["is_muted"] = False

        try:
            track_info["is_soloed"] = track.solo()
        except:
            try:
                track_info["is_soloed"] = track.is_solo
            except:
                track_info["is_soloed"] = False

        try:
            track_info["volume"] = track.volume
        except:
            track_info["volume"] = 1.0

        try:
            track_info["pan"] = track.pan
        except:
            track_info["pan"] = 0.0

        try:
            track_info["is_record_armed"] = track.is_record_armed
        except:
            try:
                track_info["is_record_armed"] = track.record_arm
            except:
                track_info["is_record_armed"] = False

        try:
            track_info["n_items"] = len(track.items)
        except:
            track_info["n_items"] = 0

        print(f"\nTrack {track_index}: '{track_info['name']}'")
        print(f"  Muted: {track_info['is_muted']}, Soloed: {track_info['is_soloed']}")
        print(f"  Volume: {track_info['volume']:.3f}, Pan: {track_info['pan']:.3f}")
        print(f"  Record Armed: {track_info['is_record_armed']}, Items: {track_info['n_items']}")
        print(f"  FX Count: {len(track.fxs)}")

        # Get FX information
        for fx_index, fx in enumerate(track.fxs):
            fx_info = get_fx_info(fx, fx_index)
            track_info["fx"].append(fx_info)

    except Exception as e:
        print(f"Error getting track {track_index} info: {e}")
        track_info["error"] = str(e)

    return track_info

def get_project_info(project):
    """Get comprehensive project information"""
    project_info = {
        "name": "Unknown",
        "path": "Unknown",
        "length": 0.0,
        "n_tracks": 0,
        "n_items": 0,
        "bpm": 120.0,
        "time_signature": "4/4",
        "tracks": []
    }

    try:
        project_info["name"] = project.name
        project_info["path"] = project.path
        project_info["length"] = project.length
        project_info["n_tracks"] = len(project.tracks)
        project_info["n_items"] = len(project.items)

        # Try to get tempo/time signature info
        try:
            project_info["bpm"] = project.bpm
        except:
            project_info["bpm"] = "N/A"

        try:
            project_info["time_signature"] = project.time_signature
        except:
            project_info["time_signature"] = "N/A"

        print(f"Project: '{project_info['name']}'")
        print(f"Path: {project_info['path']}")
        print(f"Length: {project_info['length']:.3f} seconds")
        print(f"Tracks: {project_info['n_tracks']}, Items: {project_info['n_items']}")
        print(f"BPM: {project_info['bpm']}, Time Signature: {project_info['time_signature']}")

        # Get track information
        for track_index, track in enumerate(project.tracks):
            track_info = get_track_info(track, track_index)
            project_info["tracks"].append(track_info)

    except Exception as e:
        print(f"Error getting project info: {e}")
        project_info["error"] = str(e)

    return project_info

def save_report_to_file(project_info, filename=None):
    """Save the project report to a JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reaper_project_report_{timestamp}.json"

    try:
        with open(filename, 'w') as f:
            json.dump(project_info, f, indent=2, default=str)
        print(f"\n✓ Report saved to: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving report: {e}")
        return None

def print_summary(project_info):
    """Print a summary of the project state"""
    print("\n" + "="*60)
    print("PROJECT SUMMARY")
    print("="*60)

    print(f"Project Name: {project_info.get('name', 'Unknown')}")
    print(f"Total Tracks: {project_info.get('n_tracks', 0)}")
    print(f"Total Items: {project_info.get('n_items', 0)}")
    print(f"Project Length: {project_info.get('length', 0):.3f} seconds")

    # Count total FX across all tracks
    total_fx = 0
    total_params = 0

    for track in project_info.get('tracks', []):
        fx_list = track.get('fx', [])
        total_fx += len(fx_list)

        for fx in fx_list:
            params = fx.get('parameters', {})
            if isinstance(params, dict) and 'error' not in params:
                total_params += len(params)

    print(f"Total FX: {total_fx}")
    print(f"Total Parameters: {total_params}")

    # List tracks with FX
    print(f"\nTracks with FX:")
    for track in project_info.get('tracks', []):
        fx_list = track.get('fx', [])
        if fx_list:
            print(f"  • {track.get('name', 'Unknown')} ({len(fx_list)} FX)")
            for fx in fx_list:
                status = "Enabled" if fx.get('is_enabled', False) else "Disabled"
                print(f"    - {fx.get('name', 'Unknown')} ({status})")

def main():
    """Main function to report REAPER project state"""
    print("=== REAPER Project State Reporter ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        with reapy.inside_reaper():
            print("✓ Successfully connected to REAPER")

            project = reapy.Project()
            print("✓ Got current project reference")

            # Get comprehensive project information
            print("\nGathering project information...")
            project_info = get_project_info(project)

            # Print summary
            print_summary(project_info)

            # Save detailed report
            report_file = save_report_to_file(project_info)

            print(f"\n=== Report Generation Completed ===")
            return project_info, report_file

    except Exception as e:
        print(f"ERROR: Failed to connect or report - {e}")
        return None, None

if __name__ == "__main__":
    project_info, report_file = main()
    exit(0 if project_info is not None else 1)
