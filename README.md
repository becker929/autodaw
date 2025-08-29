evolver
audio agent

The basic flow is this:
- evolver creates ReaScripts in Lua (reliable + familiar option)
- evolver starts Reaper
- Reaper executes its __startup.lua (at '/Users/anthonybecker/Library/Application Support/REAPER/Scripts/__startup.lua')
- __startup.lua calls main.lua, which calls the ReaScripts for the session
- the ReaScripts control Reaper to produce audio

Notes for agent:
- You'll need to create and organize artefacts e.g. .txt files and .wav files to document activity within Reaper
