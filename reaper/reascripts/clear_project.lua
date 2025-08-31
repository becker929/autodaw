-- Define reaper as a global to avoid linter warnings
reaper = reaper

local module = {}

-- Helper function for console output
local function print(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Clear all tracks in the current project
function module.clear_project()
    print("Clearing project")
    local track_count = reaper.CountTracks(0)
    for i = track_count - 1, 0, -1 do
        local track = reaper.GetTrack(0, i)
        if track then
            reaper.DeleteTrack(track)
        end
    end
    return true
end

-- Run the function if script is executed directly
if not ... then
    print("=== Clearing project directly ===")
    module.clear_project()
    print("=== Project cleared ===")
end

return module.clear_project
