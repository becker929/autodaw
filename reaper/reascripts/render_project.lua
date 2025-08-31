-- Define reaper as a global to avoid linter warnings
reaper = reaper

local module = {}

-- Simple render function for REAPER projects
function module.render_project(render_dir, file_name_pattern)
    render_dir = render_dir or reaper.GetProjectPath("") .. "/renders"
    file_name_pattern = file_name_pattern or "$project"
    if not reaper.file_exists(render_dir) then
        reaper.RecursiveCreateDirectory(render_dir, 0)
        reaper.ShowConsoleMsg("Created render directory: " .. render_dir .. "\n")
    end

    local proj = 0
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local output_filename = render_dir .. "/" .. file_name_pattern .. "_" .. timestamp .. ".wav"
    local proj_len = reaper.GetProjectLength(proj)
    
    reaper.ShowConsoleMsg("Setting up render with output to: " .. output_filename .. "\n")
    reaper.Main_OnCommand(40296, 0) -- Select all
    reaper.GetSet_LoopTimeRange(true, false, 0, proj_len, false)
    reaper.GetSetProjectInfo_String(proj, "RENDER_FILE", render_dir, true)
    reaper.GetSetProjectInfo_String(proj, "RENDER_PATTERN", file_name_pattern .. "_" .. timestamp, true)
    reaper.GetSetProjectInfo(proj, "RENDER_BOUNDSFLAG", 2, true)  -- Time selection
    reaper.GetSetProjectInfo(proj, "RENDER_SETTINGS", 0, true)    -- Master mix
    reaper.GetSetProjectInfo(proj, "RENDER_FMT", 0, true)      -- WAV format
    reaper.GetSetProjectInfo(proj, "RENDER_RESAMPLE", 3, true) -- Good quality
    reaper.GetSetProjectInfo(proj, "RENDER_DITHER", 3, true)   -- TPDF dither
    reaper.GetSetProjectInfo(proj, "RENDER_ADDTOPROJ", 0, true) -- Don't add to project
    reaper.ShowConsoleMsg("Starting render process using command ID 42230...\n")
    reaper.Main_OnCommand(42230, 0)  -- Render project, non-realtime
    reaper.ShowConsoleMsg("Waiting for render to complete...\n")

    local max_wait = 10  -- Wait up to 10 seconds
    local wait_time = 0
    local success = false

    local function get_file_size(file_path)
        local file = io.open(file_path, "rb")
        if not file then return 0 end
        local size = file:seek("end")
        file:close()
        return size
    end

    while wait_time < max_wait do
        if reaper.file_exists(output_filename) then
            local size = get_file_size(output_filename)
            if size > 1000 then  -- At least 1KB indicates successful render
                success = true
                break
            end
        end

        -- Wait a bit before checking again
        reaper.defer(function() end)  -- Small delay
        wait_time = wait_time + 0.5
        reaper.Sleep(500)  -- 500ms delay
    end

    if success then
        reaper.ShowConsoleMsg("Render completed successfully: " .. output_filename .. "\n")
    else
        reaper.ShowConsoleMsg("Render may have failed or is still in progress.\n")
    end

    return success
end

-- Run the function if script is executed directly
if not ... then
    reaper.ShowConsoleMsg("=== Rendering Project Directly ===\n")
    local render_dir = reaper.GetProjectPath("") .. "/renders"
    local success = module.render_project(render_dir, "test_render")
    if success then
        reaper.ShowConsoleMsg("=== Render Completed Successfully ===\n")
    else
        reaper.ShowConsoleMsg("=== Render May Have Failed ===\n")
    end
end

return module.render_project
