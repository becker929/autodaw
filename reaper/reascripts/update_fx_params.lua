-- update_fx_params.lua - Example script for updating FX parameters
-- Define reaper as a global to avoid linter warnings
reaper = reaper

-- Add the current script's directory to the package path to find modules
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

-- Import the fx_updater module
local fx_updater = require("fx_updater")

-- Helper function for console output
function print(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Function to parse JSON string into Lua table
function parse_json_string(json_str)
    -- Simple JSON parser for our specific needs
    -- This is not a full JSON parser, but works for our simple case

    -- First, let's define our parsed result
    local result = {}

    -- Look for the paramChanges array
    local param_changes_str = json_str:match('"paramChanges"%s*:%s*%[(.-)%]')
    if not param_changes_str then
        print("Error: Could not find paramChanges array in JSON")
        return nil
    end

    -- Initialize the paramChanges array
    result.paramChanges = {}

    -- Find all parameter change objects
    for param_obj_str in param_changes_str:gmatch('{(.-)}') do
        local param_change = {}

        -- Extract track
        local track = param_obj_str:match('"track"%s*:%s*"?([^",}]+)"?')
        if track then param_change.track = track end

        -- Extract fx
        local fx = param_obj_str:match('"fx"%s*:%s*"?([^",}]+)"?')
        if fx then param_change.fx = fx end

        -- Extract param
        local param = param_obj_str:match('"param"%s*:%s*"?([^",}]+)"?')
        if param then param_change.param = param end

        -- Extract value
        local value_str = param_obj_str:match('"value"%s*:%s*"?([^",}]+)"?')
        if value_str then
            -- Convert to number if possible
            local num_value = tonumber(value_str)
            param_change.value = num_value or value_str
        end

        -- Add this parameter change to our result if it has all required fields
        if param_change.track and param_change.fx and param_change.param and param_change.value ~= nil then
            table.insert(result.paramChanges, param_change)
        end
    end

    return result
end

-- Main function
function main()
    print("=== FX Parameter Update Script ===")

    -- Load parameter mapping if available
    fx_updater.load_param_mapping()

    -- Example JSON-like string with parameter changes
    local json_str = [[
    {
        "paramChanges": [
            {
                "track": "Serum Track",
                "fx": "Serum",
                "param": "OSC1 OCT",
                "value": 0.5
            },
            {
                "track": "Serum Track",
                "fx": "Serum",
                "param": "OSC1 FINE",
                "value": 0.25
            },
            {
                "track": "Serum Track",
                "fx": "Serum",
                "param": "OSC1 VOLUME",
                "value": 0.8
            }
        ]
    }
    ]]

    -- You could also get the JSON from an external source
    -- For example, from a file:
    -- local file = io.open("params.json", "r")
    -- local json_str = file:read("*all")
    -- file:close()

    -- Parse the JSON-like string
    local params_data = parse_json_string(json_str)

    if params_data and params_data.paramChanges then
        -- Process the parameter changes
        local success_count, total_count = fx_updater.process_param_changes(params_data.paramChanges)
        print("Updated " .. success_count .. " of " .. total_count .. " parameters")

        -- Example of retrieving parameter values after changes
        local param_requests = {}
        for i, change in ipairs(params_data.paramChanges) do
            table.insert(param_requests, {
                track = change.track,
                fx = change.fx,
                param = change.param
            })
        end

        local param_values = fx_updater.get_param_values(param_requests)
        print("Current parameter values:")
        for i, param in ipairs(param_values) do
            print("  Track: " .. tostring(param.track) .. ", FX: " .. tostring(param.fx) ..
                  ", Param: " .. tostring(param.param) .. ", Value: " .. tostring(param.formatted_value))
        end
    else
        print("No valid parameter changes found in input")
    end

    print("=== FX Parameter Update Completed ===")
end

-- Run the main function
main()
