-- test_error_handler.lua - Tests for the error_handler module

-- Add the parent directory to the path
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "../?.lua;" .. package.path

local test_runner = require("tests.test_runner")
local error_handler = require("lib.error_handler")

local test_error_handler = {}

function test_error_handler.run_tests()
    test_runner.describe("error_handler.log_error", function()
        -- Clear any existing errors
        error_handler.error_log = {}

        local entry = error_handler.log_error("test_source", "test message", "test details")

        test_runner.assert_not_nil(entry, "Should return error entry")
        test_runner.assert_equals("test_source", entry.source, "Should store source")
        test_runner.assert_equals("test message", entry.message, "Should store message")
        test_runner.assert_equals("test details", entry.details, "Should store details")
        test_runner.assert_not_nil(entry.timestamp, "Should have timestamp")

        test_runner.assert_equals(1, #error_handler.error_log, "Should add to error log")
        test_runner.assert_equals(entry, error_handler.error_log[1], "Should store in log")
    end)

    test_runner.describe("error_handler.try", function()
        -- Test successful function execution
        local result = error_handler.try(function()
            return "success"
        end, false)

        test_runner.assert_equals("success", result, "Should return function result on success")

        -- Test failed function execution (non-fatal)
        local result, err = error_handler.try(function()
            error("test error")
        end, false)

        test_runner.assert_nil(result, "Should return nil on error")
        test_runner.assert_not_nil(err, "Should return error message")

        -- Test fatal error handling
        test_runner.assert_error(function()
            error_handler.try(function()
                error("fatal error")
            end, true)
        end, "Should throw error when fatal=true")
    end)

    test_runner.describe("error_handler.validate", function()
        local schema = {
            name = { required = true, type = "string" },
            age = { required = false, type = "number" },
            active = { required = true, type = "boolean" }
        }

        -- Test valid parameters
        local valid_params = { name = "test", age = 25, active = true }
        local success, err = error_handler.validate(valid_params, schema)
        test_runner.assert_true(success, "Should validate correct parameters")
        test_runner.assert_nil(err, "Should not return error for valid params")

        -- Test missing required parameter
        local invalid_params = { age = 25, active = true }
        local success, err = error_handler.validate(invalid_params, schema)
        test_runner.assert_false(success, "Should fail for missing required parameter")
        test_runner.assert_not_nil(err, "Should return error message")
        test_runner.assert_true(err:match("Missing required parameter"), "Should mention missing parameter")

        -- Test wrong type
        local wrong_type_params = { name = 123, active = true }
        local success, err = error_handler.validate(wrong_type_params, schema)
        test_runner.assert_false(success, "Should fail for wrong type")
        test_runner.assert_not_nil(err, "Should return error message")
        test_runner.assert_true(err:match("wrong type"), "Should mention wrong type")

        -- Test optional parameter with correct type
        local optional_params = { name = "test", active = true }
        local success, err = error_handler.validate(optional_params, schema)
        test_runner.assert_true(success, "Should allow missing optional parameters")

        -- Test custom validator
        local custom_schema = {
            value = {
                required = true,
                type = "number",
                validator = function(v) return v > 0 end
            }
        }

        local valid_custom = { value = 5 }
        local success, err = error_handler.validate(valid_custom, custom_schema)
        test_runner.assert_true(success, "Should pass custom validation")

        local invalid_custom = { value = -1 }
        local success, err = error_handler.validate(invalid_custom, custom_schema)
        test_runner.assert_false(success, "Should fail custom validation")
    end)

    test_runner.describe("error_handler.write_log_to_file", function()
        -- Clear error log
        error_handler.error_log = {}

        -- Test with empty log
        local success, msg = error_handler.write_log_to_file("/tmp/test_log.txt")
        test_runner.assert_true(success, "Should handle empty log")
        test_runner.assert_true(msg:match("No errors"), "Should mention no errors")

        -- Add some errors and test writing
        error_handler.log_error("test1", "message1", "details1")
        error_handler.log_error("test2", "message2", "details2")

        -- Note: We can't easily test actual file writing without file system access
        -- This test mainly ensures the function doesn't crash
        local success, msg = error_handler.write_log_to_file("/dev/null")
        test_runner.assert_type("boolean", success, "Should return boolean")
        test_runner.assert_type("string", msg, "Should return message")
    end)
end

return test_error_handler
