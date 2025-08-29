-- parameter_discovery.lua - Discover VST parameter ranges and capabilities
reaper.ShowConsoleMsg("parameter_discovery.lua starting...\n")

function print(val)
    reaper.ShowConsoleMsg(tostring(val) .. "\n")
end

function update_beacon(status, message, data)
    local beacon_path = "/Users/anthonybecker/Desktop/reaper_automation_beacon.txt"
    local file = io.open(beacon_path, "w")
    if file then
        file:write("timestamp=" .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
        file:write("status=" .. status .. "\n")
        file:write("script=parameter_discovery.lua\n")
        file:write("message=" .. (message or "") .. "\n")
        if data then
            file:write("data=" .. data .. "\n")
        end
        file:close()
    end
end

function discover_parameter_ranges(track, fx_index)
    local param_count = reaper.TrackFX_GetNumParams(track, fx_index)
    local ranges = {}

    print("Discovering " .. param_count .. " parameters...")

    for i = 0, param_count - 1 do
        local retval, param_name = reaper.TrackFX_GetParamName(track, fx_index, i, "")
        if retval then
            -- Get current value
            local current_value = reaper.TrackFX_GetParam(track, fx_index, i)
            local retval_current, current_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, i, "")

            -- Test parameter bounds by setting extreme values
            reaper.TrackFX_SetParam(track, fx_index, i, 0.0)
            local retval_min, min_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, i, "")

            reaper.TrackFX_SetParam(track, fx_index, i, 1.0)
            local retval_max, max_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, i, "")

            -- Restore original value
            reaper.TrackFX_SetParam(track, fx_index, i, current_value)

            -- Store parameter info
            ranges[i] = {
                index = i,
                name = param_name,
                current_value = current_value,
                current_formatted = current_formatted or "N/A",
                min_normalized = 0.0,
                max_normalized = 1.0,
                min_formatted = min_formatted or "N/A",
                max_formatted = max_formatted or "N/A"
            }

            print("Parameter " .. i .. ": " .. param_name .. " = " .. current_value .. " (" .. (current_formatted or "N/A") .. ")")
            print("  Range: " .. (min_formatted or "N/A") .. " to " .. (max_formatted or "N/A"))
        end
    end

    return ranges
end

function save_parameter_discovery(ranges, session_id, output_dir)
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local filename = output_dir .. "/parameter_discovery_session" .. session_id .. "_" .. timestamp .. ".json"

    local file = io.open(filename, "w")
    if file then
        file:write("{\n")
        file:write('  "discovery_timestamp": "' .. os.date("%Y-%m-%d %H:%M:%S") .. '",\n')
        file:write('  "session_id": "' .. session_id .. '",\n')
        file:write('  "parameter_count": ' .. #ranges .. ',\n')
        file:write('  "parameters": {\n')

        local param_entries = {}
        for i, param in pairs(ranges) do
            local entry = string.format(
                '    "%d": {\n' ..
                '      "index": %d,\n' ..
                '      "name": "%s",\n' ..
                '      "current_value": %.6f,\n' ..
                '      "current_formatted": "%s",\n' ..
                '      "min_normalized": %.6f,\n' ..
                '      "max_normalized": %.6f,\n' ..
                '      "min_formatted": "%s",\n' ..
                '      "max_formatted": "%s"\n' ..
                '    }',
                i, param.index, param.name, param.current_value, param.current_formatted,
                param.min_normalized, param.max_normalized, param.min_formatted, param.max_formatted
            )
            table.insert(param_entries, entry)
        end

        file:write(table.concat(param_entries, ",\n"))
        file:write('\n  }\n}')
        file:close()

        print("Parameter discovery saved to: " .. filename)
        return filename
    else
        print("ERROR: Could not save parameter discovery")
        return nil
    end
end

function read_config()
    local config_file = "/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/automation_config.txt"
    local file = io.open(config_file, "r")
    if not file then
        print("ERROR: Config file not found")
        return nil
    end

    local config_data = {}
    for line in file:lines() do
        local key, value = line:match("^([^=]+)=(.*)$")
        if key and value then
            config_data[key] = value
        end
    end
    file:close()

    return config_data
end

function main()
    update_beacon("STARTED", "Parameter discovery starting")

    local config_data = read_config()
    if not config_data then
        update_beacon("ERROR", "Could not read configuration")
        return
    end

    local session_id = config_data.session_id or "unknown"
    local output_dir = config_data.output_dir or "/Users/anthonybecker/Desktop"

    local track = reaper.GetTrack(0, 0)
    if not track then
        update_beacon("ERROR", "No tracks found in project")
        return
    end

    local fx_count = reaper.TrackFX_GetCount(track)
    if fx_count == 0 then
        update_beacon("ERROR", "No FX found on the first track")
        return
    end

    local fx_index = 0
    local retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "")
    if not retval then
        update_beacon("ERROR", "Could not get FX name")
        return
    end

    print("Discovering parameters for FX: " .. fx_name)
    update_beacon("RUNNING", "Discovering parameters for " .. fx_name)

    -- Discover parameter ranges
    local ranges = discover_parameter_ranges(track, fx_index)

    -- Save discovery results
    local saved_file = save_parameter_discovery(ranges, session_id, output_dir)

    if saved_file then
        update_beacon("COMPLETED", "Parameter discovery completed, saved to " .. saved_file)
    else
        update_beacon("ERROR", "Parameter discovery completed but could not save results")
    end

    -- Update project
    reaper.UpdateArrange()
end

main()
