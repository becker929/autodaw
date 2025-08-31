-- clear_project.lua - Module for clearing the current project

-- Define reaper as a global to avoid linter warnings
reaper = reaper

-- Add the current script's directory to the package path to find modules
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

-- Import modules
local utils = require("lib.utils")
local project_manager = require("lib.project_manager")

-- Main function when run as a standalone script
function main()
    utils.print("=== Clear Project Script ===")

    local success = project_manager.clear_project()

    if success then
        utils.print("Project cleared successfully.")
    else
        utils.print("Failed to clear project.")
    end

    utils.print("=== Clear Project Complete ===")
end

-- Determine if this script is being run directly
if not package.loaded["clear_project"] then
    main()
end

-- Return the clear_project function for use as a module
return function()
    return project_manager.clear_project()
end
