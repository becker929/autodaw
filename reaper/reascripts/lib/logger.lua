-- logger.lua - Logging module that writes to both console and file
reaper = reaper

local logger = {}
local log_file_handle = nil
local log_file_path = nil

-- Initialize logging with session-specific log file
function logger.init(session_name)
    -- Create log file path in session-results directory
    local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
    local base_path
    if script_path then
        base_path = script_path .. "../../"  -- Go up two levels from reascripts/lib/ to reaper/
    else
        base_path = "./"
    end

    local log_dir = base_path .. "session-results"
    local timestamp = os.date("%Y%m%d_%H%M%S")
    log_file_path = log_dir .. "/" .. session_name .. "_" .. timestamp .. ".log"

    -- Ensure log directory exists
    local utils = require("lib.utils")
    utils.ensure_dir(log_dir)

    -- Open log file for writing
    log_file_handle = io.open(log_file_path, "w")
    if log_file_handle then
        logger.log("LOGGER_INIT", "Logging initialized to: " .. log_file_path)
    else
        reaper.ShowConsoleMsg("ERROR: Could not open log file: " .. log_file_path .. "\n")
    end

    return log_file_path
end

-- Log a message to both console and file
function logger.log(level, message)
    local timestamp = os.date("%Y-%m-%d %H:%M:%S")
    local formatted_msg = "[" .. timestamp .. "] [" .. level .. "] " .. message

    -- Write to REAPER console
    reaper.ShowConsoleMsg(formatted_msg .. "\n")

    -- Write to log file if available
    if log_file_handle then
        log_file_handle:write(formatted_msg .. "\n")
        log_file_handle:flush()  -- Ensure immediate write
    end
end

-- Convenience functions for different log levels
function logger.info(message)
    logger.log("INFO", message)
end

function logger.warn(message)
    logger.log("WARN", message)
end

function logger.error(message)
    logger.log("ERROR", message)
end

function logger.debug(message)
    logger.log("DEBUG", message)
end

-- Log session events (for Python monitoring)
function logger.session_start(session_name)
    logger.log("SESSION", "SESSION_START:" .. session_name)
end

function logger.session_complete(session_name)
    logger.log("SESSION", "SESSION_COMPLETE:" .. session_name)
end

function logger.render_start(render_id)
    logger.log("RENDER", "RENDER_START:" .. render_id)
end

function logger.render_complete(render_id, render_path)
    logger.log("RENDER", "RENDER_COMPLETE:" .. render_id .. ":" .. render_path)
end

-- Close logging
function logger.close()
    if log_file_handle then
        logger.log("LOGGER", "Closing log file")
        log_file_handle:close()
        log_file_handle = nil
    end
end

-- Get log file path
function logger.get_log_file_path()
    return log_file_path
end

return logger
