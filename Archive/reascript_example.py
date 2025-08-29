#!/usr/bin/env python3
"""
ReaScript Example - A Python script that can be executed within REAPER
This script demonstrates basic REAPER API usage and reports to stdout
"""

import sys
import os

# REAPER API is available when running as a ReaScript
try:
    import reaper_python as reaper
    REAPER_AVAILABLE = True
except ImportError:
    REAPER_AVAILABLE = False
    print("Warning: REAPER API not available - running in standalone mode")

def log_message(msg):
    """Log message to both console, REAPER console, and file"""
    print(msg)  # Still print to stdout

    # Write to file for visibility
    with open("/tmp/reascript_output.txt", "a") as f:
        f.write(msg + "\n")

    # Show in REAPER console if available
    if REAPER_AVAILABLE:
        reaper.ShowConsoleMsg(msg + "\n")

def main():
    """Main ReaScript function"""
    # Clear previous output file
    with open("/tmp/reascript_output.txt", "w") as f:
        f.write("")

    log_message("=== REAPER ReaScript Execution Started ===")

    if not REAPER_AVAILABLE:
        log_message("Error: This script must be run within REAPER as a ReaScript")
        return

        # Get project information
    project = reaper.EnumProjects(-1, "")[0]
    if project:
        log_message(f"Current project: {reaper.GetProjectName(project, '')}")
    else:
        log_message("No project loaded")

    # Get track count
    track_count = reaper.CountTracks(project)
    log_message(f"Number of tracks: {track_count}")

    # Get selected tracks
    selected_track_count = reaper.CountSelectedTracks(project)
    log_message(f"Selected tracks: {selected_track_count}")

    # List all tracks
    if track_count > 0:
        log_message("\nTrack List:")
        for i in range(track_count):
            track = reaper.GetTrack(project, i)
            track_name = reaper.GetTrackName(track, "")
            if not track_name[1]:  # If no custom name
                track_name = f"Track {i+1}"
            else:
                track_name = track_name[1]

            # Get track volume and pan
            volume = reaper.GetMediaTrackInfo_Value(track, "D_VOL")
            pan = reaper.GetMediaTrackInfo_Value(track, "D_PAN")

            log_message(f"  {i+1}: {track_name} (Vol: {volume:.2f}, Pan: {pan:.2f})")

    # Get timeline information
    play_position = reaper.GetPlayPosition()
    cursor_position = reaper.GetCursorPosition()

    log_message(f"\nTimeline Info:")
    log_message(f"  Play position: {play_position:.3f} seconds")
    log_message(f"  Edit cursor: {cursor_position:.3f} seconds")

    # Check if playing
    play_state = reaper.GetPlayState()
    state_text = {
        0: "stopped",
        1: "playing",
        2: "paused",
        4: "recording",
        5: "recording (paused)"
    }.get(play_state, "unknown")
    log_message(f"  Play state: {state_text}")

    # Get project sample rate and length
    sample_rate = reaper.GetSetProjectInfo(project, "PROJECT_SRATE", 0, False)
    project_length = reaper.GetProjectLength(project)

    log_message(f"\nProject Info:")
    log_message(f"  Sample rate: {int(sample_rate)} Hz")
    log_message(f"  Project length: {project_length:.3f} seconds")

    # Create a simple track if none exist
    if track_count == 0:
        log_message("\nNo tracks found - creating a new track...")
        reaper.InsertTrackAtIndex(0, False)
        new_track = reaper.GetTrack(project, 0)
        reaper.GetSetMediaTrackInfo_String(new_track, "P_NAME", "ReaScript Created Track", True)
        log_message("Created new track: 'ReaScript Created Track'")

    log_message("\n=== ReaScript Execution Completed ===")
    log_message(f"Output saved to: /tmp/reascript_output.txt")

    # Force REAPER to update display
    reaper.UpdateArrange()

if __name__ == "__main__":
    main()
