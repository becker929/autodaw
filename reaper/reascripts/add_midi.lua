-- add_midi.lua - Add MIDI notes to track items
reaper.ShowConsoleMsg("add_midi.lua starting...\n")

function print(val)
    reaper.ShowConsoleMsg(tostring(val) .. "\n")
end

function main()
    local track = reaper.GetTrack(0, 0)
    if not track then
        reaper.ShowMessageBox("No tracks found in project", "Error", 0)
        return
    end

    -- Check if track has any MIDI items
    local item_count = reaper.CountTrackMediaItems(track)
    local midi_item = nil

    if item_count == 0 then
        print("No items found, creating new MIDI item...")

        -- Create new MIDI item
        local item_start = 0.0
        local item_length = 4.0  -- 4 seconds
        midi_item = reaper.CreateNewMIDIItemInProj(track, item_start, item_start + item_length, false)

        if not midi_item then
            reaper.ShowMessageBox("Failed to create MIDI item", "Error", 0)
            return
        end
    else
        -- Use the first item and check if it's MIDI
        midi_item = reaper.GetTrackMediaItem(track, 0)
        local take = reaper.GetActiveTake(midi_item)

        if not take or not reaper.TakeIsMIDI(take) then
            print("First item is not MIDI, creating new MIDI item...")
            local item_start = reaper.GetMediaItemInfo_Value(midi_item, "D_POSITION") + reaper.GetMediaItemInfo_Value(midi_item, "D_LENGTH")
            local item_length = 4.0
            midi_item = reaper.CreateNewMIDIItemInProj(track, item_start, item_start + item_length, false)

            if not midi_item then
                reaper.ShowMessageBox("Failed to create MIDI item", "Error", 0)
                return
            end
        end
    end

    -- Get the MIDI take
    local take = reaper.GetActiveTake(midi_item)
    if not take or not reaper.TakeIsMIDI(take) then
        reaper.ShowMessageBox("Could not get MIDI take", "Error", 0)
        return
    end

    print("Adding MIDI notes to item...")

        -- Read session config for MIDI configuration
    local config_file = "automation_config.txt"
    local session_id = "unknown"
    local output_dir = "outputs"
    local midi_config_file = nil

    local file = io.open(config_file, "r")
    if file then
        for line in file:lines() do
            local key, value = line:match("^([^=]+)=(.*)$")
            if key == "session_id" then
                session_id = value
            elseif key == "output_dir" then
                output_dir = value
            elseif key == "midi_config" then
                midi_config_file = value
            end
        end
        file:close()
    end

    -- Documentation
    local timestamp = os.date("%Y%m%d_%H%M%S")
    local doc_file = io.open(output_dir .. "/midi_notes_session" .. session_id .. "_" .. timestamp .. ".txt", "w")
    doc_file:write("MIDI Notes Added - Session " .. session_id .. "\n")
    doc_file:write("Timestamp: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
    doc_file:write(string.rep("=", 50) .. "\n\n")

        -- Load MIDI files from configuration
    local midi_files = {}
    local files_loaded = 0

    -- Try to load MIDI configuration from JSON file
    if midi_config_file and io.open(midi_config_file, "r") then
        print("Loading MIDI configuration from: " .. midi_config_file)
        local json_content = ""
        local json_file = io.open(midi_config_file, "r")
        if json_file then
            json_content = json_file:read("*all")
            json_file:close()

            -- Simple JSON parsing for MIDI files
            -- Look for midi_files array in the JSON
            local files_start = string.find(json_content, '"midi_files"%s*:%s*%[')
            if files_start then
                local files_section = string.sub(json_content, files_start)
                local files_end = string.find(files_section, '%]')
                if files_end then
                    local files_json = string.sub(files_section, 1, files_end)
                    -- Extract individual file paths
                    for file_path in string.gmatch(files_json, '"([^"]+%.mid[i]?)"') do
                        table.insert(midi_files, file_path)
                    end
                end
            end
        end
    end

    -- Load MIDI files into the track
    if #midi_files > 0 then
        print("Loading " .. #midi_files .. " MIDI files...")

        for i, midi_file in ipairs(midi_files) do
            print("Loading MIDI file: " .. midi_file)

            -- Check if file exists
            local file_test = io.open(midi_file, "r")
            if file_test then
                file_test:close()

                -- Insert MIDI file using REAPER API
                local success = reaper.InsertMedia(midi_file, 0)  -- 0 = insert at cursor position

                if success > 0 then
                    files_loaded = files_loaded + 1
                    doc_file:write(string.format("MIDI File %d: %s - SUCCESS\n", i, midi_file))
                    print("Successfully loaded: " .. midi_file)
                else
                    doc_file:write(string.format("MIDI File %d: %s - FAILED\n", i, midi_file))
                    print("Failed to load: " .. midi_file)
                end
            else
                doc_file:write(string.format("MIDI File %d: %s - FILE NOT FOUND\n", i, midi_file))
                print("File not found: " .. midi_file)
            end
        end
    else
        print("No MIDI files specified in configuration")
        doc_file:write("No MIDI files specified in configuration\n")
    end

    doc_file:write(string.format("\nTotal MIDI files loaded: %d/%d\n", files_loaded, #midi_files))
    doc_file:close()

    print(string.format("Loaded %d MIDI files. Documented in: midi_notes_session%s_%s.txt", files_loaded, session_id, timestamp))

    -- Update project
    reaper.UpdateArrange()
end

main()
