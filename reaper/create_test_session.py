#!/usr/bin/env python3
"""
Create a test session configuration with randomized parameters and generated MIDI.
This demonstrates the complete workflow for automated audio generation.
"""

import sys
import random
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    SessionConfig, ConfigManager, MIDIConfig, RenderConfig,
    SERUM_PARAMETERS, DualOutputLogger
)


def create_randomized_session(session_name: str, num_renders: int = 5,
                            project_file: str = None, seed: int = None) -> SessionConfig:
    """Create a session config with randomized parameters per render."""

    if seed is not None:
        random.seed(seed)

    # Create session - use consistent output directory
    config = SessionConfig(
        session_name=session_name,
        project_file=project_file,
        output_directory="./outputs"
    )

    # Add metadata
    config.metadata = {
        "description": "Test session with randomized Serum parameters",
        "num_renders": num_renders,
        "seed": seed,
        "parameter_ranges": "Serum oscillator, filter, and envelope parameters"
    }

        # Key parameters to randomize with extreme values for audible differences
    key_parameters = [
        "osc_a_octave",      # Use full range: -2.0 to 2.0 (4 octave span)
        "filter_cutoff",     # Use full range: 0.0 to 1.0 (dramatic filter changes)
        "filter_resonance",  # Use full range: 0.0 to 1.0 (resonance sweep)
        "amp_attack",        # Use 0.0 to 10.0 (fast to slow attacks)
        "amp_release",       # Use 0.1 to 15.0 (short to long releases)
    ]

    print(f"Creating {num_renders} renders with randomized parameters:")
    print(f"Parameters: {', '.join(key_parameters)}")

    # Generate renders with randomized parameters
    for i in range(num_renders):
        render_name = f"render_{i+1:03d}"
        render = RenderConfig(
            name=render_name,
            render_length=30.0,  # 30 second renders
            render_quality="high"
        )

                # Randomize each parameter with extreme values for audible differences
        param_values = {}
        for param_name in key_parameters:
            # Use custom ranges for more dramatic differences
            if param_name == "osc_a_octave":
                value = random.uniform(-2.0, 2.0)  # 4 octave range
            elif param_name == "filter_cutoff":
                value = random.choice([0.1, 0.3, 0.5, 0.7, 0.9])  # Discrete steps
            elif param_name == "filter_resonance":
                value = random.choice([0.0, 0.4, 0.8])  # Low, medium, high
            elif param_name == "amp_attack":
                value = random.choice([0.0, 2.0, 8.0])  # Fast, medium, slow
            elif param_name == "amp_release":
                value = random.choice([0.1, 3.0, 12.0])  # Short, medium, long
            else:
                # Fallback to SERUM_PARAMETERS if defined
                if param_name in SERUM_PARAMETERS:
                    param_spec = SERUM_PARAMETERS[param_name]
                    value = random.uniform(param_spec["min"], param_spec["max"])
                else:
                    value = random.uniform(0.0, 1.0)

            render.add_parameter(param_name, value)
            param_values[param_name] = value

        # Set custom output filename with parameter info
        octave_val = param_values.get("osc_a_octave", 0)
        cutoff_val = param_values.get("filter_cutoff", 0.5)
        render.output_filename = f"{render_name}_oct{octave_val:.1f}_cut{cutoff_val:.2f}.wav"

        config.add_render(render)

        # Print render info
        print(f"  {render_name}:")
        for param_name, value in param_values.items():
            print(f"    {param_name}: {value:.3f}")

    return config


def generate_midi_files(session_name: str, count: int = 3) -> list:
    """Generate multiple MIDI files for the session."""
    midi_dir = Path(f"./midi/{session_name}")
    midi_dir.mkdir(parents=True, exist_ok=True)

    midi_files = []

    # Generate different types of MIDI patterns
    patterns = [
        ("melody", "C", "major", 120),
        ("chords", "Am", "minor", 110),
        ("bass", "G", "mixolydian", 130),
    ]

    for i, (pattern_type, key, scale, tempo) in enumerate(patterns[:count]):
        midi_file = midi_dir / f"{session_name}_{pattern_type}_{key}_{scale}.mid"

        # Run the MIDI generator
        cmd = [
            "uv", "run", "python", "generate_random_midi.py",
            "--output", str(midi_file),
            "--pattern", pattern_type,
            "--key", key.replace("m", ""),  # Remove 'm' from Am
            "--scale", "minor" if "m" in key else scale,
            "--tempo", str(tempo),
            "--seed", str(random.randint(1, 1000))
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            midi_files.append(str(midi_file))
            print(f"Generated MIDI: {midi_file.name}")
        except subprocess.CalledProcessError as e:
            print(f"Error generating MIDI {midi_file}: {e}")
            print(f"Command: {' '.join(cmd)}")
            if e.stdout:
                print(f"Stdout: {e.stdout}")
            if e.stderr:
                print(f"Stderr: {e.stderr}")

    return midi_files


def main():
    """Create a complete test session with MIDI and randomized parameters."""
    session_name = "test_random_session"
    num_renders = 5
    seed = 42  # For reproducible results

    print(f"Creating test session: {session_name}")
    print(f"Seed: {seed} (for reproducible results)")
    print("=" * 60)

    # Generate MIDI files first
    print("\n1. Generating MIDI files...")
    midi_files = generate_midi_files(session_name, count=2)

    if not midi_files:
        print("Warning: No MIDI files generated, continuing without MIDI")

    # Create session config with randomized parameters
    print(f"\n2. Creating session config with {num_renders} randomized renders...")

    # Use a sample project file (user would specify their actual project)
    project_file = "data/serum/serum1.RPP"  # Assuming this exists

    config = create_randomized_session(
        session_name=session_name,
        num_renders=num_renders,
        project_file=project_file,
        seed=seed
    )

    # Add MIDI configuration
    if midi_files:
        print(f"\n3. Adding MIDI configuration ({len(midi_files)} files)...")
        midi_config = MIDIConfig()
        for midi_file in midi_files:
            try:
                midi_config.add_midi_file(midi_file)
                print(f"  Added: {Path(midi_file).name}")
            except FileNotFoundError:
                print(f"  Warning: MIDI file not found: {midi_file}")

        config.set_global_midi(midi_config)

    # Save session configuration
    print(f"\n4. Saving session configuration...")
    config_manager = ConfigManager()
    config_file = config_manager.save_session_config(config)

    print(f"Session configuration saved: {config_file}")

    # Print summary
    print(f"\n" + "=" * 60)
    print("SESSION SUMMARY")
    print("=" * 60)
    print(f"Session Name: {config.session_name}")
    print(f"Session ID: {config.session_id}")
    print(f"Project File: {config.project_file}")
    print(f"Output Directory: {config.output_directory}")
    print(f"Number of Renders: {len(config.renders)}")
    print(f"MIDI Files: {len(config.global_midi_config.midi_files) if config.global_midi_config else 0}")

    print(f"\nRender Details:")
    for i, render in enumerate(config.renders, 1):
        print(f"  {i}. {render.name} ({len(render.parameters)} parameters)")
        for param_name, param_config in render.parameters.items():
            print(f"     {param_name}: {param_config.value:.3f}")

    if config.global_midi_config and config.global_midi_config.midi_files:
        print(f"\nMIDI Files:")
        for midi_file in config.global_midi_config.midi_files:
            print(f"  - {Path(midi_file).name}")

    print(f"\nConfiguration file: {config_file}")
    print(f"\nTo use this configuration:")
    print(f"  1. Load the project file in REAPER: {config.project_file}")
    print(f"  2. Run the automation system with this config")
    print(f"  3. Check outputs in: {config.output_directory}")

    return config_file


if __name__ == "__main__":
    main()
