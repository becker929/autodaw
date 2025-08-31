-- Define reaper as a global to avoid linter warnings
reaper = reaper

local module = {}

-- Parameter mapping data
local param_mapping = {}
local param_mapping_loaded = false

-- Helper function for console output
local function print(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Helper function to get track by ID or index
local function get_track(track_id)
    -- Convert to number if possible
    local track_idx = tonumber(track_id)

    if track_idx ~= nil then
        -- If track_id can be converted to number, treat it as track index
        return reaper.GetTrack(0, track_idx)
    else
        -- Try to find track by name
        local track_count = reaper.CountTracks(0)
        for i = 0, track_count - 1 do
            local track = reaper.GetTrack(0, i)
            local _, track_name = reaper.GetTrackName(track)
            if track_name == track_id then
                return track
            end
        end
    end
    return nil
end

-- Helper function to get FX by ID or index
local function get_fx(track, fx_id)
    -- Convert to number if possible
    local fx_idx = tonumber(fx_id)

    if fx_idx ~= nil then
        -- If fx_id can be converted to number, treat it as FX index
        return fx_idx
    else
        -- Try to find FX by name
        local fx_count = reaper.TrackFX_GetCount(track)
        for i = 0, fx_count - 1 do
            local _, fx_name = reaper.TrackFX_GetFXName(track, i, "")
            if fx_name:find(fx_id) then
                return i
            end
        end
    end
    return -1
end

-- Function to load parameter mapping from a JSON file
function module.load_param_mapping(file_path)
    -- Use fixed path if none provided
    if not file_path then
        local script_path = debug.getinfo(1, "S").source:match("@(.*/)") or ""
        file_path = script_path .. "../fx_parameters.json"
    end

    if not reaper.file_exists(file_path) then
        print("Error: Parameter mapping file not found at: " .. file_path)
        print("Run parameter_discovery.lua script first to generate the mapping.")
        return false
    end

    print("Loading parameter mapping from: " .. file_path)

    -- Read the file
    local file = io.open(file_path, "r")
    if not file then
        print("Error: Could not open parameter mapping file.")
        return false
    end

    local json_str = file:read("*all")
    file:close()

    -- Parse the JSON
    local success, data = pcall(function()
        -- Very simple JSON parser for our known structure
        local fx_data = {}

        -- Extract FX data section
        local fx_data_str = json_str:match('"fx_data":%s*({.+})')
        if not fx_data_str then
            print("Error: Could not find fx_data in JSON.")
            return nil
        end

        -- Extract each FX block
        for fx_key, fx_block in fx_data_str:gmatch('"([^"]+)":%s*({[^}]+})') do
            local fx_info = {}

            -- Extract FX name
            fx_info.name = fx_block:match('"name":%s*"([^"]+)"')

            -- Extract track info
            fx_info.track_name = fx_block:match('"track_name":%s*"([^"]+)"')
            fx_info.track_idx = tonumber(fx_block:match('"track_idx":%s*([%d%.]+)'))

            -- Extract parameters
            fx_info.parameters = {}

            -- Find parameters section
            local params_section = fx_block:match('"parameters":%s*({[^}]+})')
            if params_section then
                -- Extract each parameter
                for param_idx, param_block in params_section:gmatch('"(%d+)":%s*({[^}]+})') do
                    local param_info = {}
                    param_info.index = tonumber(param_idx) - 1  -- Convert back to 0-based
                    param_info.name = param_block:match('"name":%s*"([^"]+)"')

                    if param_info.name then
                        -- Store by name for quick lookup
                        fx_info.parameters[param_info.name] = param_info
                    end
                end
            end

            fx_data[fx_key] = fx_info

            -- Also store by FX name for easier lookup
            if fx_info.name then
                fx_data[fx_info.name] = fx_info
            end
        end

        return fx_data
    end)

    if not success or not data then
        print("Error parsing parameter mapping: " .. (data or "unknown error"))
        return false
    end

    -- Store the mapping
    param_mapping = data
    param_mapping_loaded = true

    print("Parameter mapping loaded successfully.")
    return true
end

-- Helper function to get parameter by ID or index
local function get_param(track, fx_idx, param_id)
    -- Convert to number if possible
    local param_idx = tonumber(param_id)

    if param_idx ~= nil then
        -- If param_id can be converted to number, treat it as parameter index
        return param_idx
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
    return -1
end

-- Update a single FX parameter
function module.update_single_param(track_id, fx_id, param_id, value)
    local track = get_track(track_id)
    if not track then
        print("Error: Track not found: " .. tostring(track_id))
        return false
    end

    local fx_idx = get_fx(track, fx_id)
    if fx_idx < 0 then
        print("Error: FX not found: " .. tostring(fx_id))
        return false
    end

    local param_idx = get_param(track, fx_idx, param_id)
    if param_idx < 0 then
        print("Error: Parameter not found: " .. tostring(param_id))
        return false
    end

    -- Convert value to number if it's a string
    local param_value = tonumber(value) or value

    -- Set the parameter value
    if type(param_value) == "number" then
        reaper.TrackFX_SetParam(track, fx_idx, param_idx, param_value)
        print("Updated parameter: Track=" .. tostring(track_id) ..
              ", FX=" .. tostring(fx_id) ..
              ", Param=" .. tostring(param_id) ..
              ", Value=" .. tostring(param_value))
        return true
    else
        print("Error: Invalid parameter value: " .. tostring(value))
        return false
    end
end

-- Get a single FX parameter value
function module.get_single_param(track_id, fx_id, param_id)
    local track = get_track(track_id)
    if not track then
        print("Error: Track not found: " .. tostring(track_id))
        return nil
    end

    local fx_idx = get_fx(track, fx_id)
    if fx_idx < 0 then
        print("Error: FX not found: " .. tostring(fx_id))
        return nil
    end

    local param_idx = get_param(track, fx_idx, param_id)
    if param_idx < 0 then
        print("Error: Parameter not found: " .. tostring(param_id))
        return nil
    end

    local value = reaper.TrackFX_GetParam(track, fx_idx, param_idx)
    local _, formatted_value = reaper.TrackFX_GetFormattedParamValue(track, fx_idx, param_idx, "")

    return {
        numeric = value,
        formatted = formatted_value
    }
end

-- Process parameter changes from a JSON-like table
function module.process_param_changes(param_changes)
    local success_count = 0
    local total_count = #param_changes

    for i, change in ipairs(param_changes) do
        local success = module.update_single_param(
            change.track,
            change.fx,
            change.param,
            change.value
        )

        if success then
            success_count = success_count + 1
        end
    end

    print("Processed " .. success_count .. " of " .. total_count .. " parameter changes")
    return success_count, total_count
end

-- Get multiple parameter values and return as a table
function module.get_param_values(param_requests)
    local results = {}

    for i, request in ipairs(param_requests) do
        local param_value = module.get_single_param(
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

return module
