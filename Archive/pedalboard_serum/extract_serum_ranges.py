#!/usr/bin/env python3
"""
Extract detailed parameter range information from Serum VST using pedalboard
"""
import pedalboard
from pedalboard import load_plugin
import os
import json
from typing import Dict, Any, List, Optional

def extract_parameter_info(param_obj) -> Dict[str, Any]:
    """Extract detailed information from an AudioProcessorParameter object"""
    info = {
        'type': type(param_obj).__name__,
        'current_value': None,
        'raw_value': None,
        'range_min': None,
        'range_max': None,
        'range_step': None,
        'is_discrete': None,
        'label': None,
        'units': None,
        'string_value': None,
        'full_repr': str(param_obj)
    }

    try:
        # Try to get common AudioProcessorParameter attributes
        if hasattr(param_obj, 'raw_value'):
            info['raw_value'] = float(param_obj.raw_value)

        if hasattr(param_obj, 'range'):
            range_info = param_obj.range
            if hasattr(range_info, 'start'):
                info['range_min'] = float(range_info.start)
            if hasattr(range_info, 'end'):
                info['range_max'] = float(range_info.end)
            if hasattr(range_info, 'interval'):
                info['range_step'] = float(range_info.interval)

        # Alternative ways to get range info
        if hasattr(param_obj, 'min_value'):
            info['range_min'] = float(param_obj.min_value)
        if hasattr(param_obj, 'max_value'):
            info['range_max'] = float(param_obj.max_value)
        if hasattr(param_obj, 'step_size'):
            info['range_step'] = float(param_obj.step_size)

        if hasattr(param_obj, 'is_discrete'):
            info['is_discrete'] = bool(param_obj.is_discrete)

        if hasattr(param_obj, 'label'):
            info['label'] = str(param_obj.label)

        if hasattr(param_obj, 'units'):
            info['units'] = str(param_obj.units)

        # Try to get the formatted string value
        try:
            info['string_value'] = str(param_obj.value) if hasattr(param_obj, 'value') else None
        except:
            pass

        # Try to get current numeric value
        try:
            if hasattr(param_obj, '__float__'):
                info['current_value'] = float(param_obj)
            elif hasattr(param_obj, 'value') and isinstance(param_obj.value, (int, float)):
                info['current_value'] = float(param_obj.value)
        except:
            pass

    except Exception as e:
        info['extraction_error'] = str(e)

    return info

def is_interesting_parameter(param_name: str) -> bool:
    """Determine if a parameter is worth detailed analysis"""
    # Skip generic MIDI CC parameters
    if param_name.startswith('cc') and param_name.endswith(('_chan_1', '_chan_2', '_chan_3', '_chan_4',
                                                            '_chan_5', '_chan_6', '_chan_7', '_chan_8',
                                                            '_chan_9', '_chan_10', '_chan_11', '_chan_12',
                                                            '_chan_13', '_chan_14', '_chan_15', '_chan_16')):
        return False

    # Skip other generic MIDI parameters
    generic_patterns = ['aftertouch_chan_', 'pitch_bend_chan_', 'velocity_chan_']
    if any(param_name.startswith(pattern) for pattern in generic_patterns):
        return False

    # Include parameters that seem VST-specific or musically relevant
    interesting_patterns = [
        'osc', 'filter', 'env', 'lfo', 'fx', 'reverb', 'delay', 'distortion',
        'chorus', 'phaser', 'flanger', 'eq', 'compressor', 'gate', 'arpeggiator',
        'sequencer', 'mod', 'macro', 'preset', 'wavetable', 'sub', 'noise',
        'unison', 'detune', 'pitch', 'bend', 'portamento', 'glide', 'vol', 'pan',
        'warp', 'wtpos', 'mastervol', '_a_', '_b_', 'verb', 'spin'
    ]

    param_lower = param_name.lower()
    if any(pattern in param_lower for pattern in interesting_patterns):
        return True

    # Include short parameter names (likely not generic)
    if len(param_name) <= 12 and not param_name.isdigit():
        return True

    return False

def extract_serum_ranges(vst_path: str, max_params: int = 100) -> Dict[str, Any]:
    """Extract detailed parameter range information from Serum"""
    print(f"Analyzing VST ranges: {vst_path}")
    print("=" * 60)

    metadata = {
        'vst_path': vst_path,
        'basic_info': {},
        'parameter_ranges': {},
        'statistics': {
            'total_parameters': 0,
            'analyzed_parameters': 0,
            'parameters_with_ranges': 0,
            'discrete_parameters': 0,
            'continuous_parameters': 0
        }
    }

    try:
        # Load the VST plugin
        plugin = load_plugin(vst_path)

        # Basic plugin information
        metadata['basic_info'] = {
            'name': getattr(plugin, 'name', 'Unknown'),
            'type': type(plugin).__name__,
            'version': getattr(plugin, 'version', 'Unknown'),
            'category': getattr(plugin, 'category', 'Unknown')
        }

        print(f"Plugin: {metadata['basic_info']['name']} v{metadata['basic_info']['version']}")

        # Process parameters
        if hasattr(plugin, 'parameters'):
            param_items = list(plugin.parameters.items())
            metadata['statistics']['total_parameters'] = len(param_items)
            print(f"Total Parameters: {len(param_items)}")

            # Analyze interesting parameters (up to max_params)
            analyzed_count = 0
            for param_name, param_obj in param_items:
                if analyzed_count >= max_params:
                    break

                if is_interesting_parameter(param_name):
                    try:
                        param_info = extract_parameter_info(param_obj)
                        metadata['parameter_ranges'][param_name] = param_info
                        analyzed_count += 1

                        # Update statistics
                        if param_info.get('range_min') is not None and param_info.get('range_max') is not None:
                            metadata['statistics']['parameters_with_ranges'] += 1

                        if param_info.get('is_discrete'):
                            metadata['statistics']['discrete_parameters'] += 1
                        else:
                            metadata['statistics']['continuous_parameters'] += 1

                        print(f"  {param_name}: {param_info.get('range_min', '?')} - {param_info.get('range_max', '?')} "
                              f"(current: {param_info.get('string_value', param_info.get('current_value', '?'))})")

                    except Exception as e:
                        print(f"  Error analyzing {param_name}: {e}")

            metadata['statistics']['analyzed_parameters'] = analyzed_count
            print(f"Analyzed {analyzed_count} interesting parameters")

        return metadata

    except Exception as e:
        print(f"Error loading VST: {e}")
        metadata['load_error'] = str(e)
        return metadata

def main():
    print("Pedalboard version:", pedalboard.__version__)
    print()

    # Focus on the working VST3 version
    serum_path = "/Library/Audio/Plug-Ins/VST3/Serum.vst3"

    if not os.path.exists(serum_path):
        print(f"VST not found: {serum_path}")
        return

    # Extract detailed range information
    metadata = extract_serum_ranges(serum_path, max_params=200)  # Analyze more parameters

    # Save detailed range information
    output_file = "serum_parameter_ranges.json"
    with open(output_file, "w") as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"\nDetailed range information saved to: {output_file}")

    # Create a summary of ranges
    if metadata['parameter_ranges']:
        print(f"\nRange Summary:")
        print(f"  Parameters with defined ranges: {metadata['statistics']['parameters_with_ranges']}")
        print(f"  Discrete parameters: {metadata['statistics']['discrete_parameters']}")
        print(f"  Continuous parameters: {metadata['statistics']['continuous_parameters']}")

        # Show some example ranges
        print(f"\nExample Parameter Ranges:")
        count = 0
        for param_name, info in metadata['parameter_ranges'].items():
            if count >= 10:  # Show first 10 examples
                break
            if info.get('range_min') is not None and info.get('range_max') is not None:
                range_str = f"{info['range_min']} to {info['range_max']}"
                if info.get('range_step'):
                    range_str += f" (step: {info['range_step']})"
                current_str = info.get('string_value', info.get('current_value', 'unknown'))
                print(f"  {param_name}: {range_str} | Current: {current_str}")
                count += 1

if __name__ == "__main__":
    main()
