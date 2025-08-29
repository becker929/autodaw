#!/usr/bin/env python3
"""
REAPER Control Script using reapy-boost
This script connects to REAPER externally and reports information to stdout
"""

import reapy_boost as reapy

def main():
    """Main function using reapy-boost"""
    print("=== REAPER reapy-boost Script Started ===")

    try:
        # Connect to REAPER (must be running)
        with reapy.inside_reaper():
            print("Successfully connected to REAPER")

            # Get current project
            project = reapy.Project()
            print(f"Current project: {project.name}")

            # Get track count
            track_count = len(project.tracks)
            print(f"Number of tracks: {track_count}")

            # List all tracks
            if track_count > 0:
                print("\nTrack List:")
                for i, track in enumerate(project.tracks):
                    volume = track.volume
                    pan = track.pan
                    name = track.name if track.name else f"Track {i+1}"
                    print(f"  {i+1}: {name} (Vol: {volume:.2f}, Pan: {pan:.2f})")

            # Get timeline information
            play_position = project.play_position
            cursor_position = project.cursor_position

            print(f"\nTimeline Info:")
            print(f"  Play position: {play_position:.3f} seconds")
            print(f"  Edit cursor: {cursor_position:.3f} seconds")

            # Check if playing
            is_playing = project.is_playing
            is_paused = project.is_paused
            is_recording = project.is_recording

            if is_recording:
                state = "recording"
            elif is_playing:
                state = "playing"
            elif is_paused:
                state = "paused"
            else:
                state = "stopped"

            print(f"  Play state: {state}")

            # Get project info
            try:
                bpm = project.bpm
                print(f"\nProject Info:")
                print(f"  BPM: {bpm}")

                # Try to get other project info if available
                if hasattr(project, 'sample_rate'):
                    print(f"  Sample rate: {int(project.sample_rate)} Hz")
                if hasattr(project, 'length'):
                    print(f"  Project length: {project.length:.3f} seconds")

            except Exception as e:
                print(f"\nProject Info: (Some attributes unavailable: {e})")

            # Create a track if none exist
            if track_count == 0:
                print("\nNo tracks found - creating a new track...")
                new_track = project.add_track()
                new_track.name = "reapy Created Track"
                print("Created new track: 'reapy Created Track'")

            print("\n=== reapy-boost Script Completed ===")

    except Exception as e:
        print(f"Error connecting to REAPER: {e}")
        print("Make sure REAPER is running and reapy is properly configured")
        return False

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
