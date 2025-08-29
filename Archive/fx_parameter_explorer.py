#!/usr/bin/env python3
"""
FX Parameter Explorer - Test different ways to access FX parameters in reapy
"""

import reapy_boost as reapy
import sys

def explore_fx_parameter_methods(fx, param_index=0):
    """Explore all possible ways to access FX parameters"""
    print(f"\n=== Exploring FX Parameter Access Methods ===")
    print(f"FX: {fx.name}")
    print(f"Testing parameter index: {param_index}")

    methods_tested = []

    # Method 1: Direct parameter object
    print("\n--- Method 1: fx.params[i] ---")
    try:
        param = fx.params[param_index]
        print(f"Parameter object: {param}")
        print(f"Parameter type: {type(param)}")

        # Try to access attributes
        attrs_to_try = ['name', 'value', 'formatted_value', 'min_value', 'max_value', 'default_value']
        for attr in attrs_to_try:
            try:
                value = getattr(param, attr, 'NOT_FOUND')
                print(f"  {attr}: {value}")
            except Exception as e:
                print(f"  {attr}: ERROR - {e}")

        methods_tested.append("fx.params[i] - partial success")
    except Exception as e:
        print(f"ERROR: {e}")
        methods_tested.append("fx.params[i] - failed")

    # Method 2: Try FX direct methods
    print("\n--- Method 2: FX direct methods ---")
    fx_methods_to_try = [
        'get_param', 'get_param_name', 'get_param_text', 'get_param_formatted',
        'param_name', 'param_value', 'param_text'
    ]

    for method_name in fx_methods_to_try:
        try:
            if hasattr(fx, method_name):
                method = getattr(fx, method_name)
                result = method(param_index)
                print(f"  {method_name}({param_index}): {result}")
                methods_tested.append(f"{method_name} - success")
            else:
                print(f"  {method_name}: NOT AVAILABLE")
        except Exception as e:
            print(f"  {method_name}({param_index}): ERROR - {e}")
            methods_tested.append(f"{method_name} - failed")

    # Method 3: Inspect all available methods/attributes
    print("\n--- Method 3: Available FX attributes/methods ---")
    fx_attrs = [attr for attr in dir(fx) if not attr.startswith('_')]
    param_related = [attr for attr in fx_attrs if 'param' in attr.lower()]
    print(f"Parameter-related attributes: {param_related}")

    # Method 4: Try to access via track
    print("\n--- Method 4: Track-based parameter access ---")
    try:
        track = fx.parent if hasattr(fx, 'parent') else None
        if track:
            print(f"Track: {track.name}")
            # Try track-based parameter access
            track_methods = [attr for attr in dir(track) if 'param' in attr.lower()]
            print(f"Track parameter methods: {track_methods}")
        else:
            print("No parent track found")
    except Exception as e:
        print(f"Track access error: {e}")

    print(f"\n=== Summary ===")
    print("Methods tested:")
    for method in methods_tested:
        print(f"  - {method}")

    return methods_tested

def main():
    """Main exploration function"""
    print("=== FX Parameter Explorer ===")

    try:
        with reapy.inside_reaper():
            print("✓ Connected to REAPER")

            project = reapy.Project()
            print(f"Project: {project.name or 'Untitled'}")

            if len(project.tracks) == 0:
                print("No tracks found!")
                return

            # Find first track with FX
            fx_found = None
            track_with_fx = None

            for track in project.tracks:
                if len(track.fxs) > 0:
                    fx_found = track.fxs[0]
                    track_with_fx = track
                    break

            if not fx_found:
                print("No FX found on any track!")
                return

            print(f"Found FX: {fx_found.name} on track: {track_with_fx.name}")
            print(f"Parameter count: {fx_found.n_params}")

            # Explore parameter access methods
            methods = explore_fx_parameter_methods(fx_found, 0)

            # Try a few more parameter indices if available
            if fx_found.n_params > 1:
                print(f"\n=== Testing parameter index 1 ===")
                explore_fx_parameter_methods(fx_found, 1)

            print("\n=== Exploration Complete ===")

    except Exception as e:
        print(f"ERROR: {e}")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
