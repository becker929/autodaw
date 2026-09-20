// Pure loop math. No three.js, no DOM, no clock.
// Every animated value in the scene is a function of a Time made here,
// so the render is a pure function of (spec, frame, subframe).
import { z } from "zod";

export const LoopSpec = z
  .object({
    bpm: z.number().positive().default(160),
    bars: z.number().int().positive().default(20),
    beatsPerBar: z.number().int().positive().default(4),
    fps: z.number().int().positive().default(60),
    width: z.number().int().positive().default(3840),
    height: z.number().int().positive().default(2160),
    // Renders averaged into one output frame. Gives motion blur and antialiasing.
    subframes: z.number().int().min(1).max(64).default(8),
    // Fraction of the frame interval the virtual shutter stays open. 0.5 is a 180 degree shutter.
    shutter: z.number().min(0).max(1).default(0.5),
    // Distance the camera travels in one beat. Ring spacing equals this, so a ring passes on every beat.
    unitsPerBeat: z.number().positive().default(9),
  })
  .strict();
export type LoopSpec = z.infer<typeof LoopSpec>;

export interface Loop {
  spec: LoopSpec;
  beats: number;
  seconds: number;
  frames: number;
  /** World length of one full lap of the track. */
  length: number;
}

export interface Time {
  /** 0 at the loop start, 1 at the loop end. Not wrapped, so phase 1 is a real test of closure. */
  phase: number;
  /** Beats since the loop start. */
  beat: number;
  /** Camera position on the track axis. The camera moves toward negative z. */
  camZ: number;
  /** Output frame index. Used only for film grain. */
  frame: number;
}

export function deriveLoop(spec: LoopSpec): Loop {
  const beats = spec.bars * spec.beatsPerBar;
  const seconds = (beats * 60) / spec.bpm;
  const frames = seconds * spec.fps;
  if (Math.abs(frames - Math.round(frames)) > 1e-9) {
    throw new Error(
      `Loop of ${seconds}s at ${spec.fps} fps is ${frames} frames. It must be a whole number, or the loop cannot close.`,
    );
  }
  return { spec, beats, seconds, frames: Math.round(frames), length: beats * spec.unitsPerBeat };
}

export function timeAt(loop: Loop, frame: number, sub = 0): Time {
  const { subframes, shutter } = loop.spec;
  const f = frame + (shutter * (sub + 0.5)) / subframes;
  const phase = f / loop.frames;
  const beat = phase * loop.beats;
  return { phase, beat, camZ: -phase * loop.length, frame };
}

export const fract = (x: number): number => x - Math.floor(x);
export const mod = (x: number, m: number): number => ((x % m) + m) % m;
export const clamp01 = (x: number): number => Math.min(1, Math.max(0, x));
export const lerp = (a: number, b: number, t: number): number => a + (b - a) * t;
export function smoothstep(e0: number, e1: number, x: number): number {
  const t = clamp01((x - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
}

/**
 * Distance from the camera to an object along the direction of travel, on a circular track.
 * The result lies in [-behind, length - behind). Objects just passed stay briefly behind the camera.
 */
export function relAhead(objZ: number, camZ: number, length: number, behind: number): number {
  return mod(camZ - objZ + behind, length) - behind;
}

/**
 * Position inside a repeating cycle of `everyBeats` beats, in [0, 1).
 * Throws unless the cycle divides the loop, because any other cycle would break the loop seam.
 */
export function cycle(loop: Loop, beat: number, everyBeats: number): number {
  const n = loop.beats / everyBeats;
  if (Math.abs(n - Math.round(n)) > 1e-9) {
    throw new Error(`A cycle of ${everyBeats} beats does not divide the ${loop.beats}-beat loop.`);
  }
  return fract(beat / everyBeats);
}

/** Sharp attack, exponential decay. `x` is a cycle position in [0, 1). */
export const pulse = (x: number, sharpness = 5): number => Math.exp(-sharpness * x);

/** sin with a whole number of turns per loop. */
export function wave(t: Time, turnsPerLoop: number, offset = 0): number {
  if (!Number.isInteger(turnsPerLoop)) throw new Error("wave needs a whole number of turns per loop");
  return Math.sin(2 * Math.PI * (t.phase * turnsPerLoop + offset));
}

/** Integer hash to [0, 1). */
export function hash01(n: number): number {
  let h = (n | 0) ^ 0x9e3779b9;
  h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

/**
 * A value that changes `stepsPerBeat` times per beat and repeats with the loop.
 * Used for flicker that must look random but still close the loop.
 */
export function stepNoise(loop: Loop, beat: number, stepsPerBeat: number, seed: number): number {
  const total = loop.beats * stepsPerBeat;
  const step = mod(Math.floor(beat * stepsPerBeat + 1e-7), total);
  return hash01(step * 7919 + seed * 104729);
}

/** Seeded random number generator (mulberry32). Math.random is banned in this project. */
export function rng(seed: number): () => number {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export type Rng = () => number;
