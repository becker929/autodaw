# REAPER ReaScripts Library

This is a modular library of Lua scripts for automating REAPER DAW tasks.

## Project Structure

```
reascripts/
├── lib/                     # Core modules
│   ├── error_handler.lua    # Error handling utilities
│   ├── fx_manager.lua       # FX parameter management
│   ├── json.lua             # JSON parsing/serialization
│   ├── project_manager.lua  # Project management utilities
│   └── utils.lua            # Common utility functions
├── clear_project.lua        # Script to clear project
├── fx_updater.lua           # Legacy script (redirects to lib modules)
├── main.lua                 # Main demonstration script
├── parameter_discovery.lua  # Script to discover and save FX parameters
├── render_project.lua       # Script to render project
├── setup_simple_project.lua # Script to set up a simple project
└── update_fx_params.lua     # Script to update FX parameters
```

## Modules

### lib/utils.lua

Common utility functions used across multiple scripts.

- File operations
- Track and FX lookup
- Console output

### lib/json.lua

JSON parsing and serialization functionality.

- Parse parameter changes from JSON
- Parse FX parameter mapping
- Encode Lua tables to JSON

### lib/fx_manager.lua

FX parameter management functionality.

- Discover FX parameters
- Load parameter mapping
- Update/get parameter values

### lib/project_manager.lua

Project management functions.

- Clear project
- Set up project
- Render project

### lib/error_handler.lua

Error handling utilities.

- Error logging
- Safe function execution
- Parameter validation

## Usage Examples

### Setting up and rendering a project

```lua
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

local project_manager = require("lib.project_manager")

-- Clear the project
project_manager.clear_project()

-- Set up a simple project
project_manager.setup_simple_project({
    fx_name = "Serum",
    track_name = "Synth"
})

-- Render the project
local render_dir = reaper.GetProjectPath("") .. "/renders"
project_manager.render_project(render_dir, "my_render")
```

### Updating FX parameters

```lua
local script_path = debug.getinfo(1, "S").source:match("@(.*/)")
package.path = script_path .. "?.lua;" .. package.path

local fx_manager = require("lib.fx_manager")
local json = require("lib.json")

-- Load parameter mapping
fx_manager.load_param_mapping()

-- Update a single parameter
fx_manager.update_single_param("Synth", "Serum", "OSC1 OCT", 0.5)

-- Update multiple parameters from JSON
local json_str = [[
{
    "paramChanges": [
        {
            "track": "Synth",
            "fx": "Serum",
            "param": "OSC1 OCT",
            "value": 0.5
        },
        {
            "track": "Synth",
            "fx": "Serum",
            "param": "OSC1 FINE",
            "value": 0.25
        }
    ]
}
]]

local params_data = json.parse_param_changes(json_str)
if params_data and params_data.paramChanges then
    fx_manager.process_param_changes(params_data.paramChanges)
end
```

## Running Scripts

The scripts can be run directly from REAPER's Actions menu or via the ReaScript development environment.

## Error Handling

The library includes comprehensive error handling. Errors are logged to the console and can be written to a file using:

```lua
local error_handler = require("lib.error_handler")
error_handler.write_log_to_file(script_path .. "error_log.txt")
```
