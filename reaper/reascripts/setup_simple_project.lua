-- setup_simple_project.lua - Module for setting up a simple project

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
    utils.print("=== Setup Simple Project Script ===")

    -- Clear project first
    project_manager.clear_project()

    -- Setup project with default options
    local success = project_manager.setup_simple_project()

    if success then
        utils.print("Simple project setup successfully.")
    else
        utils.print("Failed to set up simple project.")
    end

    utils.print("=== Setup Simple Project Complete ===")
end

-- Determine if this script is being run directly
if not package.loaded["setup_simple_project"] then
    main()
end

-- Return the setup_simple_project function for use as a module
return function(options)
    return project_manager.setup_simple_project(options)
end
