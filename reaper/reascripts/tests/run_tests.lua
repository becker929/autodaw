-- run_tests.lua - Main test runner script

-- Set up comprehensive reaper mocks for all tests
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
    TrackFX_GetCount = function() return 0 end,
    InsertMedia = function() return {media_item = true} end,
    GetSetProjectInfo = function() end,
    GetSetProjectInfo_String = function() end,
    GetSetMediaTrackInfo_String = function() end,
    Main_OnCommand = function() end,
    SelectAllMediaItems = function() end,
    DeleteTrack = function() end,
    GetProjectName = function() return "Test Project" end
}

-- Add the parent directory to the path
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "../?.lua;" .. package.path

-- Import test runner and test modules
local test_runner = require("tests.test_runner")
local test_utils = require("tests.test_utils")
local test_json = require("tests.test_json")
local test_error_handler = require("tests.test_error_handler")
local test_fx_manager = require("tests.test_fx_manager")
local test_constants = require("tests.test_constants")
local test_session_manager = require("tests.test_session_manager")

-- Override print function for testing
test_runner.print = print

-- Main function
function main()
    test_runner.print("🧪 Starting ReaScripts Test Suite")
    test_runner.print("=" .. string.rep("=", 49))

    -- Reset stats before running tests
    test_runner.reset_stats()

    -- Run all test modules
    local test_modules = {
        test_utils,
        test_json,
        test_error_handler,
        test_fx_manager,
        test_constants,
        test_session_manager
    }

    test_runner.run_all_tests(test_modules)

    -- Return exit code based on test results
    if test_runner.stats and test_runner.stats.failed > 0 then
        return 1  -- Exit with error code if tests failed
    else
        return 0  -- Success
    end
end

-- Run tests
local exit_code = main()

-- If we're not in REAPER, we can exit with the code
if not reaper and os and os.exit then
    os.exit(exit_code)
end
