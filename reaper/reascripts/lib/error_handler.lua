-- error_handler.lua - Error handling utilities

-- Import utilities
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

local utils = require("lib.utils")

local error_handler = {}

-- Global error log
error_handler.error_log = {}

-- Function to add an error to the log
function error_handler.log_error(source, message, details)
    local error_entry = {
        timestamp = os.date("%Y-%m-%d %H:%M:%S"),
        source = source,
        message = message,
        details = details
    }

    table.insert(error_handler.error_log, error_entry)

    -- Print to console
    utils.print("[ERROR] " .. source .. ": " .. message)
    if details then
        utils.print("  Details: " .. tostring(details))
    end

    return error_entry
end

-- Function to safely execute a function with error handling
-- Set fatal=true to crash the script on error
function error_handler.try(func, fatal, ...)
    local success, result = pcall(func, ...)

    if not success then
        error_handler.log_error("try", "Function execution failed", result)

        if fatal then
            utils.print("CRITICAL ERROR: Function execution failed. Exiting script.")
            error(result)
        end

        return nil, result
    end

    return result
end

-- Function to validate parameters
function error_handler.validate(params, schema)
    for key, requirement in pairs(schema) do
        local value = params[key]

        -- Check if required parameter is missing
        if requirement.required and (value == nil) then
            return false, "Missing required parameter: " .. key
        end

        -- If value exists, validate type
        if value ~= nil and requirement.type then
            local value_type = type(value)
            if value_type ~= requirement.type then
                return false, "Parameter " .. key .. " has wrong type. Expected " ..
                              requirement.type .. ", got " .. value_type
            end
        end

        -- If value exists and has validator function, run it
        if value ~= nil and requirement.validator and not requirement.validator(value) then
            return false, "Parameter " .. key .. " failed validation"
        end
    end

    return true
end

-- Function to write error log to file
function error_handler.write_log_to_file(file_path)
    if #error_handler.error_log == 0 then
        return true, "No errors to log"
    end

    local file = io.open(file_path, "w")
    if not file then
        return false, "Could not open log file for writing: " .. file_path
    end

    file:write("=== REASCRIPT ERROR LOG ===\n")
    file:write("Generated: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n\n")

    for i, err in ipairs(error_handler.error_log) do
        file:write("Error #" .. i .. "\n")
        file:write("Timestamp: " .. err.timestamp .. "\n")
        file:write("Source: " .. err.source .. "\n")
        file:write("Message: " .. err.message .. "\n")

        if err.details then
            file:write("Details: " .. tostring(err.details) .. "\n")
        end

        file:write("\n")
    end

    file:close()
    return true, "Error log written to: " .. file_path
end

return error_handler
