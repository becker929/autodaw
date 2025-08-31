#!/usr/bin/env lua

-- test_clean.lua - Clean test runner that clears module cache and sets up fresh mocks

-- Clear any cached modules to ensure fresh loading
for k,v in pairs(package.loaded) do
    if k:match("^lib%.") or k:match("^tests%.") or k:match("^reascripts%.") then
        package.loaded[k] = nil
    end
end

-- Set up comprehensive reaper mocks before any modules are loaded
reaper = {
    ShowConsoleMsg = function(msg) print(msg:gsub("\n$", "")) end,
    GetProjectPath = function() return "/test/project" end,
    CountTracks = function() return 1 end,
    InsertTrackAtIndex = function() end,
    GetTrack = function(proj, idx)
        if idx == 0 then
            return {track_id = idx}
        end
        return nil
    end,
    GetTrackName = function(track) return true, "Test Track" end,
    TrackFX_AddByName = function() return 0 end,
    TrackFX_SetParam = function() end,
    TrackFX_GetCount = function() return 1 end,
    TrackFX_GetNumParams = function() return 2 end,
    TrackFX_GetFXName = function() return true, "TestFX" end,
    TrackFX_GetParamName = function() return true, "TestParam" end,
    TrackFX_GetParam = function() return 0.5, 0.0, 1.0 end,
    TrackFX_GetParamEx = function() return 0.5, 0.0, 1.0, 0.5 end,
    TrackFX_GetFormattedParamValue = function() return true, "50%" end,
    TrackFX_GetParamIdent = function() return true, "test_param" end,
    TrackFX_GetParamNormalized = function() return 0.5 end,
    InsertMedia = function() return {media_item = true} end,
    GetSetProjectInfo = function() end,
    GetSetProjectInfo_String = function() end,
    GetSetMediaTrackInfo_String = function() end,
    Main_OnCommand = function() end,
    SelectAllMediaItems = function() end,
    DeleteTrack = function() end,
    GetProjectName = function() return "Test Project" end,
    RecursiveCreateDirectory = function() return true end
}

-- Add the current script's directory to the package path to find modules
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

-- Now run the tests
require("tests.run_tests")
