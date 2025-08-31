-- utils.lua - Common utility functions for ReaScripts
reaper = reaper

local utils = {}

-- Helper function for console output
function utils.print(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Get the path of the script's directory
function utils.get_script_path()
    return debug.getinfo(2, "S").source:match("@(.*/)")
end

-- Check if a file exists
function utils.file_exists(file_path)
    local f = io.open(file_path, "r")
    if f then
        f:close()
        return true
    end
    return false
end

-- Helper function to get track by ID or index
function utils.get_track(track_id)
    if track_id == nil then
        return nil, "Track ID cannot be nil"
    end

    -- Convert to number if possible
    local track_idx = tonumber(track_id)

    if track_idx ~= nil then
        -- If track_id can be converted to number, treat it as track index
        local track = reaper.GetTrack(0, track_idx)
        if not track then
            return nil, "Track index out of range: " .. track_idx
        end
        return track
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
    return nil, "Track not found: " .. tostring(track_id)
end

-- Helper function to get FX by ID or index
function utils.get_fx(track, fx_id)
    if track == nil then
        return -1, "Track cannot be nil"
    end

    if fx_id == nil then
        return -1, "FX ID cannot be nil"
    end

    -- Convert to number if possible
    local fx_idx = tonumber(fx_id)

    if fx_idx ~= nil then
        -- If fx_id can be converted to number, treat it as FX index
        local fx_count = reaper.TrackFX_GetCount(track)
        if fx_idx >= fx_count then
            return -1, "FX index out of range: " .. fx_idx
        end
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
    return -1, "FX not found: " .. tostring(fx_id)
end

-- Ensure a directory exists
function utils.ensure_dir(path)
    if not path then
        return false, "Directory path cannot be nil"
    end

    local success = reaper.RecursiveCreateDirectory(path, 0)
    if not success then
        return false, "Failed to create directory: " .. path
    end
    return true
end

-- Function to safely read a file
function utils.read_file(file_path)
    if not file_path then
        return nil, "File path cannot be nil"
    end

    local file = io.open(file_path, "r")
    if not file then
        return nil, "Could not open file: " .. file_path
    end

    local content = file:read("*all")
    file:close()

    return content
end

-- Function to safely write to a file
function utils.write_file(file_path, content)
    if not file_path then
        return false, "File path cannot be nil"
    end

    if content == nil then
        return false, "Content cannot be nil"
    end

    local file = io.open(file_path, "w")
    if not file then
        return false, "Could not open file for writing: " .. file_path
    end

    file:write(content)
    file:close()

    return true
end

return utils
