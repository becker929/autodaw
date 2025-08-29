-- change_params.lua - Change VST parameters and document the changes
reaper.ShowConsoleMsg("change_params.lua starting...\n")

function print(val)
    reaper.ShowConsoleMsg(tostring(val) .. "\n")
end

function update_beacon(status, message)
    local beacon_path = "/Users/anthonybecker/Desktop/reaper_automation_beacon.txt"
    local file = io.open(beacon_path, "w")
    if file then
        file:write("timestamp=" .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
        file:write("status=" .. status .. "\n")
        file:write("script=change_params.lua\n")
        file:write("message=" .. (message or "") .. "\n")
        file:close()
    end
end

function main()
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

    print("Changing parameters for FX: " .. fx_name)

    -- Get parameter count
    local param_count = reaper.TrackFX_GetNumParams(track, fx_index)

    -- Documentation file
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local doc_file = io.open("/Users/anthonybecker/Desktop/param_changes_" .. timestamp .. ".txt", "w")
    doc_file:write("Parameter Changes Log - " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
    doc_file:write("FX: " .. fx_name .. "\n")
    doc_file:write("Total parameters: " .. param_count .. "\n")
    doc_file:write(string.rep("=", 60) .. "\n\n")

    -- Change some parameters (first 5 or all if less than 5)
    local params_to_change = math.min(5, param_count)

    for i = 0, params_to_change - 1 do
        local retval_name, param_name = reaper.TrackFX_GetParamName(track, fx_index, i, "")
        if retval_name then
            -- Get original value
            local original_value = reaper.TrackFX_GetParam(track, fx_index, i)
            local retval_orig_formatted, orig_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, i, "")

            -- Set new value (cycle through 0.2, 0.5, 0.8 based on parameter index)
            local new_values = {0.2, 0.5, 0.8}
            local new_value = new_values[(i % 3) + 1]

            -- Set the parameter
            reaper.TrackFX_SetParam(track, fx_index, i, new_value)

            -- Get the new formatted value
            local retval_new_formatted, new_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, i, "")

            -- Verify the change
            local current_value = reaper.TrackFX_GetParam(track, fx_index, i)
            local change_success = math.abs(current_value - new_value) < 0.001

            -- Log the change
            local log_entry = string.format(
                "Parameter %d: '%s'\n" ..
                "  Original: %.6f (%s)\n" ..
                "  New:      %.6f (%s)\n" ..
                "  Current:  %.6f\n" ..
                "  Success:  %s\n\n",
                i, param_name,
                original_value, orig_formatted or "N/A",
                new_value, new_formatted or "N/A",
                current_value,
                change_success and "YES" or "NO"
            )

            doc_file:write(log_entry)
            print("Changed param " .. i .. ": " .. param_name .. " from " .. original_value .. " to " .. current_value)
        end
    end

    doc_file:write("\nParameter change operation completed.\n")
    doc_file:close()

        print("Parameter changes documented in: param_changes_" .. timestamp .. ".txt")

    -- Update project to reflect changes
    reaper.UpdateArrange()

    -- Signal completion
    update_beacon("COMPLETED", string.format("Changed %d parameters successfully", params_to_change))
end

main()
