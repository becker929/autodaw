reaper.ShowConsoleMsg("that worked")

function print(val)
  reaper.ShowConsoleMsg("\n")
  reaper.ShowConsoleMsg(tostring(val))
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

    local param_count = reaper.TrackFX_GetNumParams(track, fx_index)
    local output = "FX: " .. fx_name .. "\n"
    output = output .. "Number of parameters: " .. param_count .. "\n\n"
    output = output .. "Parameters:\n"
    output = output .. string.rep("-", 50) .. "\n"
    for i = 0, param_count - 1 do
        local retval_name, param_name = reaper.TrackFX_GetParamName(track, fx_index, i, "")
        local param_value = reaper.TrackFX_GetParam(track, fx_index, i)
        local retval_formatted, param_formatted = reaper.TrackFX_GetFormattedParamValue(track, fx_index, i, "")
        if retval_name then
            output = output .. "'" .. tostring(param_name) .. "'," .. tostring(param_value) .. "\n"
        end
    end

    -- Read session config for output directory
    local config_file = "automation_config.txt"
    local session_id = "unknown"
    local output_dir = "outputs"

    local config = io.open(config_file, "r")
    if config then
        for line in config:lines() do
            local key, value = line:match("^([^=]+)=(.*)$")
            if key == "session_id" then
                session_id = value
            elseif key == "output_dir" then
                output_dir = value
            end
        end
        config:close()
    end

    -- save to file
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local file = io.open(output_dir .. "/params_session" .. session_id .. "_" .. timestamp .. ".txt", "w")
    file:write(output)
    file:close()
end

main()
