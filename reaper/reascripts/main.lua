-- main.lua - Main ReaScript for the session
-- This script performs basic project setup and rendering

-- Define reaper as a global to avoid linter warnings
reaper = reaper

-- Add the current script's directory to the package path to find modules
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

-- Import modules using require
local clear_project = require("clear_project")
local render_project = require("render_project")
local setup_simple_project = require("setup_simple_project")

-- Helper function for console output
function print(msg)
    reaper.ShowConsoleMsg(msg .. "\n")
end

-- Main function
function main()
    print("=== ReaScript Main Started ===")
    local proj_path = reaper.GetProjectPath("")
    local render_dir = proj_path .. "/renders"

    -- first render
    clear_project()
    if setup_simple_project() then
        local success = render_project(render_dir, "test_render1")
        if success then
            print("Render 1 completed successfully!")
        else
            print("Render 1 may have failed - check REAPER for details")
        end
    else
        print("Project setup failed - skipping render 1")
    end

    -- second render
    clear_project()
    if setup_simple_project() then
        local success = render_project(render_dir, "test_render2")
        if success then
            print("Render 2 completed successfully!")
        else
            print("Render 2 may have failed - check REAPER for details")
        end
    else
        print("Project setup failed - skipping render 2")
    end

    print("=== ReaScript Main Ended ===")
end

-- Run the main function
main()
