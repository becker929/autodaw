-- main_v2.lua - Improved ReaScript controller with structured communication
reaper.ShowConsoleMsg("main_v2.lua starting...\n")

function print(val)
    reaper.ShowConsoleMsg(tostring(val) .. "\n")
end

-- Configuration
local config = {
    script_dir = "/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/reascripts/",
    config_file = "/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/automation_config.txt"
}

function create_beacon_file(status, message, script_name, progress, data)
    local beacon_path = "/Users/anthonybecker/Desktop/reaper_automation_beacon.txt"
    local file = io.open(beacon_path, "w")
    if file then
        file:write("timestamp=" .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
        file:write("status=" .. status .. "\n")
        file:write("script=" .. (script_name or "main_v2.lua") .. "\n")
        file:write("message=" .. (message or "") .. "\n")
        file:write("session_id=" .. (session_config and session_config.session_id or "unknown") .. "\n")
        file:write("progress=" .. (progress or 0.0) .. "\n")
        
        if data then
            -- Simple JSON-like data encoding
            file:write("data=" .. data .. "\n")
        end
        
        file:close()
        print("Beacon updated: " .. status)
    else
        print("ERROR: Could not create beacon file")
    end
end

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

function run_workflow_step(script_name, step_number, total_steps, description)
    local script_path = config.script_dir .. script_name
    local progress = (step_number - 1) / total_steps
    
    print("Step " .. step_number .. "/" .. total_steps .. ": " .. description)
    create_beacon_file("RUNNING", "Step " .. step_number .. "/" .. total_steps .. ": " .. description, script_name, progress)
    
    -- Check if script file exists
    local file = io.open(script_path, "r")
    if not file then
        print("ERROR: Script file not found: " .. script_path)
        create_beacon_file("ERROR", "Script file not found: " .. script_path, script_name, progress)
        return false
    end
    file:close()
    
    -- Execute the script with error handling
    local success, error_msg = pcall(dofile, script_path)
    
    if success then
        local completion_progress = step_number / total_steps
        create_beacon_file("RUNNING", "Step " .. step_number .. " completed", script_name, completion_progress)
        print("Step " .. step_number .. " completed successfully")
        return true
    else
        create_beacon_file("ERROR", "Step " .. step_number .. " failed: " .. tostring(error_msg), script_name, progress)
        print("Step " .. step_number .. " failed: " .. tostring(error_msg))
        return false
    end
end

function run_full_workflow(session_config)
    print("Running full workflow for session " .. (session_config.session_id or "unknown"))
    print("Workflow mode: " .. (session_config.workflow_mode or "unknown"))
    
    local workflow_steps = {
        {"get_params.lua", "Getting VST parameters"},
        {"change_params_octave.lua", "Changing target parameter to " .. (session_config.parameter_value or "0.0")},
        {"add_midi.lua", "Adding MIDI notes"},
        {"render_audio.lua", "Rendering audio output"}
    }
    
    -- Execute each workflow step
    for i, step in ipairs(workflow_steps) do
        local script_name, description = step[1], step[2]
        
        local success = run_workflow_step(script_name, i, #workflow_steps, description)
        if not success then
            create_beacon_file("ERROR", "Workflow failed at step " .. i .. ": " .. description, "main_v2.lua")
            return false
        end
    end
    
    -- Workflow completed successfully
    create_beacon_file("COMPLETED", "Full workflow completed for session " .. (session_config.session_id or "unknown"), "main_v2.lua", 1.0)
    return true
end

function run_discovery_workflow(session_config)
    print("Running parameter discovery workflow")
    
    local success = run_workflow_step("parameter_discovery.lua", 1, 1, "Discovering VST parameters")
    
    if success then
        create_beacon_file("COMPLETED", "Parameter discovery completed", "main_v2.lua", 1.0)
    else
        create_beacon_file("ERROR", "Parameter discovery failed", "main_v2.lua")
    end
    
    return success
end

function run_single_script_workflow(script_name, session_config)
    print("Running single script: " .. script_name)
    
    local success = run_workflow_step(script_name, 1, 1, "Executing " .. script_name)
    
    if success then
        create_beacon_file("COMPLETED", "Script " .. script_name .. " completed", "main_v2.lua", 1.0)
    else
        create_beacon_file("ERROR", "Script " .. script_name .. " failed", "main_v2.lua")
    end
    
    return success
end

-- Global session config for beacon file access
session_config = nil

-- Main execution
function main()
    print("Reading automation configuration...")
    session_config = read_config()
    
    if not session_config then
        create_beacon_file("ERROR", "Could not read configuration file", "main_v2.lua")
        return
    end
    
    print("Configuration loaded:")
    print("  Workflow mode: " .. (session_config.workflow_mode or "unknown"))
    print("  Target parameter: " .. (session_config.target_parameter or "unknown"))
    print("  Parameter value: " .. (session_config.parameter_value or "unknown"))
    print("  Session ID: " .. (session_config.session_id or "unknown"))
    print("  Output directory: " .. (session_config.output_dir or "unknown"))

    -- Signal automation starting
    create_beacon_file("STARTED", "Automation system initialized - Session " .. (session_config.session_id or "unknown"), "main_v2.lua")

    -- Route to appropriate workflow
    local workflow_mode = session_config.workflow_mode or "full"
    local success = false
    
    if workflow_mode == "full" then
        success = run_full_workflow(session_config)
    elseif workflow_mode == "discovery" then
        success = run_discovery_workflow(session_config)
    elseif workflow_mode == "single" then
        local target_script = session_config.target_script or "get_params.lua"
        success = run_single_script_workflow(target_script, session_config)
    else
        create_beacon_file("ERROR", "Unknown workflow mode: " .. workflow_mode, "main_v2.lua")
        return
    end
    
    if success then
        print("Workflow completed successfully")
    else
        print("Workflow failed")
    end
end

main()
