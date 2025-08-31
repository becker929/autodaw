-- constants.lua - Centralized constants for the ReaScript system

local constants = {}

-- Directory paths (relative to project root)
constants.SESSION_CONFIGS_DIR = "session-configs"
constants.SESSION_RESULTS_DIR = "session-results"
constants.RENDERS_DIR = "renders"

-- Default render settings
constants.DEFAULT_SAMPLE_RATE = 44100
constants.DEFAULT_CHANNELS = 2
constants.DEFAULT_RENDER_FORMAT = ""
constants.DEFAULT_RENDER_BOUNDS_FLAG = 1  -- Entire project

-- File naming patterns
constants.RENDER_FILENAME_PATTERN = "%s_%s_%s_%s"  -- session_name, render_id, timestamp, base_name
constants.TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

-- Default session values
constants.DEFAULT_SESSION_NAME = "default_session"
constants.DEFAULT_RENDER_ID = "render"

-- MIDI file extensions
constants.MIDI_EXTENSIONS = {".mid", ".midi"}

-- Error messages
constants.ERROR_SESSION_NOT_FOUND = "Session file not found"
constants.ERROR_INVALID_JSON = "Invalid JSON format"
constants.ERROR_MISSING_RENDER_CONFIGS = "No render configs found in session"
constants.ERROR_TRACK_SETUP_FAILED = "Track setup failed"
constants.ERROR_PARAMETER_APPLICATION_FAILED = "Parameter application failed"
constants.ERROR_MIDI_LOAD_FAILED = "MIDI file loading failed"
constants.ERROR_RENDER_FAILED = "Render operation failed"

return constants
