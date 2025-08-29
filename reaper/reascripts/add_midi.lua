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

        -- Read session config for filename
    local config_file = "/Users/anthonybecker/Desktop/tmsmsm/autodaw/reaper/automation_config.txt"
    local session_id = "unknown"
    local output_dir = "/Users/anthonybecker/Desktop"

    local file = io.open(config_file, "r")
    if file then
        for line in file:lines() do
            local key, value = line:match("^([^=]+)=(.*)$")
            if key == "session_id" then
                session_id = value
            elseif key == "output_dir" then
                output_dir = value
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

    -- Define some notes to add (C major scale pattern)
    local notes = {
        {pitch = 60, start = 0.0, length = 0.5, velocity = 80},   -- C4
        {pitch = 62, start = 0.5, length = 0.5, velocity = 75},   -- D4
        {pitch = 64, start = 1.0, length = 0.5, velocity = 85},   -- E4
        {pitch = 65, start = 1.5, length = 0.5, velocity = 70},   -- F4
        {pitch = 67, start = 2.0, length = 0.5, velocity = 90},   -- G4
        {pitch = 69, start = 2.5, length = 0.5, velocity = 78},   -- A4
        {pitch = 71, start = 3.0, length = 0.5, velocity = 82},   -- B4
        {pitch = 72, start = 3.5, length = 0.5, velocity = 88}    -- C5
    }

        local notes_added = 0

    for i, note in ipairs(notes) do
        -- Convert time to PPQ position using REAPER API
        local start_ppq = reaper.MIDI_GetPPQPosFromProjTime(take, note.start)
        local end_ppq = reaper.MIDI_GetPPQPosFromProjTime(take, note.start + note.length)

        -- Insert the note (channel 0, not selected, not muted)
        local success = reaper.MIDI_InsertNote(take, false, false, start_ppq, end_ppq, 0, note.pitch, note.velocity, true)

        if success then
            notes_added = notes_added + 1
            local note_name = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"}
            local note_octave = math.floor(note.pitch / 12) - 1
            local note_letter = note_name[(note.pitch % 12) + 1]
            local full_note_name = note_letter .. note_octave

            local log_entry = string.format(
                "Note %d: %s (MIDI %d)\n" ..
                "  Start: %.2f sec (PPQ: %.0f)\n" ..
                "  Length: %.2f sec\n" ..
                "  Velocity: %d\n" ..
                "  Success: YES\n\n",
                i, full_note_name, note.pitch,
                note.start, start_ppq,
                note.length, note.velocity
            )

            doc_file:write(log_entry)
            print("Added note: " .. full_note_name .. " at " .. note.start .. "s")
        else
            doc_file:write(string.format("Note %d: FAILED to add MIDI %d\n\n", i, note.pitch))
            print("Failed to add note: " .. note.pitch)
        end
    end

    -- Sort MIDI events
    reaper.MIDI_Sort(take)

    doc_file:write(string.format("Total notes added: %d/%d\n", notes_added, #notes))
    doc_file:close()

    print(string.format("Added %d MIDI notes. Documented in: midi_notes_session%s_%s.txt", notes_added, session_id, timestamp))

    -- Update project
    reaper.UpdateArrange()
end

main()
