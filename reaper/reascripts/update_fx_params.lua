-- update_fx_params.lua - Script for updating FX parameters

-- Define reaper as a global to avoid linter warnings
reaper = reaper

-- Add the current script's directory to the package path to find modules
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

-- Import modules
local utils = require("lib.utils")
local json = require("lib.json")
local fx_manager = require("lib.fx_manager")
local error_handler = require("lib.error_handler")

-- Error handling wrapper
local function safe_execute(func, fatal, ...)
    return error_handler.try(func, fatal, ...)
end

-- Main function
function main()
    utils.print("=== FX Parameter Update Script ===")

    -- Load parameter mapping if available - this will fail fatally if there's an error
    fx_manager.load_param_mapping()

    -- Example JSON-like string with parameter changes
    local json_str = [[
    {
        "paramChanges": [
            {
                "track": "Synth",
                "fx": "Serum",
                "param": "OSC1 OCT",
                "value": 0.5
            },
            {
                "track": "Synth",
                "fx": "Serum",
                "param": "OSC1 FINE",
                "value": 0.25
            },
            {
                "track": "Synth",
                "fx": "Serum",
                "param": "OSC1 VOLUME",
                "value": 0.8
            }
        ]
    }
    ]]

    -- Parse the JSON-like string - will fail fatally if the JSON is invalid
    local params_data = safe_execute(function()
        local data = json.parse_param_changes(json_str)
        if not data or not data.paramChanges then
            error("Invalid parameter changes format")
        end
        return data
    end, true)

    -- Process the parameter changes - will fail fatally if parameters can't be updated
    local success_count, total_count = fx_manager.process_param_changes(params_data.paramChanges)
    utils.print("Updated " .. success_count .. " of " .. total_count .. " parameters")

    -- Example of retrieving parameter values after changes
    local param_requests = {}
    for i, change in ipairs(params_data.paramChanges) do
        table.insert(param_requests, {
            track = change.track,
            fx = change.fx,
            param = change.param
        })
    end

    local param_values = fx_manager.get_param_values(param_requests)
    utils.print("Current parameter values:")
    for i, param in ipairs(param_values) do
        utils.print("  Track: " .. tostring(param.track) .. ", FX: " .. tostring(param.fx) ..
              ", Param: " .. tostring(param.param) .. ", Value: " .. tostring(param.formatted_value))
    end

    utils.print("=== FX Parameter Update Completed ===")
end

-- Run the main function with error handling
safe_execute(main, true)
