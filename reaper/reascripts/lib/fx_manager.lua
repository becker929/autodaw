-- fx_manager.lua - FX parameter management module
reaper = reaper

local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

local utils = require("lib.utils")
local json = require("lib.json")
local error_handler = require("lib.error_handler")

local fx_manager = {}

-- Parameter mapping data
local param_mapping = {}
local param_mapping_loaded = false

-- Function to load parameter mapping from a JSON file
function fx_manager.load_param_mapping(file_path)
    -- Use fixed path if none provided
    if not file_path then
        local script_path = utils.get_script_path()
        file_path = script_path .. "../../fx_parameters.json"
    end

        if not utils.file_exists(file_path) then
        error_handler.log_error("fx_manager.load_param_mapping",
                              "Parameter mapping file not found",
                              file_path)
        utils.print("CRITICAL ERROR: Parameter mapping file not found. Exiting script.")
        error("Parameter mapping file not found at: " .. file_path)
        -- The error() function will stop the script execution
        return false
    end

    utils.print("Loading parameter mapping from: " .. file_path)

        -- Read the file
    local json_str, err = json.read_file(file_path)
    if not json_str then
        error_handler.log_error("fx_manager.load_param_mapping",
                              "Failed to read parameter mapping file",
                              err)
        utils.print("CRITICAL ERROR: Failed to read parameter mapping file. Exiting script.")
        error("Failed to read parameter mapping file: " .. tostring(err))
        return false
    end

        -- Parse the JSON (pass true as second argument to make errors fatal)
    local data = error_handler.try(function()
        local result = json.parse_fx_mapping(json_str)
        if not result then
            error("Failed to parse parameter mapping: JSON structure not recognized")
        end
        return result
    end, true) -- true = fatal error handling

    if not data then
        -- This won't be reached due to fatal error handling, but keeping for clarity
        return false
    end

    -- Store the mapping
    param_mapping = data
    param_mapping_loaded = true

    utils.print("Parameter mapping loaded successfully.")
    return true
end

-- Helper function to get parameter by ID or index
local function get_param(track, fx_idx, param_id)
    if not track then
        return -1, "Track cannot be nil"
    end

    if fx_idx < 0 then
        return -1, "Invalid FX index"
    end

    if not param_id then
        return -1, "Parameter ID cannot be nil"
    end

    -- Convert to number if possible
    local param_idx = tonumber(param_id)

    if param_idx ~= nil then
        -- If param_id can be converted to number, treat it as parameter index
        local param_count = reaper.TrackFX_GetNumParams(track, fx_idx)
        if param_idx >= 0 and param_idx < param_count then
            return param_idx
        else
            return -1, "Parameter index out of range: " .. param_idx
        end
    else
        -- Check if we have a mapping for this parameter
        if param_mapping_loaded then
            -- Get FX name
            local _, fx_name = reaper.TrackFX_GetFXName(track, fx_idx, "")
            if fx_name and param_mapping[fx_name] and param_mapping[fx_name].parameters and
               param_mapping[fx_name].parameters[param_id] then
                return param_mapping[fx_name].parameters[param_id].index
            end
        end

        -- Fallback: Try to find parameter by exact name match
        local param_count = reaper.TrackFX_GetNumParams(track, fx_idx)
        for i = 0, param_count - 1 do
            local _, param_name = reaper.TrackFX_GetParamName(track, fx_idx, i, "")
            -- Only use exact match
            if param_name == param_id then
                return i
            end
        end
    end
    return -1, "Parameter not found: " .. tostring(param_id)
end

-- Get all parameter information for an FX
function fx_manager.get_fx_params_info(track, fx_idx)
    if not track then
        error_handler.log_error("fx_manager.get_fx_params_info", "Track cannot be nil")
        return nil
    end

    local fx_count = reaper.TrackFX_GetCount(track)
    if fx_idx < 0 or fx_idx >= fx_count then
        error_handler.log_error("fx_manager.get_fx_params_info",
                              "FX index out of range",
                              "Index: " .. fx_idx .. ", Count: " .. fx_count)
        return nil
    end

    local fx_info = {}

    -- Get FX name
    local _, fx_name = reaper.TrackFX_GetFXName(track, fx_idx, "")
    fx_info.name = fx_name

    -- Get number of parameters
    local param_count = reaper.TrackFX_GetNumParams(track, fx_idx)
    fx_info.param_count = param_count

    -- Get parameter information
    fx_info.parameters = {}

    for param_idx = 0, param_count - 1 do
        local param_info = {}

        -- Get parameter name
        local _, param_name = reaper.TrackFX_GetParamName(track, fx_idx, param_idx, "")
        param_info.name = param_name

        -- Get parameter value and range
        local param_value, min_val, max_val = reaper.TrackFX_GetParam(track, fx_idx, param_idx)
        param_info.value = param_value
        param_info.min_value = min_val
        param_info.max_value = max_val

        -- Get extended parameter info if available
        local param_value_ex, min_val_ex, max_val_ex, mid_val = reaper.TrackFX_GetParamEx(track, fx_idx, param_idx)
        if mid_val then
            param_info.mid_value = mid_val
        end

        -- Get parameter formatted value
        local _, param_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_idx, param_idx, "")
        param_info.formatted_value = param_formatted

        -- Get parameter identifier if available
        local has_ident, param_ident = reaper.TrackFX_GetParamIdent(track, fx_idx, param_idx, "")
        if has_ident then
            param_info.identifier = param_ident
        end

        -- Get parameter normalized value (0.0 - 1.0)
        local param_norm = reaper.TrackFX_GetParamNormalized(track, fx_idx, param_idx)
        param_info.normalized_value = param_norm

        -- Add to parameters table
        fx_info.parameters[param_idx + 1] = param_info  -- +1 for 1-based Lua indexing
    end

    return fx_info
end

-- Function to discover all FX parameters in the project
function fx_manager.discover_fx_parameters()
    utils.print("=== FX Parameter Discovery ===")

    local discovery_data = {}
    discovery_data.project = {}
    discovery_data.project.name = reaper.GetProjectName(0, "")
    discovery_data.fx_data = {}

    -- Get all tracks in the project
    local track_count = reaper.CountTracks(0)
    utils.print("Found " .. track_count .. " tracks in project")

    for track_idx = 0, track_count - 1 do
        local track = reaper.GetTrack(0, track_idx)
        local _, track_name = reaper.GetTrackName(track)

        -- Get FX count for this track
        local fx_count = reaper.TrackFX_GetCount(track)
        utils.print("Track " .. track_idx .. " (" .. track_name .. ") has " .. fx_count .. " FX")

        -- Process each FX
        for fx_idx = 0, fx_count - 1 do
            local fx_info = fx_manager.get_fx_params_info(track, fx_idx)

            if fx_info then
                -- Store FX info with track reference
                fx_info.track_idx = track_idx
                fx_info.track_name = track_name

                -- Add to main data table with a unique key
                local fx_key = track_name .. "_" .. fx_info.name
                fx_key = fx_key:gsub(" ", "_"):gsub("%(", ""):gsub("%)", "")

                discovery_data.fx_data[fx_key] = fx_info

                utils.print("  Processed FX: " .. fx_info.name .. " with " .. fx_info.param_count .. " parameters")
            else
                error_handler.log_error("fx_manager.discover_fx_parameters",
                                      "Failed to get parameter info for FX",
                                      "Track: " .. track_name .. ", FX index: " .. fx_idx)
            end
        end
    end

    return discovery_data
end

-- Update a single FX parameter
function fx_manager.update_single_param(track_id, fx_id, param_id, value)
    -- Parameter validation
    if not track_id then
        error_handler.log_error("fx_manager.update_single_param", "Track ID cannot be nil")
        return false
    end

    if not fx_id then
        error_handler.log_error("fx_manager.update_single_param", "FX ID cannot be nil")
        return false
    end

    if not param_id then
        error_handler.log_error("fx_manager.update_single_param", "Parameter ID cannot be nil")
        return false
    end

    if value == nil then
        error_handler.log_error("fx_manager.update_single_param", "Parameter value cannot be nil")
        return false
    end

    local track, track_err = utils.get_track(track_id)
    if not track then
        error_handler.log_error("fx_manager.update_single_param", "Track not found", track_err)
        return false
    end

    local fx_idx, fx_err = utils.get_fx(track, fx_id)
    if fx_idx < 0 then
        error_handler.log_error("fx_manager.update_single_param", "FX not found", fx_err)
        return false
    end

    local param_idx, param_err = get_param(track, fx_idx, param_id)
    if param_idx < 0 then
        error_handler.log_error("fx_manager.update_single_param", "Parameter not found", param_err)
        return false
    end

    -- Convert value to number if it's a string
    local param_value = tonumber(value) or value

    -- Set the parameter value
    if type(param_value) == "number" then
        reaper.TrackFX_SetParam(track, fx_idx, param_idx, param_value)
        utils.print("Updated parameter: Track=" .. tostring(track_id) ..
              ", FX=" .. tostring(fx_id) ..
              ", Param=" .. tostring(param_id) ..
              ", Value=" .. tostring(param_value))
        return true
    else
        error_handler.log_error("fx_manager.update_single_param",
                              "Invalid parameter value",
                              "Value must be a number, got: " .. type(param_value))
        return false
    end
end

-- Get a single FX parameter value
function fx_manager.get_single_param(track_id, fx_id, param_id)
    -- Parameter validation
    if not track_id then
        error_handler.log_error("fx_manager.get_single_param", "Track ID cannot be nil")
        return nil
    end

    if not fx_id then
        error_handler.log_error("fx_manager.get_single_param", "FX ID cannot be nil")
        return nil
    end

    if not param_id then
        error_handler.log_error("fx_manager.get_single_param", "Parameter ID cannot be nil")
        return nil
    end

    local track, track_err = utils.get_track(track_id)
    if not track then
        error_handler.log_error("fx_manager.get_single_param", "Track not found", track_err)
        return nil
    end

    local fx_idx, fx_err = utils.get_fx(track, fx_id)
    if fx_idx < 0 then
        error_handler.log_error("fx_manager.get_single_param", "FX not found", fx_err)
        return nil
    end

    local param_idx, param_err = get_param(track, fx_idx, param_id)
    if param_idx < 0 then
        error_handler.log_error("fx_manager.get_single_param", "Parameter not found", param_err)
        return nil
    end

    local value = reaper.TrackFX_GetParam(track, fx_idx, param_idx)
    local _, formatted_value = reaper.TrackFX_GetFormattedParamValue(track, fx_idx, param_idx, "")

    return {
        numeric = value,
        formatted = formatted_value
    }
end

-- Process parameter changes from a table
function fx_manager.process_param_changes(param_changes)
    if not param_changes or type(param_changes) ~= "table" then
        error_handler.log_error("fx_manager.process_param_changes",
                              "Invalid param_changes parameter",
                              "Expected table, got: " .. type(param_changes))
        return 0, 0
    end

    local success_count = 0
    local total_count = #param_changes

    for i, change in ipairs(param_changes) do
        local success = fx_manager.update_single_param(
            change.track,
            change.fx,
            change.param,
            change.value
        )

        if success then
            success_count = success_count + 1
        end
    end

    utils.print("Processed " .. success_count .. " of " .. total_count .. " parameter changes")
    return success_count, total_count
end

-- Get multiple parameter values and return as a table
function fx_manager.get_param_values(param_requests)
    if not param_requests or type(param_requests) ~= "table" then
        error_handler.log_error("fx_manager.get_param_values",
                              "Invalid param_requests parameter",
                              "Expected table, got: " .. type(param_requests))
        return {}
    end

    local results = {}

    for i, request in ipairs(param_requests) do
        local param_value = fx_manager.get_single_param(
            request.track,
            request.fx,
            request.param
        )

        if param_value then
            table.insert(results, {
                track = request.track,
                fx = request.fx,
                param = request.param,
                value = param_value.numeric,
                formatted_value = param_value.formatted
            })
        end
    end

    return results
end

return fx_manager
