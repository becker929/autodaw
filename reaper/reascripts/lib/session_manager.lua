-- session_manager.lua - Session management and render config execution

local session_manager = {}
local json = require("lib.json")
local utils = require("lib.utils")
local constants = require("lib.constants")
local fx_manager = require("lib.fx_manager")
local project_manager = require("lib.project_manager")

-- Load and parse session JSON file
function session_manager.load_session(session_filename)
    -- Use script directory as base path, not REAPER project path
    local script_path = utils.get_script_path()
    local base_path
    if script_path then
        base_path = script_path .. "../../"  -- Go up two levels from reascripts/lib/ to reaper/
    else
        -- Fallback: use current working directory if script path is not available
        base_path = "./"
    end
    local session_path = base_path .. constants.SESSION_CONFIGS_DIR .. "/" .. session_filename

    if not utils.file_exists(session_path) then
        error(constants.ERROR_SESSION_NOT_FOUND .. ": " .. session_path)
    end

    local file = io.open(session_path, "r")
    if not file then
        error(constants.ERROR_SESSION_NOT_FOUND .. ": " .. session_path)
    end

    local content = file:read("*all")
    file:close()

    local session_data = json.decode(content)
    if not session_data then
        error(constants.ERROR_INVALID_JSON .. ": " .. session_path)
    end

    session_manager.validate_session(session_data)
    return session_data
end

-- Validate session structure
function session_manager.validate_session(session_data)
    if not session_data.session_name then
        error("Missing session_name in session data")
    end

    if not session_data.render_configs or type(session_data.render_configs) ~= "table" then
        error(constants.ERROR_MISSING_RENDER_CONFIGS)
    end

    if #session_data.render_configs == 0 then
        error(constants.ERROR_MISSING_RENDER_CONFIGS)
    end

    -- Validate each render config
    for i, config in ipairs(session_data.render_configs) do
        if not config.render_id then
            error("Missing render_id in render config " .. i)
        end
        if not config.tracks or type(config.tracks) ~= "table" then
            error("Missing or invalid tracks in render config " .. config.render_id)
        end
        if not config.parameters or type(config.parameters) ~= "table" then
            error("Missing or invalid parameters in render config " .. config.render_id)
        end
        if not config.midi_files or type(config.midi_files) ~= "table" then
            error("Missing or invalid midi_files in render config " .. config.render_id)
        end
    end
end

-- Execute a single render config
function session_manager.execute_render_config(session_name, render_config)
    utils.print("=== Executing Render Config: " .. render_config.render_id .. " ===")

    -- Step 1: Clear project
    project_manager.clear_project()

    -- Step 2: Set up tracks
    session_manager.setup_tracks(render_config.tracks)

    -- Step 3: Apply FX parameters (before MIDI loading)
    local success_count, total_count = fx_manager.process_param_changes(render_config.parameters)
    utils.print("Applied " .. success_count .. " of " .. total_count .. " parameters")

    -- Step 4: Load MIDI files
    session_manager.load_midi_files(render_config.midi_files)

    -- Step 5: Render project
    local script_path = utils.get_script_path()
    local base_path
    if script_path then
        base_path = script_path .. "../../"  -- Go up two levels from reascripts/lib/ to reaper/
    else
        base_path = "./"
    end
    local render_dir = base_path .. constants.RENDERS_DIR

    local render_options = render_config.render_options or {}
    render_options.session_name = session_name
    render_options.render_id = render_config.render_id

    project_manager.render_project(render_dir, "params", render_options)
    utils.print("Render completed: " .. render_config.render_id)
end

-- Set up tracks from render config
function session_manager.setup_tracks(tracks_config)
    for _, track_config in ipairs(tracks_config) do
        -- Insert track at specified index
        reaper.InsertTrackAtIndex(track_config.index, false)
        local track = reaper.GetTrack(0, track_config.index)

        if not track then
            error(constants.ERROR_TRACK_SETUP_FAILED .. ": track index " .. track_config.index)
        end

        -- Set track name
        if track_config.name then
            reaper.GetSetMediaTrackInfo_String(track, "P_NAME", track_config.name, true)
        end

        -- Add FX chain
        if track_config.fx_chain then
            for _, fx_config in ipairs(track_config.fx_chain) do
                local fx_index = reaper.TrackFX_AddByName(track, fx_config.plugin_name, false, -1)
                if fx_index == -1 then
                    error(constants.ERROR_TRACK_SETUP_FAILED .. ": failed to add FX " .. fx_config.plugin_name)
                end
                utils.print("Added FX: " .. fx_config.plugin_name .. " to track " .. track_config.index)
            end
        end
    end
end

-- Load MIDI files according to track mapping
function session_manager.load_midi_files(midi_files_config)
    -- Use script directory as base path for MIDI files
    local script_path = utils.get_script_path()
    local base_path
    if script_path then
        base_path = script_path .. "../../"  -- Go up two levels from reascripts/lib/ to reaper/
    else
        base_path = "./"
    end

    for track_index, midi_filename in pairs(midi_files_config) do
        local track_idx = tonumber(track_index)
        if not track_idx then
            error(constants.ERROR_MIDI_LOAD_FAILED .. ": invalid track index " .. track_index)
        end

        local track = reaper.GetTrack(0, track_idx)
        if not track then
            error(constants.ERROR_MIDI_LOAD_FAILED .. ": track not found " .. track_idx)
        end

        local midi_path = base_path .. midi_filename
        if not utils.file_exists(midi_path) then
            error(constants.ERROR_MIDI_LOAD_FAILED .. ": MIDI file not found " .. midi_path)
        end

        local media_item = reaper.InsertMedia(midi_path, 0)
        if not media_item then
            error(constants.ERROR_MIDI_LOAD_FAILED .. ": failed to insert " .. midi_filename)
        end

        utils.print("Loaded MIDI file: " .. midi_filename .. " to track " .. track_idx)
    end
end

-- Execute entire session
function session_manager.execute_session(session_filename)
    local session_data = session_manager.load_session(session_filename)

    utils.print("=== Starting Session: " .. session_data.session_name .. " ===")
    utils.print("Render configs to execute: " .. #session_data.render_configs)

    -- Load parameter mapping
    fx_manager.load_param_mapping()

    -- Execute each render config
    for i, render_config in ipairs(session_data.render_configs) do
        local success, error_msg = pcall(function()
            session_manager.execute_render_config(session_data.session_name, render_config)
        end)

        if not success then
            error("Render config " .. render_config.render_id .. " failed: " .. tostring(error_msg))
        end
    end

    utils.print("=== Session Complete: " .. session_data.session_name .. " ===")
end

return session_manager
