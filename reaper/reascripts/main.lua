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
local logger = require("lib.logger")

-- Error handling wrapper
local function safe_execute(func, fatal, ...)
    return error_handler.try(func, fatal, ...)
end

-- Main function
function main()
    -- Execute session from JSON configuration
    local session_file = "example_session.json"

    local current_session_path = "current_session.txt"
    if utils.file_exists(current_session_path) then
        local file = io.open(current_session_path, "r")
        if file then
            local specified_session = file:read("*line")
            file:close()
            if specified_session and specified_session ~= "" then
                session_file = specified_session
            end
        end
    end

    local session_name = session_file:gsub("%.json$", "")
    local log_file_path = logger.init(session_name)
    logger.session_start(session_name)
    logger.info("ReaScript Main Started")
    logger.info("Log file: " .. (log_file_path or "none"))
    logger.info("Loading session: " .. session_file)
    session_manager.execute_session(session_file)
    logger.info("ReaScript Main Ended")
    logger.session_complete(session_name)
    logger.close()
end

-- Run the main function with error handling
safe_execute(main, true)
