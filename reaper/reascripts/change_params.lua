-- change_params.lua - Change VST parameters based on config
reaper.ShowConsoleMsg("change_params.lua starting...\n")

function print(val)
    reaper.ShowConsoleMsg(tostring(val) .. "\n")
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
    local config_data = read_config()
    if not config_data then
        return
    end

    local target_value = tonumber(config_data.parameter_value) or 0.0
    local session_id = config_data.session_id or "unknown"
    local output_dir = config_data.output_dir or "/Users/anthonybecker/Desktop"

    local track = reaper.GetTrack(0, 0)
    if not track then
        reaper.ShowMessageBox("No tracks found in project", "Error", 0)
        return
    end

    local fx_count = reaper.TrackFX_GetCount(track)
    if fx_count == 0 then
        reaper.ShowMessageBox("No FX found on the first track", "Error", 0)
        return
    end

    local fx_index = 0
    local retval, fx_name = reaper.TrackFX_GetFXName(track, fx_index, "")
    if not retval then
        reaper.ShowMessageBox("Could not get FX name", "Error", 0)
        return
    end

    print("Changing target parameter for FX: " .. fx_name)
    print("Target parameter value: " .. target_value)

    -- Documentation file
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local doc_file = io.open(output_dir .. "/param_change_session" .. session_id .. "_" .. timestamp .. ".txt", "w")
    doc_file:write("Parameter Change Log - Session " .. session_id .. "\n")
    doc_file:write("Timestamp: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
    doc_file:write("FX: " .. fx_name .. "\n")
    doc_file:write("Target parameter value: " .. target_value .. "\n")
    doc_file:write(string.rep("=", 60) .. "\n\n")

    -- Find octave parameter (common names: "Oct", "Octave", "OCTAVE")
    local param_count = reaper.TrackFX_GetNumParams(track, fx_index)
    local octave_param_index = -1

    for i = 0, param_count - 1 do
        local retval_name, param_name = reaper.TrackFX_GetParamName(track, fx_index, i, "")
        if retval_name then
            local param_lower = string.lower(param_name)
            if string.find(param_lower, "oct") then
                octave_param_index = i
                print("Found octave parameter at index " .. i .. ": " .. param_name)
                doc_file:write("Found octave parameter: " .. param_name .. " (index " .. i .. ")\n")
                break
            end
        end
    end

    if octave_param_index == -1 then
        print("ERROR: No octave parameter found")
        doc_file:write("ERROR: No octave parameter found\n")
        doc_file:close()
        return
    end

    -- Get original value
    local original_value = reaper.TrackFX_GetParam(track, fx_index, octave_param_index)
    local retval_orig_formatted, orig_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, octave_param_index, "")

    -- Set new value (convert target_value to 0-1 range if needed)
    -- Assuming octave range is typically -4 to +4, so we normalize
    local normalized_value = (target_value + 4.0) / 8.0  -- Convert -4 to +4 range to 0-1
    normalized_value = math.max(0.0, math.min(1.0, normalized_value))  -- Clamp to 0-1

    reaper.TrackFX_SetParam(track, fx_index, octave_param_index, normalized_value)

    -- Verify the change
    local current_value = reaper.TrackFX_GetParam(track, fx_index, octave_param_index)
    local retval_new_formatted, new_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, octave_param_index, "")
    local change_success = math.abs(current_value - normalized_value) < 0.001

    -- Log the change
    doc_file:write(string.format(
        "Original value: %.6f (%s)\n" ..
        "Target octave: %.2f\n" ..
        "Normalized value: %.6f\n" ..
        "Current value: %.6f (%s)\n" ..
        "Change success: %s\n",
        original_value, orig_formatted or "N/A",
        target_value,
        normalized_value,
        current_value, new_formatted or "N/A",
        change_success and "YES" or "NO"
    ))

    doc_file:write("\nOctave parameter change completed.\n")
    doc_file:close()

    print("Octave changed from " .. original_value .. " to " .. current_value)
    print("Documentation saved to: octave_change_session" .. session_id .. "_" .. timestamp .. ".txt")

    -- Update project to reflect changes
    reaper.UpdateArrange()
end

main()
