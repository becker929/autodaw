-- main.lua - Main ReaScript for the session
-- This script performs basic project setup and rendering

-- Define reaper as a global to avoid linter warnings
reaper = reaper

-- Add the current script's directory to the package path to find modules
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

-- Import modules using require
local utils = require("lib.utils")
local json = require("lib.json")
local fx_manager = require("lib.fx_manager")
local project_manager = require("lib.project_manager")
local error_handler = require("lib.error_handler")

-- Error handling wrapper
local function safe_execute(func, fatal, ...)
    return error_handler.try(func, fatal, ...)
end

-- Main function
function main()
    utils.print("=== ReaScript Main Started ===")
    local proj_path = reaper.GetProjectPath("")
    local render_dir = proj_path .. "/renders"

    -- Load parameter mapping if available - this will fail fatally if there's an error
    fx_manager.load_param_mapping()

    -- Define parameter changes for testing
    local params_render1 = {
        {
            track = "0",
            fx = "Serum",
            param = "A Octave",
            value = 0.4  -- Slightly lower octave
        },
        {
            track = "0",
            fx = "Serum",
            param = "A Fine",
            value = 0.0  -- No fine tuning
        }
    }

    local params_render2 = {
        {
            track = "0",
            fx = "Serum",
            param = "A Octave",
            value = 0.6  -- Slightly higher octave
        },
        {
            track = "0",
            fx = "Serum",
            param = "A Fine",
            value = 0.25  -- Quarter fine tuning
        }
    }

    -- First render with first parameter set
    utils.print("=== First Render with Parameter Set 1 ===")
    project_manager.clear_project()
    project_manager.setup_simple_project()

    -- Apply first parameter set
    local success_count, total_count = fx_manager.process_param_changes(params_render1)
    utils.print("Applied " .. success_count .. " of " .. total_count .. " parameters for render 1")

    -- Render with first parameter set
    local render1_options = { session_name = "main_session", render_id = "render1" }
    project_manager.render_project(render_dir, "params", render1_options)
    utils.print("Render 1 completed successfully!")

    -- Second render with second parameter set
    utils.print("=== Second Render with Parameter Set 2 ===")
    project_manager.clear_project()
    project_manager.setup_simple_project()

    -- Apply second parameter set
    local success_count, total_count = fx_manager.process_param_changes(params_render2)
    utils.print("Applied " .. success_count .. " of " .. total_count .. " parameters for render 2")

    -- Render with second parameter set
    local render2_options = { session_name = "main_session", render_id = "render2" }
    project_manager.render_project(render_dir, "params", render2_options)
    utils.print("Render 2 completed successfully!")

    -- Show final parameter values
    utils.print("=== Final Parameter Values ===")
    local param_requests = {
        { track = 0, fx = "Serum", param = "A Octave" },
        { track = 0, fx = "Serum", param = "A Fine" }
    }

    local param_values = fx_manager.get_param_values(param_requests)
    utils.print("Current parameter values:")
    for i, param in ipairs(param_values) do
        utils.print("  Track: " .. tostring(param.track) .. ", FX: " .. tostring(param.fx) ..
              ", Param: " .. tostring(param.param) .. ", Value: " .. tostring(param.formatted_value))
    end

    utils.print("=== ReaScript Main Ended ===")
end

-- Run the main function with error handling
safe_execute(main, true)
