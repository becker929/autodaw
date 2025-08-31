# ReaScripts Testing Framework

This directory contains a comprehensive unit testing framework for the ReaScripts library.

## Structure

```
tests/
├── README.md              # This file
├── test_runner.lua         # Core testing framework
├── run_tests.lua          # Main test runner
├── test_utils.lua         # Tests for utils module
├── test_json.lua          # Tests for JSON module
├── test_error_handler.lua # Tests for error handler
└── test_fx_manager.lua    # Tests for FX manager
```

## Running Tests

### In REAPER

1. Load `tests/run_tests.lua` as a ReaScript
2. Run it from the Actions menu
3. Check the REAPER console for test results

### Command Line (Outside REAPER)

```bash
cd /Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/reascripts
lua test_standalone.lua
```

## Test Framework Features

### Assertions

- `assert_true(condition, message)` - Assert condition is true
- `assert_false(condition, message)` - Assert condition is false
- `assert_equals(expected, actual, message)` - Assert values are equal
- `assert_not_nil(value, message)` - Assert value is not nil
- `assert_nil(value, message)` - Assert value is nil
- `assert_type(expected_type, value, message)` - Assert value has expected type
- `assert_error(func, message)` - Assert function throws an error

### Test Organization

```lua
test_runner.describe("Test Suite Name", function()
    test_runner.assert_true(true, "This should pass")
    test_runner.assert_equals(2, 1+1, "Math should work")
end)
```

### Test Statistics

The framework tracks:
- Total tests run
- Tests passed
- Tests failed
- Detailed error messages
- Success rate

## Writing New Tests

1. Create a new test file: `test_your_module.lua`
2. Follow this template:

```lua
-- test_your_module.lua - Tests for your_module

local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "../?.lua;" .. package.path

local test_runner = require("tests.test_runner")
local your_module = require("lib.your_module")

local test_your_module = {}

function test_your_module.run_tests()
    test_runner.describe("your_module.some_function", function()
        local result = your_module.some_function("input")
        test_runner.assert_not_nil(result, "Should return a result")
        test_runner.assert_equals("expected", result, "Should return expected value")
    end)

    test_runner.describe("your_module.another_function", function()
        test_runner.assert_error(function()
            your_module.another_function(nil)
        end, "Should throw error for nil input")
    end)
end

return test_your_module
```

3. Add your test module to `run_tests.lua`:

```lua
local test_your_module = require("tests.test_your_module")

-- Add to test_modules array
local test_modules = {
    test_utils,
    test_json,
    test_error_handler,
    test_fx_manager,
    test_your_module  -- Add here
}
```

## Test Coverage

Current test coverage includes:

- **Utils Module**: File operations, track/FX lookup, directory creation
- **JSON Module**: Encoding, parameter parsing, FX mapping parsing
- **Error Handler**: Error logging, validation, fatal error handling
- **FX Manager**: Parameter discovery, mapping, updates (with mocked REAPER API)

## Mocking REAPER API

For testing outside REAPER, the framework provides basic mocks of REAPER functions. These can be extended as needed:

```lua
if not reaper then
    reaper = {
        ShowConsoleMsg = function(msg) print(msg:gsub("\n$", "")) end,
        GetProjectPath = function() return "/tmp/test_project" end,
        -- Add more mocks as needed
    }
end
```

## Best Practices

1. **Test Edge Cases**: Always test with nil inputs, empty strings, invalid types
2. **Test Error Conditions**: Ensure error handling works correctly
3. **Keep Tests Simple**: Each test should verify one specific behavior
4. **Use Descriptive Messages**: Make assertion messages clear and helpful
5. **Mock External Dependencies**: Use mocks for REAPER API calls when testing outside REAPER
