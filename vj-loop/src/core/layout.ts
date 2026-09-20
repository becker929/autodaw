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

/** Split the lap into equal zones. Each zone is a whole number of bars when bars divides by the zone count. */
export function layoutTrack(loop: Loop): ModuleSlot[] {
  const n = loop.beats;
  const per = n / ZONES.length;
  if (!Number.isInteger(per)) throw new Error(`${n} beats do not split into ${ZONES.length} equal zones.`);
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
