-- test_constants.lua - Tests for constants module

local test_runner = require("tests.test_runner")

local function run_tests()
    test_runner.describe("Constants Module Loading", function()
        local constants = require("lib.constants")
        test_runner.assert_not_nil(constants, "Constants module should load successfully")
    end)

    test_runner.describe("Directory Constants", function()
        local constants = require("lib.constants")

        test_runner.assert_type("string", constants.SESSION_CONFIGS_DIR, "SESSION_CONFIGS_DIR should be string")
        test_runner.assert_type("string", constants.SESSION_RESULTS_DIR, "SESSION_RESULTS_DIR should be string")
        test_runner.assert_type("string", constants.RENDERS_DIR, "RENDERS_DIR should be string")

        test_runner.assert_equals("session-configs", constants.SESSION_CONFIGS_DIR, "SESSION_CONFIGS_DIR should be correct")
        test_runner.assert_equals("session-results", constants.SESSION_RESULTS_DIR, "SESSION_RESULTS_DIR should be correct")
        test_runner.assert_equals("renders", constants.RENDERS_DIR, "RENDERS_DIR should be correct")
    end)

    test_runner.describe("Default Render Settings", function()
        local constants = require("lib.constants")

        test_runner.assert_type("number", constants.DEFAULT_SAMPLE_RATE, "DEFAULT_SAMPLE_RATE should be number")
        test_runner.assert_type("number", constants.DEFAULT_CHANNELS, "DEFAULT_CHANNELS should be number")
        test_runner.assert_type("string", constants.DEFAULT_RENDER_FORMAT, "DEFAULT_RENDER_FORMAT should be string")

        test_runner.assert_equals(44100, constants.DEFAULT_SAMPLE_RATE, "DEFAULT_SAMPLE_RATE should be 44100")
        test_runner.assert_equals(2, constants.DEFAULT_CHANNELS, "DEFAULT_CHANNELS should be 2")
    end)

    test_runner.describe("File Naming Constants", function()
        local constants = require("lib.constants")

        test_runner.assert_type("string", constants.RENDER_FILENAME_PATTERN, "RENDER_FILENAME_PATTERN should be string")
        test_runner.assert_type("string", constants.TIMESTAMP_FORMAT, "TIMESTAMP_FORMAT should be string")
        test_runner.assert_equals("%s_%s_%s_%s", constants.RENDER_FILENAME_PATTERN, "RENDER_FILENAME_PATTERN should be correct")
        test_runner.assert_equals("%Y%m%d_%H%M%S", constants.TIMESTAMP_FORMAT, "TIMESTAMP_FORMAT should be correct")
    end)

    test_runner.describe("Error Messages", function()
        local constants = require("lib.constants")

        test_runner.assert_type("string", constants.ERROR_SESSION_NOT_FOUND, "ERROR_SESSION_NOT_FOUND should be string")
        test_runner.assert_type("string", constants.ERROR_INVALID_JSON, "ERROR_INVALID_JSON should be string")
        test_runner.assert_type("string", constants.ERROR_MISSING_RENDER_CONFIGS, "ERROR_MISSING_RENDER_CONFIGS should be string")
        test_runner.assert_type("string", constants.ERROR_TRACK_SETUP_FAILED, "ERROR_TRACK_SETUP_FAILED should be string")
        test_runner.assert_type("string", constants.ERROR_PARAMETER_APPLICATION_FAILED, "ERROR_PARAMETER_APPLICATION_FAILED should be string")
        test_runner.assert_type("string", constants.ERROR_MIDI_LOAD_FAILED, "ERROR_MIDI_LOAD_FAILED should be string")
        test_runner.assert_type("string", constants.ERROR_RENDER_FAILED, "ERROR_RENDER_FAILED should be string")
    end)
end

return {
    run_tests = run_tests
}
