-- test_runner.lua - Simple test framework and runner for ReaScripts
-- This provides a basic testing framework since we can't use external Lua testing libraries in REAPER

local test_runner = {}

-- Test statistics
local stats = {
    total = 0,
    passed = 0,
    failed = 0,
    errors = {}
}

-- Current test context
local current_test = nil

-- Print function (can be overridden for different environments)
test_runner.print = function(msg)
    if reaper then
        reaper.ShowConsoleMsg(msg .. "\n")
    else
        print(msg)
    end
end

-- Assert functions
function test_runner.assert_true(condition, message)
    stats.total = stats.total + 1
    message = message or "Expected true, got false"

    if condition then
        stats.passed = stats.passed + 1
        test_runner.print("  ✓ " .. message)
    else
        stats.failed = stats.failed + 1
        local error_msg = "FAIL: " .. (current_test or "Unknown test") .. " - " .. message
        table.insert(stats.errors, error_msg)
        test_runner.print("  ✗ " .. error_msg)
    end
end

function test_runner.assert_false(condition, message)
    test_runner.assert_true(not condition, message or "Expected false, got true")
end

function test_runner.assert_equals(expected, actual, message)
    local msg = message or ("Expected '" .. tostring(expected) .. "', got '" .. tostring(actual) .. "'")
    test_runner.assert_true(expected == actual, msg)
end

function test_runner.assert_not_nil(value, message)
    test_runner.assert_true(value ~= nil, message or "Expected non-nil value")
end

function test_runner.assert_nil(value, message)
    test_runner.assert_true(value == nil, message or "Expected nil value")
end

function test_runner.assert_type(expected_type, value, message)
    local actual_type = type(value)
    local msg = message or ("Expected type '" .. expected_type .. "', got '" .. actual_type .. "'")
    test_runner.assert_equals(expected_type, actual_type, msg)
end

function test_runner.assert_error(func, message)
    local success, error_msg = pcall(func)
    test_runner.assert_false(success, message or "Expected function to throw an error")
end

-- Test runner functions
function test_runner.describe(test_name, test_func)
    current_test = test_name
    test_runner.print("\n=== " .. test_name .. " ===")

    local success, error_msg = pcall(test_func)
    if not success then
        stats.failed = stats.failed + 1
        local error_msg = "ERROR in test '" .. test_name .. "': " .. tostring(error_msg)
        table.insert(stats.errors, error_msg)
        test_runner.print("  ✗ " .. error_msg)
    end

    current_test = nil
end

function test_runner.run_all_tests(test_modules)
    test_runner.print("Starting test run...\n")

    for _, module in ipairs(test_modules) do
        if type(module) == "function" then
            module()
        elseif type(module) == "table" and module.run_tests then
            module.run_tests()
        end
    end

    test_runner.print_summary()
end

function test_runner.print_summary()
    test_runner.print("\n" .. string.rep("=", 50))
    test_runner.print("TEST SUMMARY")
    test_runner.print(string.rep("=", 50))
    test_runner.print("Total tests: " .. stats.total)
    test_runner.print("Passed: " .. stats.passed)
    test_runner.print("Failed: " .. stats.failed)

    if stats.failed > 0 then
        test_runner.print("\nFAILED TESTS:")
        for _, error in ipairs(stats.errors) do
            test_runner.print("  " .. error)
        end
    end

    local success_rate = stats.total > 0 and (stats.passed / stats.total * 100) or 0
    test_runner.print(string.format("\nSuccess rate: %.1f%%", success_rate))

    if stats.failed == 0 then
        test_runner.print("🎉 All tests passed!")
    else
        test_runner.print("❌ Some tests failed.")
    end
end

function test_runner.reset_stats()
    stats.total = 0
    stats.passed = 0
    stats.failed = 0
    stats.errors = {}
end

return test_runner
