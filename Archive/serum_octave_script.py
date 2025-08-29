#!/usr/bin/env python3
"""
REAPER Script to Add Track with Serum VST
This script creates a new track and adds Serum VST
"""

import reapy_boost as reapy
import time

def clear_project(project):
    """Clear all tracks from the project"""
    print("Clearing project to ensure clean state...")
    initial_tracks = list(project.tracks)
    for track in initial_tracks:
        track.delete()

    track_count = len(project.tracks)
    print(f"Track count after clearing: {track_count}")
    return track_count

def create_track(project, track_name):
    """Create a new track and verify creation"""
    print("Creating new track...")
    initial_count = len(project.tracks)

    new_track = project.add_track()
    new_track.name = track_name

    updated_count = len(project.tracks)
    if updated_count != initial_count + 1:
        raise Exception(f"Track creation failed. Expected {initial_count + 1}, got {updated_count}")

    print(f"✓ Track created successfully: '{new_track.name}' (Track count: {updated_count})")
    return new_track

def add_serum_vst(track):
    """Add Serum VST to the track and verify"""
    print("Adding Serum VST...")
    initial_fx_count = len(track.fxs)
    print(f"Initial FX count on track: {initial_fx_count}")

    serum_names = ["Serum", "Serum (Xfer Records)", "Xfer Serum", "VST3:Serum"]
    serum_fx = None

    for serum_name in serum_names:
        try:
            serum_fx = track.add_fx(serum_name)
            print(f"✓ Successfully added {serum_name}")
            break
        except Exception as e:
            print(f"Failed to add {serum_name}: {e}")
            continue

    updated_fx_count = len(track.fxs)
    if serum_fx is None or updated_fx_count != initial_fx_count + 1:
        raise Exception(f"Serum VST addition failed. Expected {initial_fx_count + 1} FX, got {updated_fx_count}")

    print(f"✓ Serum VST verified on track (FX count: {updated_fx_count})")
    time.sleep(2)  # Wait for plugin to initialize
    return serum_fx



def main():
    """Main function to add track with Serum VST"""
    print("=== REAPER Serum VST Script Started ===")

    try:
        with reapy.inside_reaper():
            print("Successfully connected to REAPER")

            project = reapy.Project()
            print(f"Current project: {project.name}")

            clear_project(project)
            track = create_track(project, "Serum Track")
            serum_fx = add_serum_vst(track)

            print(f"\n=== Script Completed Successfully ===")
            print(f"✓ Track '{track.name}' created and verified")
            print(f"✓ Serum VST loaded and verified")
            return True

    except Exception as e:
        print(f"ERROR: Script failed - {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
