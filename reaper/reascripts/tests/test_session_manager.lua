-- test_session_manager.lua - Tests for session management functionality

local test_runner = require("tests.test_runner")

-- Set up reaper mocks before any modules are loaded
reaper = {
    ShowConsoleMsg = function(msg) print(msg:gsub("\n$", "")) end,
    GetProjectPath = function() return "/test/project" end,
    CountTracks = function() return 1 end,
    InsertTrackAtIndex = function() end,
    GetTrack = function(proj, idx)
        if idx == 0 then
            return {track_id = idx}  -- Return a valid track object
        end
        return nil
    end,
    TrackFX_AddByName = function() return 0 end,
    TrackFX_SetParam = function() end,
    InsertMedia = function() return {media_item = true} end,  -- Return valid media item
    GetSetProjectInfo = function() end,
    GetSetProjectInfo_String = function() end,
    GetSetMediaTrackInfo_String = function() end,
    Main_OnCommand = function() end,
    SelectAllMediaItems = function() end,
    DeleteTrack = function() end
}

local function run_tests()

    test_runner.describe("Session Manager Loading", function()
        local session_manager = require("lib.session_manager")
        test_runner.assert_not_nil(session_manager, "Session manager module should load")
        test_runner.assert_type("function", session_manager.load_session, "load_session should be a function")
        test_runner.assert_type("function", session_manager.validate_session, "validate_session should be a function")
        test_runner.assert_type("function", session_manager.execute_session, "execute_session should be a function")
    end)

    test_runner.describe("Session Validation", function()
        local session_manager = require("lib.session_manager")

        -- Test valid session structure
        local valid_session = {
            session_name = "test",
            render_configs = {
                {
                    render_id = "test_render",
                    tracks = {},
                    parameters = {},
                    midi_files = {}
                }
            }
        }

        test_runner.assert_true(pcall(function()
            session_manager.validate_session(valid_session)
        end), "Should validate correct session structure")

        -- Test invalid session structure - missing session_name
        local invalid_session1 = {
            render_configs = {
                {
                    render_id = "test_render",
                    tracks = {},
                    parameters = {},
                    midi_files = {}
                }
            }
        }

        test_runner.assert_false(pcall(function()
            session_manager.validate_session(invalid_session1)
        end), "Should fail validation for missing session_name")

        -- Test invalid session structure - missing render_configs
        local invalid_session2 = {
            session_name = "test",
        }

        test_runner.assert_false(pcall(function()
            session_manager.validate_session(invalid_session2)
        end), "Should fail validation for missing render_configs")

        -- Test invalid session structure - empty render_configs
        local invalid_session3 = {
            session_name = "test",
            render_configs = {}
        }

        test_runner.assert_false(pcall(function()
            session_manager.validate_session(invalid_session3)
        end), "Should fail validation for empty render_configs")
    end)

    test_runner.describe("Track Setup", function()
        local session_manager = require("lib.session_manager")

        local tracks_config = {
            {
                index = 0,
                name = "Test Track",
                fx_chain = {
                    {
                        name = "TestFX",
                        plugin_name = "TestPlugin"
                    }
                }
            }
        }

        local success, error_msg = pcall(function()
            session_manager.setup_tracks(tracks_config)
        end)

        if not success then
            test_runner.print("Track Setup Error: " .. tostring(error_msg))
        end

        test_runner.assert_true(success, "Should set up tracks without error")
    end)

    test_runner.describe("MIDI File Loading", function()
        local session_manager = require("lib.session_manager")

        -- Mock file_exists to return true for test
        local utils = require("lib.utils")
        local original_file_exists = utils.file_exists
        utils.file_exists = function() return true end

        local midi_files_config = {
            ["0"] = "test.mid"
        }

        local success, error_msg = pcall(function()
            session_manager.load_midi_files(midi_files_config)
        end)

        if not success then
            test_runner.print("MIDI File Loading Error: " .. tostring(error_msg))
        end

        test_runner.assert_true(success, "Should load MIDI files without error")

        -- Restore original function
        utils.file_exists = original_file_exists
    end)

    test_runner.describe("Render Config Execution", function()
        local session_manager = require("lib.session_manager")
        local utils = require("lib.utils")

        -- Mock file_exists to return true for test
        local original_file_exists = utils.file_exists
        local original_ensure_dir = utils.ensure_dir
        utils.file_exists = function() return true end
        utils.ensure_dir = function() return true, nil end

        local render_config = {
            render_id = "test_render",
            tracks = {
                {
                    index = 0,
                    name = "Test Track",
                    fx_chain = {
                        {
                            name = "TestFX",
                            plugin_name = "TestPlugin"
                        }
                    }
                }
            },
            parameters = {},
            midi_files = {
                ["0"] = "test.mid"
            },
            render_options = {}
        }

        local success, error_msg = pcall(function()
            session_manager.execute_render_config("test_session", render_config)
        end)

        if not success then
            test_runner.print("Render Config Execution Error: " .. tostring(error_msg))
        end

        test_runner.assert_true(success, "Should execute render config without error")

        -- Restore original functions
        utils.file_exists = original_file_exists
        utils.ensure_dir = original_ensure_dir
    end)
end

return {
    run_tests = run_tests
}
