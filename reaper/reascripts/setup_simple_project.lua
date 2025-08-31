-- Define reaper as a global to avoid linter warnings
reaper = reaper

local module = {}

-- Helper function for console output
local function print(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Create a simple project with a track and MIDI item
function module.setup_simple_project()
    print("Setting up a simple project...")

    -- Import clear_project module
    local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
    package.path = script_path .. "?.lua;" .. package.path
    local clear_project = require("clear_project")

    -- Clear the project first
    clear_project()

    -- Create a new track
    reaper.InsertTrackAtIndex(0, true)
    local track = reaper.GetTrack(0, 0)

    -- Name the track
    reaper.GetSetMediaTrackInfo_String(track, "P_NAME", "Serum Track", true)

                -- Add Serum VST to the track
    print("Adding Serum VST to track...")
    local fx_index = reaper.TrackFX_AddByName(track, "Serum (Xfer Records)", false, 1)

    if fx_index < 0 then
        print("ERROR: Failed to add Serum VST.")
        return false
    else
        print("Successfully added Serum VST")
    end

    -- Create a MIDI item (1 bar at 120bpm = 2 seconds)
    local start_time = 0
    local length = 2
    local midi_item = reaper.CreateNewMIDIItemInProj(track, start_time, start_time + length)

    -- Get the MIDI take
    local midi_take = reaper.GetActiveTake(midi_item)

    -- Add a simple MIDI note (C4, velocity 100, at start, 1 beat long)
    reaper.MIDI_InsertNote(midi_take, false, false, 0, 960, 0, 60, 100)

    -- Update the MIDI item
    reaper.MIDI_Sort(midi_take)

    print("Project setup complete")
    return true
end

-- Run the function if script is executed directly
if not ... then
    print("=== Setting up simple project directly ===")
    module.setup_simple_project()
    print("=== Simple project setup complete ===")
end

return module.setup_simple_project
