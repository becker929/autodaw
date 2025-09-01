-- project_manager.lua - Project management functions
reaper = reaper

local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

local utils = require("lib.utils")
local constants = require("lib.constants")
local logger = require("lib.logger")

local project_manager = {}

-- Function to clear the current project
function project_manager.clear_project()
    logger.info("Clearing project...")

    -- Select all tracks
    reaper.SelectAllMediaItems(0, true)

    -- Delete selected items
    reaper.Main_OnCommand(40006, 0) -- Delete selected items

    -- Select all tracks
    reaper.Main_OnCommand(40296, 0) -- Select all tracks

    -- Delete selected tracks
    reaper.Main_OnCommand(40005, 0) -- Remove tracks

    -- Reset playback position to start
    reaper.SetEditCurPos(0.0, false, false)  -- Set cursor to 0 seconds

    -- Reset project timeline
    reaper.Main_OnCommand(40042, 0) -- Transport: Go to start of project

    logger.info("Project cleared.")
    return true
end

-- Function to set up a simple project with a single track and VST
function project_manager.setup_simple_project(options)
    options = options or {}
    local fx_name = options.fx_name or "Serum"
    local track_name = options.track_name or "Synth"

    utils.print("Setting up simple project...")

    -- Create a new track
    reaper.InsertTrackAtIndex(0, true)
    local track = reaper.GetTrack(0, 0)

    -- Name the track
    reaper.GetSetMediaTrackInfo_String(track, "P_NAME", track_name, true)

    -- Add FX to the track
    local fx_idx = reaper.TrackFX_AddByName(track, fx_name, false, -1)
    if fx_idx < 0 then
        utils.print("CRITICAL ERROR: Could not add FX: " .. fx_name)
        error("Failed to add FX: " .. fx_name)
        return false
    end

    -- Make the FX visible
    reaper.TrackFX_Show(track, fx_idx, 3) -- 3 = show floating window

    -- Add a simple MIDI item with some notes
    local midi_length = options.midi_length or 4.0  -- 4 seconds by default
    local midi_item = reaper.CreateNewMIDIItemInProj(track, 0, midi_length, false)

    if midi_item then
        -- Get the MIDI take
        local midi_take = reaper.GetActiveTake(midi_item)
        if midi_take then
            -- Add some simple MIDI notes (C major chord progression)
            local notes = {
                {note = 60, start = 0.0, length = 1.0, velocity = 80},    -- C4
                {note = 64, start = 0.0, length = 1.0, velocity = 80},    -- E4
                {note = 67, start = 0.0, length = 1.0, velocity = 80},    -- G4
                {note = 65, start = 1.0, length = 1.0, velocity = 80},    -- F4
                {note = 69, start = 1.0, length = 1.0, velocity = 80},    -- A4
                {note = 72, start = 1.0, length = 1.0, velocity = 80},    -- C5
                {note = 67, start = 2.0, length = 1.0, velocity = 80},    -- G4
                {note = 71, start = 2.0, length = 1.0, velocity = 80},    -- B4
                {note = 74, start = 2.0, length = 1.0, velocity = 80},    -- D5
                {note = 60, start = 3.0, length = 1.0, velocity = 80},    -- C4
                {note = 64, start = 3.0, length = 1.0, velocity = 80},    -- E4
                {note = 67, start = 3.0, length = 1.0, velocity = 80},    -- G4
            }

            for _, note in ipairs(notes) do
                local start_ppq = reaper.MIDI_GetPPQPosFromProjTime(midi_take, note.start)
                local end_ppq = reaper.MIDI_GetPPQPosFromProjTime(midi_take, note.start + note.length)
                reaper.MIDI_InsertNote(midi_take, false, false, start_ppq, end_ppq, 0, note.note, note.velocity, true)
            end

            -- Sort and update the MIDI
            reaper.MIDI_Sort(midi_take)
            utils.print("Added MIDI content with " .. #notes .. " notes")
        else
            utils.print("Warning: Could not get MIDI take")
        end
    else
        utils.print("Warning: Could not create MIDI item")
    end

    -- Set project length to match MIDI content
    reaper.GetSet_LoopTimeRange2(0, true, false, 0, midi_length, false)

    utils.print("Added " .. fx_name .. " to track " .. track_name)
    utils.print("Simple project setup complete.")

    return true
end

-- Function to render the project
function project_manager.render_project(render_dir, file_name, options)
    options = options or {}
    local sample_rate = options.sample_rate or constants.DEFAULT_SAMPLE_RATE
    local channels = options.channels or constants.DEFAULT_CHANNELS
    local render_format = options.render_format or constants.DEFAULT_RENDER_FORMAT
    local session_name = options.session_name or constants.DEFAULT_SESSION_NAME
    local render_id = options.render_id or constants.DEFAULT_RENDER_ID

    logger.info("Starting project render for: " .. render_id)

    -- Ensure render directory exists
    local success, err = utils.ensure_dir(render_dir)
    if not success then
        logger.error("CRITICAL ERROR: Could not create render directory: " .. render_dir)
        error("Failed to create render directory: " .. tostring(err))
        return nil
    end

    -- Generate timestamp for filename
    local timestamp = os.date(constants.TIMESTAMP_FORMAT)

    -- Build filename with session, render, and timestamp
    local filename_with_context = string.format(constants.RENDER_FILENAME_PATTERN,
                                               session_name, render_id, timestamp, file_name)

    -- Build full render path
    local render_file = render_dir .. "/" .. filename_with_context

    -- Set render path
    reaper.GetSetProjectInfo_String(0, "RENDER_FILE", render_file, true)

    -- Set render bounds to entire project
    reaper.GetSetProjectInfo(0, "RENDER_BOUNDSFLAG", constants.DEFAULT_RENDER_BOUNDS_FLAG, true)

    -- Set render settings
    reaper.GetSetProjectInfo(0, "RENDER_SRATE", sample_rate, true)
    reaper.GetSetProjectInfo(0, "RENDER_CHANNELS", channels, true)
    reaper.GetSetProjectInfo(0, "RENDER_SETTINGS", 0, true) -- Default settings

    -- Set render format
    if render_format ~= "" then
        reaper.GetSetProjectInfo_String(0, "RENDER_FORMAT", render_format, true)
    end

    -- Execute render (render to file, close render dialog when finished)
    logger.info("Executing render command...")
    reaper.Main_OnCommand(42230, 0) -- Render project to disk (bypass dialog)

    logger.info("Render completed to: " .. render_file)
    return render_file
end

return project_manager
