-- render_audio.lua - Render project audio and document output
reaper.ShowConsoleMsg("render_audio.lua starting...\n")

function print(val)
    reaper.ShowConsoleMsg(tostring(val) .. "\n")
end

function main()
    -- Get current project
    local project, project_path = reaper.EnumProjects(-1)
    if not project then
        reaper.ShowMessageBox("No project found", "Error", 0)
        return
    end
    print("Rendering project: " .. (project_path or "Untitled"))

        -- Read session config for filename
    local config_file = "/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/automation_config.txt"
    local session_id = "unknown"
    local octave_value = "0.0"
    local output_dir = "/Users/anthonybecker/Desktop"

    local file = io.open(config_file, "r")
    if file then
        for line in file:lines() do
            local key, value = line:match("^([^=]+)=(.*)$")
            if key == "session_id" then
                session_id = value
            elseif key == "parameter_value" then
                octave_value = value
            elseif key == "output_dir" then
                output_dir = value
            end
        end
        file:close()
    end

    -- Set up render settings with session info
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local output_filename = "rendered_audio_session" .. session_id .. "_octave" .. octave_value .. "_" .. timestamp .. ".wav"
    local full_output_path = output_dir .. "/" .. output_filename

    -- Documentation
    local doc_file = io.open(output_dir .. "/render_log_session" .. session_id .. "_" .. timestamp .. ".txt", "w")
    doc_file:write("Audio Render Log - Session " .. session_id .. "\n")
    doc_file:write("Timestamp: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
    doc_file:write("Project: " .. (project_path or "Untitled") .. "\n")
    doc_file:write("Octave Value: " .. octave_value .. "\n")
    doc_file:write("Output: " .. full_output_path .. "\n")
    doc_file:write(string.rep("=", 60) .. "\n\n")

    -- Get project timeline info
    local start_time, end_time = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)
    if end_time <= start_time then
        -- No time selection, use project length or default
        local project_length = 0
        local track_count = reaper.CountTracks(project)

        -- Find the longest item to determine project length
        for i = 0, track_count - 1 do
            local track = reaper.GetTrack(project, i)
            local item_count = reaper.CountTrackMediaItems(track)

            for j = 0, item_count - 1 do
                local item = reaper.GetTrackMediaItem(track, j)
                local item_pos = reaper.GetMediaItemInfo_Value(item, "D_POSITION")
                local item_len = reaper.GetMediaItemInfo_Value(item, "D_LENGTH")
                local item_end = item_pos + item_len

                if item_end > project_length then
                    project_length = item_end
                end
            end
        end

        -- Use project length or minimum 4 seconds
        end_time = math.max(project_length, 4.0)
        start_time = 0.0

        print(string.format("No time selection, using full project: %.2f - %.2f seconds", start_time, end_time))
    else
        print(string.format("Using time selection: %.2f - %.2f seconds", start_time, end_time))
    end

    doc_file:write(string.format("Render range: %.2f - %.2f seconds (%.2f sec duration)\n",
                                start_time, end_time, end_time - start_time))

    -- Set render bounds
    reaper.GetSet_LoopTimeRange(true, false, start_time, end_time, false)

    -- Configure render settings
    -- WAV format, 44.1kHz, 16-bit
    reaper.GetSetProjectInfo_String(project, "RENDER_FILE", full_output_path, true)
    reaper.GetSetProjectInfo_String(project, "RENDER_PATTERN", "", true)  -- Use project name
    reaper.GetSetProjectInfo(project, "RENDER_FMT", 0, true)      -- WAV format
    reaper.GetSetProjectInfo(project, "RENDER_1X", 1, true)       -- Full speed render
    reaper.GetSetProjectInfo(project, "RENDER_BOUNDSFLAG", 2, true)    -- Time selection
    reaper.GetSetProjectInfo(project, "RENDER_RESAMPLE", 3, true) -- Good quality
    reaper.GetSetProjectInfo(project, "RENDER_ADDTOPROJ", 0, true) -- Don't add to project
    reaper.GetSetProjectInfo(project, "RENDER_SETTINGS", 0, true)    -- Master mix
    reaper.GetSetProjectInfo(project, "RENDER_DITHER", 3, true)   -- TPDF dither

    doc_file:write("Render settings configured:\n")
    doc_file:write("  Format: WAV\n")
    doc_file:write("  Sample Rate: 44100 Hz\n")
    doc_file:write("  Bit Depth: 16-bit\n")
    doc_file:write("  Dither: TPDF\n")
    doc_file:write("  Source: Master mix\n\n")

    -- Start render
    print("Starting render...")
    doc_file:write("Render started at: " .. os.date("%H:%M:%S") .. "\n")

    local render_start_time = reaper.time_precise()

    -- Perform the render
    reaper.Main_OnCommand(42230, 0)  -- Render project to disk

    -- Wait for render to complete (check for file existence)
    local max_wait = 30  -- Maximum 30 seconds
    local wait_count = 0
    local render_success = false

    while wait_count < max_wait do
        reaper.defer(function() end)  -- Allow REAPER to process

        -- Check if output file exists and has size > 0
        local file = io.open(full_output_path, "rb")
        if file then
            local size = file:seek("end")
            file:close()
            if size > 1000 then  -- At least 1KB indicates successful render
                render_success = true
                break
            end
        end

        wait_count = wait_count + 1
        reaper.defer(function() end)
        -- Small delay
        local delay_start = reaper.time_precise()
        while reaper.time_precise() - delay_start < 1.0 do
            -- Wait 1 second
        end
    end

    local render_end_time = reaper.time_precise()
    local render_duration = render_end_time - render_start_time

    doc_file:write("Render completed at: " .. os.date("%H:%M:%S") .. "\n")
    doc_file:write(string.format("Render duration: %.2f seconds\n", render_duration))
    doc_file:write(string.format("Render success: %s\n", render_success and "YES" or "NO"))

    if render_success then
        -- Get file size
        local file = io.open(full_output_path, "rb")
        if file then
            local size = file:seek("end")
            file:close()
            doc_file:write(string.format("Output file size: %d bytes\n", size))
            print(string.format("Render successful! Output: %s (%d bytes)", output_filename, size))
        end
    else
        doc_file:write("ERROR: Render failed or timed out\n")
        print("ERROR: Render failed or timed out")
    end

    doc_file:write("\nRender operation completed.\n")
    doc_file:close()

    print("Render documentation saved to: render_log_session" .. session_id .. "_" .. timestamp .. ".txt")

    -- Update project
    reaper.UpdateArrange()
end

main()
