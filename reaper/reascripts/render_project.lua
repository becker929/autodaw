-- render_project.lua - Module for rendering projects

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
    utils.print("=== Render Project Script ===")

    -- Default render settings
    local proj_path = reaper.GetProjectPath("")
    local render_dir = proj_path .. "/renders"
    -- Render with default options including session context
    local render_options = { session_name = "standalone", render_id = "default" }
    local success = project_manager.render_project(render_dir, "output", render_options)

    if success then
        utils.print("Project rendered successfully.")
    else
        utils.print("Failed to render project.")
    end

    utils.print("=== Render Project Complete ===")
end

-- Determine if this script is being run directly
if not package.loaded["render_project"] then
    main()
end

-- Return the render_project function for use as a module
return function(render_dir, file_name, options)
    return project_manager.render_project(render_dir, file_name, options)
end
