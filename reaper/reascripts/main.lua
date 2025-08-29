-- main.lua - Central ReaScript controller for automated audio rendering system
-- This script manages which ReaScript to run based on configuration

reaper.ShowConsoleMsg("main.lua starting...\n")

function print(val)
    reaper.ShowConsoleMsg(tostring(val) .. "\n")
end

-- Configuration
local config = {
    script_dir = "/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/reascripts/",
    config_file = "/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/automation_config.txt"
}

function read_config()
    local file = io.open(config.config_file, "r")
    if not file then
        print("ERROR: Config file not found: " .. config.config_file)
        return nil
    end

    local config_data = {}
    for line in file:lines() do
        local key, value = line:match("^([^=]+)=(.*)$")
        if key and value then
            config_data[key] = value
        end
    end
    file:close()

    return config_data
end

-- Available scripts
local scripts = {
    get_params = "get_params.lua",
    change_params = "change_params.lua",
    add_midi = "add_midi.lua",
    render_audio = "render_audio.lua"
}

function create_beacon_file(status, message, script_name)
    local beacon_path = "/Users/anthonybecker/Desktop/reaper_automation_beacon.txt"
    local file = io.open(beacon_path, "w")
    if file then
        file:write("timestamp=" .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
        file:write("status=" .. status .. "\n")
        file:write("script=" .. (script_name or "main.lua") .. "\n")
        file:write("message=" .. (message or "") .. "\n")
        file:close()
        print("Beacon file updated: " .. status)
    else
        print("ERROR: Could not create beacon file")
    end
end



function run_full_workflow(session_config)
    print("Running full workflow for session " .. (session_config.session_id or "unknown"))

    -- Step 1: Get parameters
    create_beacon_file("RUNNING", "Step 1/4: Getting parameters", "get_params.lua")
    dofile(config.script_dir .. "get_params.lua")

    -- Step 2: Change parameters (specifically octave)
    create_beacon_file("RUNNING", "Step 2/4: Changing octave parameter to " .. (session_config.parameter_value or "0.0"), "change_params_octave.lua")
    dofile(config.script_dir .. "change_params_octave.lua")

    -- Step 3: Add MIDI
    create_beacon_file("RUNNING", "Step 3/4: Adding MIDI notes", "add_midi.lua")
    dofile(config.script_dir .. "add_midi.lua")

    -- Step 4: Render audio
    create_beacon_file("RUNNING", "Step 4/4: Rendering audio", "render_audio.lua")
    dofile(config.script_dir .. "render_audio.lua")

    create_beacon_file("COMPLETED", "Full workflow completed for session " .. (session_config.session_id or "unknown"), "main.lua")
end

-- Main execution
function main()
    print("Reading automation configuration...")
    local session_config = read_config()

    if not session_config then
        create_beacon_file("ERROR", "Could not read configuration file")
        return
    end

    print("Workflow mode: " .. (session_config.workflow_mode or "unknown"))
    print("Target parameter: " .. (session_config.target_parameter or "unknown"))
    print("Parameter value: " .. (session_config.parameter_value or "unknown"))
    print("Session ID: " .. (session_config.session_id or "unknown"))

    -- Signal automation starting
    create_beacon_file("STARTED", "Automation system initialized - Session " .. (session_config.session_id or "unknown"), "main.lua")

    if session_config.workflow_mode == "full" then
        run_full_workflow(session_config)
    else
        create_beacon_file("ERROR", "Unknown workflow mode: " .. (session_config.workflow_mode or "none"), "main.lua")
    end
end

main()
