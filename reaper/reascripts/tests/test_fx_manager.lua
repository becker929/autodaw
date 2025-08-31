-- test_fx_manager.lua - Tests for the fx_manager module

-- Add the parent directory to the path
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "../?.lua;" .. package.path

local test_runner = require("tests.test_runner")

-- Mock REAPER functions for testing
if not reaper then
    reaper = {
        ShowConsoleMsg = function(msg) print(msg:gsub("\n$", "")) end,
        GetProjectPath = function() return "/tmp/test_project" end,
        GetProjectName = function() return "Test Project" end,
        CountTracks = function() return 0 end,
        GetTrack = function() return nil end,
        GetTrackName = function() return true, "Test Track" end,
        TrackFX_GetCount = function() return 0 end,
        TrackFX_GetFXName = function() return true, "Test FX" end,
        TrackFX_GetNumParams = function() return 0 end,
        TrackFX_GetParamName = function() return true, "Test Param" end,
        TrackFX_GetParam = function() return 0.5, 0.0, 1.0 end,
        TrackFX_GetParamEx = function() return 0.5, 0.0, 1.0, 0.5 end,
        TrackFX_GetFormattedParamValue = function() return true, "50%" end,
        TrackFX_GetParamIdent = function() return false, "" end,
        TrackFX_GetParamNormalized = function() return 0.5 end,
        file_exists = function() return false end
    }
end

local fx_manager = require("lib.fx_manager")

local test_fx_manager = {}

function test_fx_manager.run_tests()
        test_runner.describe("fx_manager.load_param_mapping", function()
        -- Test with non-existent file - this should throw a fatal error
        test_runner.assert_error(function()
            fx_manager.load_param_mapping("/nonexistent/path/file.json")
        end, "Should throw fatal error for non-existent file")

        -- Note: We can't easily test with a real file without creating one
        -- In a real test environment, we would create a temporary test file
    end)

    test_runner.describe("fx_manager.get_fx_params_info", function()
        -- Test with nil track
        local result = fx_manager.get_fx_params_info(nil, 0)
        test_runner.assert_nil(result, "Should return nil for nil track")

        -- Test with invalid FX index
        local mock_track = {}
        local result = fx_manager.get_fx_params_info(mock_track, -1)
        test_runner.assert_nil(result, "Should return nil for invalid FX index")
    end)

    test_runner.describe("fx_manager.update_single_param", function()
        -- Test with nil inputs
        local success = fx_manager.update_single_param(nil, "fx", "param", 0.5)
        test_runner.assert_false(success, "Should return false for nil track ID")

        local success = fx_manager.update_single_param("track", nil, "param", 0.5)
        test_runner.assert_false(success, "Should return false for nil FX ID")

        local success = fx_manager.update_single_param("track", "fx", nil, 0.5)
        test_runner.assert_false(success, "Should return false for nil param ID")

        local success = fx_manager.update_single_param("track", "fx", "param", nil)
        test_runner.assert_false(success, "Should return false for nil value")
    end)

    test_runner.describe("fx_manager.get_single_param", function()
        -- Test with nil inputs
        local result = fx_manager.get_single_param(nil, "fx", "param")
        test_runner.assert_nil(result, "Should return nil for nil track ID")

        local result = fx_manager.get_single_param("track", nil, "param")
        test_runner.assert_nil(result, "Should return nil for nil FX ID")

        local result = fx_manager.get_single_param("track", "fx", nil)
        test_runner.assert_nil(result, "Should return nil for nil param ID")
    end)

    test_runner.describe("fx_manager.process_param_changes", function()
        -- Test with nil input
        local success_count, total_count = fx_manager.process_param_changes(nil)
        test_runner.assert_equals(0, success_count, "Should return 0 success for nil input")
        test_runner.assert_equals(0, total_count, "Should return 0 total for nil input")

        -- Test with non-table input
        local success_count, total_count = fx_manager.process_param_changes("not a table")
        test_runner.assert_equals(0, success_count, "Should return 0 success for non-table input")
        test_runner.assert_equals(0, total_count, "Should return 0 total for non-table input")

        -- Test with empty table
        local success_count, total_count = fx_manager.process_param_changes({})
        test_runner.assert_equals(0, success_count, "Should return 0 success for empty table")
        test_runner.assert_equals(0, total_count, "Should return 0 total for empty table")

        -- Test with invalid parameter changes
        local invalid_changes = {
            { track = nil, fx = "fx", param = "param", value = 0.5 }
        }
        local success_count, total_count = fx_manager.process_param_changes(invalid_changes)
        test_runner.assert_equals(0, success_count, "Should return 0 success for invalid changes")
        test_runner.assert_equals(1, total_count, "Should return correct total count")
    end)

    test_runner.describe("fx_manager.get_param_values", function()
        -- Test with nil input
        local results = fx_manager.get_param_values(nil)
        test_runner.assert_type("table", results, "Should return table for nil input")
        test_runner.assert_equals(0, #results, "Should return empty table for nil input")

        -- Test with non-table input
        local results = fx_manager.get_param_values("not a table")
        test_runner.assert_type("table", results, "Should return table for non-table input")
        test_runner.assert_equals(0, #results, "Should return empty table for non-table input")

        -- Test with empty table
        local results = fx_manager.get_param_values({})
        test_runner.assert_type("table", results, "Should return table for empty input")
        test_runner.assert_equals(0, #results, "Should return empty table for empty input")
    end)

    test_runner.describe("fx_manager.discover_fx_parameters", function()
        -- This test mainly ensures the function doesn't crash
        -- In a real REAPER environment, it would discover actual FX parameters
        local result = fx_manager.discover_fx_parameters()
        test_runner.assert_not_nil(result, "Should return a result")
        test_runner.assert_type("table", result, "Should return a table")
        test_runner.assert_not_nil(result.project, "Should have project info")
        test_runner.assert_not_nil(result.fx_data, "Should have fx_data")
    end)
end

return test_fx_manager
