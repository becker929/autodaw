-- main.lua - Main ReaScript for the session
-- This script loads and executes session configurations from JSON

-- Define reaper as a global to avoid linter warnings
reaper = reaper

-- Add the current script's directory to the package path to find modules
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

-- Import modules using require
local utils = require("lib.utils")
local constants = require("lib.constants")
local session_manager = require("lib.session_manager")
local error_handler = require("lib.error_handler")

-- Error handling wrapper
local function safe_execute(func, fatal, ...)
    return error_handler.try(func, fatal, ...)
end

-- Main function
function main()
    utils.print("=== ReaScript Main Started ===")

    -- Execute session from JSON configuration
    -- Default session file - this could be parameterized in the future
    local session_file = "example_session.json"

    utils.print("Loading session: " .. session_file)

    -- Execute the entire session with fail-fast error handling
    session_manager.execute_session(session_file)

    utils.print("=== ReaScript Main Ended ===")
end

-- Run the main function with error handling
safe_execute(main, true)
