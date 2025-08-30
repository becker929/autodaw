#!/usr/bin/env python3
"""
Generate random MIDI files using music theory for automation sessions.
Creates 1-bar MIDI patterns with various musical styles and progressions.
"""

import sys
import random
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

try:
    import mido
    from music21 import stream, note, chord, meter, tempo, key, scale, interval, duration
except ImportError as e:
    print(f"Error: Required music libraries not installed: {e}")
    print("Install with: uv add mido music21")
    sys.exit(1)


class MIDIGenerator:
    """Generate random MIDI files using music theory."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)

        # Musical scales and modes
        self.scales = {
            'major': [0, 2, 4, 5, 7, 9, 11],
            'minor': [0, 2, 3, 5, 7, 8, 10],
            'dorian': [0, 2, 3, 5, 7, 9, 10],
            'mixolydian': [0, 2, 4, 5, 7, 9, 10],
            'pentatonic_major': [0, 2, 4, 7, 9],
            'pentatonic_minor': [0, 3, 5, 7, 10],
            'blues': [0, 3, 5, 6, 7, 10],
            'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
        }

        # Common chord progressions (in scale degrees)
        self.progressions = {
            'pop': [1, 5, 6, 4],  # I-V-vi-IV
            'jazz': [1, 6, 2, 5],  # I-vi-ii-V
            'folk': [1, 4, 5, 1],  # I-IV-V-I
            'modal': [1, 7, 4, 1],  # I-bVII-IV-I
            'minor': [1, 3, 6, 7],  # i-III-VI-VII
        }

        # Rhythm patterns (16th note grid)
        self.rhythms = {
            'straight': [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'syncopated': [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0],
            'dotted': [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
            'sparse': [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
            'dense': [1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0],
        }

    def generate_scale_notes(self, root_note: int, scale_name: str, octaves: int = 2) -> List[int]:
        """Generate notes from a scale across specified octaves."""
        scale_intervals = self.scales[scale_name]
        notes = []

        for octave in range(octaves):
            for interval in scale_intervals:
                note_num = root_note + interval + (octave * 12)
                if 0 <= note_num <= 127:  # Valid MIDI range
                    notes.append(note_num)

        return notes

    def generate_chord_progression(self, root_note: int, scale_name: str,
                                 progression_name: str) -> List[List[int]]:
        """Generate a chord progression based on scale and progression type."""
        scale_notes = self.generate_scale_notes(root_note, scale_name, 1)
        progression = self.progressions[progression_name]
        chords = []

        for degree in progression:
            # Get root of chord (scale degree - 1 for 0-indexing)
            chord_root = scale_notes[(degree - 1) % len(scale_notes)]

            # Build triad (root, third, fifth)
            chord_notes = [
                chord_root,
                scale_notes[(degree - 1 + 2) % len(scale_notes)],  # Third
                scale_notes[(degree - 1 + 4) % len(scale_notes)]   # Fifth
            ]

            chords.append(chord_notes)

        return chords

    def generate_melody(self, root_note: int, scale_name: str, num_notes: int = 8) -> List[int]:
        """Generate a random melody using scale notes."""
        scale_notes = self.generate_scale_notes(root_note, scale_name, 2)
        melody = []

        # Start near the root
        current_octave_notes = [n for n in scale_notes if root_note <= n <= root_note + 12]
        current_note = random.choice(current_octave_notes)
        melody.append(current_note)

        for _ in range(num_notes - 1):
            # Prefer stepwise motion with occasional leaps
            if random.random() < 0.7:  # 70% stepwise
                # Find nearby notes
                nearby_notes = [n for n in scale_notes if abs(n - current_note) <= 4]
                if nearby_notes:
                    current_note = random.choice(nearby_notes)
            else:  # 30% leaps
                current_note = random.choice(scale_notes)

            melody.append(current_note)

        return melody

    def create_midi_pattern(self, pattern_type: str = 'random',
                          root_note: int = 60, scale_name: str = 'major',
                          tempo_bpm: int = 120) -> mido.MidiFile:
        """Create a 1-bar MIDI pattern."""
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        # Set tempo
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo_bpm)))

        # Ticks per beat (quarter note)
        ticks_per_beat = mid.ticks_per_beat
        sixteenth_note = ticks_per_beat // 4

        if pattern_type == 'melody':
            self._create_melody_pattern(track, root_note, scale_name, sixteenth_note)
        elif pattern_type == 'chords':
            self._create_chord_pattern(track, root_note, scale_name, sixteenth_note)
        elif pattern_type == 'bass':
            self._create_bass_pattern(track, root_note, scale_name, sixteenth_note)
        elif pattern_type == 'drums':
            self._create_drum_pattern(track, sixteenth_note)
        else:  # random
            pattern_types = ['melody', 'chords', 'bass']
            chosen_type = random.choice(pattern_types)
            return self.create_midi_pattern(chosen_type, root_note, scale_name, tempo_bpm)

        return mid

    def _create_melody_pattern(self, track: mido.MidiTrack, root_note: int,
                             scale_name: str, sixteenth_note: int):
        """Create a melodic pattern."""
        melody = self.generate_melody(root_note, scale_name, 8)
        rhythm_name = random.choice(list(self.rhythms.keys()))
        rhythm = self.rhythms[rhythm_name]

        time_offset = 0
        note_on_events = []

        for i, beat in enumerate(rhythm):
            if beat and i < len(melody):
                note_num = melody[i % len(melody)]
                velocity = random.randint(60, 100)

                # Note on
                track.append(mido.Message('note_on', channel=0, note=note_num,
                                        velocity=velocity, time=time_offset))

                # Store for note off
                note_length = random.choice([sixteenth_note, sixteenth_note * 2, sixteenth_note * 3])
                note_on_events.append((note_num, note_length))
                time_offset = 0
            else:
                time_offset += sixteenth_note

        # Add note off events
        for note_num, length in note_on_events:
            track.append(mido.Message('note_off', channel=0, note=note_num,
                                    velocity=0, time=length))

    def _create_chord_pattern(self, track: mido.MidiTrack, root_note: int,
                            scale_name: str, sixteenth_note: int):
        """Create a chord pattern."""
        progression_name = random.choice(list(self.progressions.keys()))
        chords = self.generate_chord_progression(root_note, scale_name, progression_name)

        # Play chords on beats 1 and 3
        chord_times = [0, sixteenth_note * 8]  # Beat 1 and 3 of 4/4

        for i, chord_time in enumerate(chord_times):
            chord_notes = chords[i % len(chords)]
            velocity = random.randint(50, 80)

            # Chord on
            for j, note_num in enumerate(chord_notes):
                track.append(mido.Message('note_on', channel=0, note=note_num,
                                        velocity=velocity, time=chord_time if j == 0 else 0))

            # Chord off
            chord_length = sixteenth_note * 6  # Slightly overlapping
            for j, note_num in enumerate(chord_notes):
                track.append(mido.Message('note_off', channel=0, note=note_num,
                                        velocity=0, time=chord_length if j == 0 else 0))

    def _create_bass_pattern(self, track: mido.MidiTrack, root_note: int,
                           scale_name: str, sixteenth_note: int):
        """Create a bass pattern."""
        # Use lower octave
        bass_root = root_note - 24 if root_note >= 36 else root_note - 12
        scale_notes = self.generate_scale_notes(bass_root, scale_name, 1)

        # Simple bass pattern: root on 1, fifth on 3
        bass_notes = [
            scale_notes[0],  # Root
            scale_notes[4] if len(scale_notes) > 4 else scale_notes[0]  # Fifth
        ]

        times = [0, sixteenth_note * 8]  # Beat 1 and 3

        for i, (note_num, time_offset) in enumerate(zip(bass_notes, times)):
            velocity = random.randint(70, 90)

            # Note on
            track.append(mido.Message('note_on', channel=0, note=note_num,
                                    velocity=velocity, time=time_offset))

            # Note off
            note_length = sixteenth_note * 3
            track.append(mido.Message('note_off', channel=0, note=note_num,
                                    velocity=0, time=note_length))

    def _create_drum_pattern(self, track: mido.MidiTrack, sixteenth_note: int):
        """Create a simple drum pattern."""
        # General MIDI drum map
        kick = 36
        snare = 38
        hihat = 42

        # Basic rock pattern
        pattern = [
            (0, kick, 90),           # Beat 1
            (4, hihat, 60),          # Off-beat
            (8, snare, 85),          # Beat 2
            (12, hihat, 60),         # Off-beat
        ]

        for time_offset, drum_note, velocity in pattern:
            # Drum on
            track.append(mido.Message('note_on', channel=9, note=drum_note,
                                    velocity=velocity, time=time_offset * sixteenth_note))

            # Drum off (short)
            track.append(mido.Message('note_off', channel=9, note=drum_note,
                                    velocity=0, time=sixteenth_note // 4))


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Generate random MIDI files for automation')
    parser.add_argument('--output', '-o', type=str, default='generated_midi.mid',
                       help='Output MIDI file name')
    parser.add_argument('--pattern', '-p', choices=['random', 'melody', 'chords', 'bass', 'drums'],
                       default='random', help='Pattern type to generate')
    parser.add_argument('--key', '-k', type=str, default='C',
                       help='Root key (C, D, E, F, G, A, B)')
    parser.add_argument('--scale', '-s', choices=['major', 'minor', 'dorian', 'mixolydian',
                       'pentatonic_major', 'pentatonic_minor', 'blues', 'harmonic_minor'],
                       default='major', help='Scale type')
    parser.add_argument('--tempo', '-t', type=int, default=120,
                       help='Tempo in BPM')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--count', '-c', type=int, default=1,
                       help='Number of MIDI files to generate')

    args = parser.parse_args()

    # Convert key name to MIDI note number
    key_map = {'C': 60, 'D': 62, 'E': 64, 'F': 65, 'G': 67, 'A': 69, 'B': 71}
    root_note = key_map.get(args.key.upper(), 60)

    generator = MIDIGenerator(seed=args.seed)

    for i in range(args.count):
        if args.count > 1:
            # Multiple files: add number to filename
            output_path = Path(args.output)
            output_file = output_path.parent / f"{output_path.stem}_{i+1:03d}{output_path.suffix}"
        else:
            output_file = Path(args.output)

        # Generate MIDI
        midi_file = generator.create_midi_pattern(
            pattern_type=args.pattern,
            root_note=root_note,
            scale_name=args.scale,
            tempo_bpm=args.tempo
        )

        # Save file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        midi_file.save(str(output_file))

        print(f"Generated: {output_file}")
        print(f"  Pattern: {args.pattern}")
        print(f"  Key: {args.key} {args.scale}")
        print(f"  Tempo: {args.tempo} BPM")
        if args.seed is not None:
            print(f"  Seed: {args.seed}")


if __name__ == "__main__":
    main()
