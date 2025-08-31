-- parameter_discovery.lua
-- Script to discover and save FX parameter information to a JSON file

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
    utils.print("Starting FX parameter discovery...")

    -- Create discovery data - will fail fatally if there's an error
    local discovery_data = safe_execute(function()
        local data = fx_manager.discover_fx_parameters()
        if not data or not data.fx_data then
            error("Failed to discover FX parameters")
        end
        return data
    end, true)

    -- Save to file - use fixed path relative to script
    local script_path = utils.get_script_path()
    local output_file = script_path .. "../fx_parameters.json"

    -- Write to file - will fail fatally if there's an error
    safe_execute(function()
        local success, err = json.write_file(output_file, discovery_data)
        if not success then
            error("Failed to save parameter discovery data: " .. (err or "unknown error"))
        end
        utils.print("Parameter discovery completed successfully!")
        utils.print("Data saved to: " .. output_file)
    end, true)

    utils.print("=== FX Parameter Discovery Complete ===")
end

-- Run the main function with error handling
safe_execute(main, true)
