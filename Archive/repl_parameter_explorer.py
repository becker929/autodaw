# Run this first to set up the connection:
import reapy_boost as reapy
context = reapy.inside_reaper()
context.__enter__()
project = reapy.Project()
track = project.tracks[0]
fx = track.fxs[0]
print(f'FX: {fx.name}, Parameters: {fx.n_params}')
