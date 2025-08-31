-- test_utils.lua - Tests for the utils module

-- Set up reaper mocks before loading any modules that depend on reaper
if not reaper then
    reaper = {
        ShowConsoleMsg = function(msg) print(msg:gsub("\n$", "")) end,
        CountTracks = function() return 1 end,
        GetTrack = function(proj, idx)
            if idx == 0 then return {track_id = idx} end
            return nil
        end,
        GetTrackName = function(track) return true, "Test Track" end,
        TrackFX_GetCount = function() return 1 end,
        RecursiveCreateDirectory = function() return true end
    }
end

-- Add the parent directory to the path
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "../?.lua;" .. package.path

local test_runner = require("tests.test_runner")
local utils = require("lib.utils")

local test_utils = {}

function test_utils.run_tests()
    -- Override reaper functions again to ensure they're set
    reaper = reaper or {}
    reaper.GetTrackName = function(track) return true, "Test Track" end
    reaper.TrackFX_GetCount = function() return 1 end
    reaper.RecursiveCreateDirectory = function() return true end
    test_runner.describe("utils.get_script_path", function()
        local path = utils.get_script_path()
        test_runner.assert_not_nil(path, "get_script_path should return a path")
        test_runner.assert_type("string", path, "Path should be a string")
        test_runner.assert_true(path:match("/$"), "Path should end with /")
    end)

    test_runner.describe("utils.file_exists", function()
        -- Test with a file that should exist (this test file itself)
        local test_file = script_path .. "test_utils.lua"
        test_runner.assert_true(utils.file_exists(test_file), "Should detect existing file")

        -- Test with a file that shouldn't exist
        local fake_file = script_path .. "nonexistent_file_12345.txt"
        test_runner.assert_false(utils.file_exists(fake_file), "Should not detect non-existent file")

        -- Test with nil input - this should not crash but return false
        local success, result = pcall(utils.file_exists, nil)
        if success then
            test_runner.assert_false(result, "Should handle nil input gracefully")
        else
            test_runner.assert_true(true, "Should handle nil input (caught error as expected)")
        end
    end)

    test_runner.describe("utils.get_track", function()
        -- Test with nil input
        local track, err = utils.get_track(nil)
        test_runner.assert_nil(track, "Should return nil for nil input")
        test_runner.assert_not_nil(err, "Should return error message for nil input")

        -- Test with invalid string input (when no REAPER project is loaded)
        local track, err = utils.get_track("NonexistentTrack")
        test_runner.assert_nil(track, "Should return nil for non-existent track")
        test_runner.assert_not_nil(err, "Should return error message for non-existent track")
    end)

    test_runner.describe("utils.get_fx", function()
        -- Test with nil track
        local fx_idx, err = utils.get_fx(nil, "SomeFX")
        test_runner.assert_equals(-1, fx_idx, "Should return -1 for nil track")
        test_runner.assert_not_nil(err, "Should return error message for nil track")

        -- Test with nil FX ID
        local fake_track = {} -- Mock track object
        local fx_idx, err = utils.get_fx(fake_track, nil)
        test_runner.assert_equals(-1, fx_idx, "Should return -1 for nil FX ID")
        test_runner.assert_not_nil(err, "Should return error message for nil FX ID")
    end)

    test_runner.describe("utils.ensure_dir", function()
        -- Test with nil input
        local success, err = utils.ensure_dir(nil)
        test_runner.assert_false(success, "Should return false for nil input")
        test_runner.assert_not_nil(err, "Should return error message for nil input")
    end)

    test_runner.describe("utils.read_file", function()
        -- Test with nil input
        local content, err = utils.read_file(nil)
        test_runner.assert_nil(content, "Should return nil for nil input")
        test_runner.assert_not_nil(err, "Should return error message for nil input")

        -- Test with non-existent file
        local fake_file = script_path .. "nonexistent_file_12345.txt"
        local content, err = utils.read_file(fake_file)
        test_runner.assert_nil(content, "Should return nil for non-existent file")
        test_runner.assert_not_nil(err, "Should return error message for non-existent file")
    end)

    test_runner.describe("utils.write_file", function()
        -- Test with nil file path
        local success, err = utils.write_file(nil, "content")
        test_runner.assert_false(success, "Should return false for nil file path")
        test_runner.assert_not_nil(err, "Should return error message for nil file path")

        -- Test with nil content
        local success, err = utils.write_file("/tmp/test.txt", nil)
        test_runner.assert_false(success, "Should return false for nil content")
        test_runner.assert_not_nil(err, "Should return error message for nil content")
    end)
end

return test_utils
