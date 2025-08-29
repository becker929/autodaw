# REAPER Automated Audio Rendering System

A complete system for automated audio production using REAPER with Lua ReaScripts and Python orchestration.

## System Components

### 1. Python Entry Point (`main.py`)
- Manages REAPER application lifecycle (start/stop)
- Orchestrates automation workflows
- Handles project file loading
- Usage: `uv run main.py workflow` or `uv run main.py single <script> [project]`

### 2. Lua ReaScripts (`reascripts/`)
- **`main.lua`**: Central controller that determines which script to run
- **`get_params.lua`**: Extracts VST parameters and saves to file
- **`change_params.lua`**: Modifies VST parameters and documents changes
- **`add_midi.lua`**: Adds MIDI notes to track items
- **`render_audio.lua`**: Renders project audio to WAV files

### 3. Audio Validation (`audio_validator.py`)
- Uses librosa to analyze rendered audio files
- Validates that audio content was actually produced
- Generates detailed analysis reports
- Usage: `uv run audio_validator.py`

### 4. REAPER Startup Integration
- `__startup.lua` in REAPER Scripts folder calls our `main.lua`
- Enables automatic execution when REAPER starts

## Workflow

1. Python `main.py` starts REAPER with specified project
2. REAPER executes `__startup.lua` which calls `main.lua`
3. `main.lua` runs the configured ReaScript (get_params, change_params, add_midi, or render_audio)
4. Each script documents its actions to text files on Desktop
5. Python stops REAPER and can run audio validation
6. Process repeats for different scripts/projects

## File Outputs

All automation generates documentation files on Desktop:
- `params_*.txt`: Parameter extraction results
- `param_changes_*.txt`: Parameter modification logs
- `midi_notes_*.txt`: MIDI note addition logs
- `render_log_*.txt`: Audio rendering logs
- `rendered_audio_*.wav`: Actual audio output
- `audio_validation_*.json`: Audio analysis reports

## Dependencies

Install with: `uv sync`
- librosa: Audio analysis
- numpy: Numerical operations
- reapy-boost: REAPER Python integration (optional)
- rpp: REAPER project file parsing (optional)

## Quick Start

```bash
# Run full automation workflow
uv run main.py workflow

# Run single automation
uv run main.py single get_params.lua data/serum/serum1.RPP

# Validate recent audio files
uv run audio_validator.py
```

This system provides a complete skeleton for automated audio production with parameter manipulation, MIDI generation, audio rendering, and validation.
