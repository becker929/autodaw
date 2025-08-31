-- parameter_discovery.lua
-- Script to discover and save FX parameter information to a JSON file
-- Captures parameter names, values, formatted values, and value ranges (min/max/mid)

-- Define reaper as a global to avoid linter warnings
reaper = reaper

-- Helper function for console output
function print(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Function to convert Lua table to JSON string
function table_to_json(tbl, level)
    level = level or 0
    local indent = string.rep("  ", level)
    local json_str = "{"

    local pairs_list = {}
    for k, v in pairs(tbl) do
        table.insert(pairs_list, k)
    end
    table.sort(pairs_list)

    local first = true
    for _, k in ipairs(pairs_list) do
        local v = tbl[k]
        if not first then
            json_str = json_str .. ","
        end
        first = false

        json_str = json_str .. "\n" .. indent .. "  "

        -- Key formatting
        if type(k) == "number" then
            json_str = json_str .. "\"" .. tostring(k) .. "\""
        else
            json_str = json_str .. "\"" .. tostring(k) .. "\""
        end

        json_str = json_str .. ": "

        -- Value formatting
        if type(v) == "table" then
            json_str = json_str .. table_to_json(v, level + 1)
        elseif type(v) == "string" then
            json_str = json_str .. "\"" .. v:gsub("\\", "\\\\"):gsub("\"", "\\\""):gsub("\n", "\\n") .. "\""
        elseif type(v) == "number" or type(v) == "boolean" then
            json_str = json_str .. tostring(v)
        else
            json_str = json_str .. "\"" .. tostring(v) .. "\""
        end
    end

    if first then
        json_str = json_str .. "}"
    else
        json_str = json_str .. "\n" .. indent .. "}"
    end

    return json_str
end

-- Function to get all parameter information for an FX
function get_fx_params_info(track, fx_idx)
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
function discover_fx_parameters()
    print("=== FX Parameter Discovery ===")

    local discovery_data = {}
    discovery_data.project = {}
    discovery_data.project.name = reaper.GetProjectName(0, "")
    discovery_data.fx_data = {}

    -- Get all tracks in the project
    local track_count = reaper.CountTracks(0)
    print("Found " .. track_count .. " tracks in project")

    for track_idx = 0, track_count - 1 do
        local track = reaper.GetTrack(0, track_idx)
        local _, track_name = reaper.GetTrackName(track)

        -- Get FX count for this track
        local fx_count = reaper.TrackFX_GetCount(track)
        print("Track " .. track_idx .. " (" .. track_name .. ") has " .. fx_count .. " FX")

        -- Process each FX
        for fx_idx = 0, fx_count - 1 do
            local fx_info = get_fx_params_info(track, fx_idx)

            -- Store FX info with track reference
            fx_info.track_idx = track_idx
            fx_info.track_name = track_name

            -- Add to main data table with a unique key
            local fx_key = track_name .. "_" .. fx_info.name
            fx_key = fx_key:gsub(" ", "_"):gsub("%(", ""):gsub("%)", "")

            discovery_data.fx_data[fx_key] = fx_info

            print("  Processed FX: " .. fx_info.name .. " with " .. fx_info.param_count .. " parameters (including value ranges)")
        end
    end

    return discovery_data
end

-- Function to save data to a file
function save_to_file(data, file_path)
    local file = io.open(file_path, "w")
    if not file then
        print("Error: Could not open file for writing: " .. file_path)
        return false
    end

    local json_str = table_to_json(data)
    file:write(json_str)
    file:close()

    print("Data saved to: " .. file_path)
    return true
end

-- Main function
function main()
    print("Starting FX parameter discovery...")

    -- Create discovery data
    local discovery_data = discover_fx_parameters()

    -- Save to file - use fixed path relative to script
    local script_path = debug.getinfo(1, "S").source:match("@(.*/)") or ""
    local output_file = script_path .. "../fx_parameters.json"

    local success = save_to_file(discovery_data, output_file)

    if success then
        print("Parameter discovery completed successfully!")
    else
        print("Parameter discovery failed to save data.")
    end

    print("=== FX Parameter Discovery Complete ===")
end

-- Run the main function
main()
