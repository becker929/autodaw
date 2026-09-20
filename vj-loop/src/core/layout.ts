// Pure track layout. The track is a closed lap of modules. One module is one beat long.
import type { Loop } from "./timeline";

export const ZONES = ["iris", "forge", "nanite", "hall"] as const;
export type Zone = (typeof ZONES)[number];

export interface ModuleSlot {
  index: number;
  zone: Zone;
  /** Index inside its zone, from 0. */
  local: number;
  /** Modules in this zone. */
  zoneSize: number;
  /** True for the first module of a bar. */
  downbeat: boolean;
  /** World z of the module's leading ring. The module extends toward negative z. */
  z: number;
}

/** Beat cycles the scene animates on. Each must divide the loop, or the seam breaks. */
export const SCENE_CYCLES = [1, 2, 4, 8] as const;

/**
 * Everything the scene needs from a loop, checked up front. Run this before opening a browser,
 * so a bad spec fails in a second with one clear message, not minutes into a render.
 */
export class SceneLoopError extends Error {}

export function validateSceneLoop(loop: Loop): void {
  const problems: string[] = [];
  if (loop.beats % ZONES.length !== 0) problems.push(`${loop.beats} beats do not split into ${ZONES.length} equal zones`);
  for (const c of SCENE_CYCLES) {
    if (loop.beats % c !== 0) {
      problems.push(`the scene has a ${c}-beat cycle, which does not divide ${loop.beats} beats (use a beat count that divides by 8)`);
    }
  }
  if (loop.spec.unitsPerBeat < 6) problems.push(`unitsPerBeat ${loop.spec.unitsPerBeat} is below 6; the module parts do not fit`);
  if (problems.length) throw new SceneLoopError(`This loop cannot be rendered: ${problems.join("; ")}.`);
}

/** Split the lap into equal zones. Each zone is a whole number of bars when bars divides by the zone count. */
export function layoutTrack(loop: Loop): ModuleSlot[] {
  validateSceneLoop(loop);
  const n = loop.beats;
  const per = n / ZONES.length;
  const slots: ModuleSlot[] = [];
  for (let i = 0; i < n; i++) {
    const zi = Math.floor(i / per);
    slots.push({
      index: i,
      zone: ZONES[zi]!,
      local: i - zi * per,
      zoneSize: per,
      downbeat: i % loop.spec.beatsPerBar === 0,
      z: -i * loop.spec.unitsPerBeat,
    });
  }
  return slots;
}
