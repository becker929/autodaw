// Zone 4: the transformation hall. A square hall whose armour walls unfold as the sled nears,
// showing the lit cores behind them. Pistons in the roof pump on the beat.
import * as THREE from "three";
import { cycle, pulse, smoothstep } from "../../core/timeline";
import { boxMesh, instancedBoxes, railBed, type ModuleBuilder, type Placement } from "../kit";
import { FLOOR_Y } from "./iris";

const HALF_W = 6.2;
const ROOF_Y = 6.4;
const ROWS = 4;
const COLS = 3;

export const buildHall: ModuleBuilder = (kit, slot, rand) => {
  const len = kit.loop.spec.unitsPerBeat;
  const group = new THREE.Group();
  group.add(railBed(kit, len, FLOOR_Y));

  // Portal frame at the front of the module.
  const frame: Placement[] = [
    { x: -HALF_W - 0.6, y: (ROOF_Y + FLOOR_Y) / 2, z: 0, rz: 0, sx: 1.2, sy: ROOF_Y - FLOOR_Y + 1.6, sz: 1.0 },
    { x: HALF_W + 0.6, y: (ROOF_Y + FLOOR_Y) / 2, z: 0, rz: 0, sx: 1.2, sy: ROOF_Y - FLOOR_Y + 1.6, sz: 1.0 },
    { x: 0, y: ROOF_Y + 0.6, z: 0, rz: 0, sx: HALF_W * 2 + 2.4, sy: 1.2, sz: 1.0 },
    { x: -4.2, y: FLOOR_Y - 0.5, z: 0, rz: 0, sx: HALF_W * 2 - 5.2, sy: 0.9, sz: 1.0 },
    { x: 4.2, y: FLOOR_Y - 0.5, z: 0, rz: 0, sx: HALF_W * 2 - 5.2, sy: 0.9, sz: 1.0 },
  ];
  group.add(instancedBoxes(kit, kit.dark, frame));
  const trim = slot.downbeat ? kit.glows.white : kit.glows.magenta;
  const trimItems: Placement[] = [
    { x: -HALF_W + 0.02, y: (ROOF_Y + FLOOR_Y) / 2, z: 0.2, rz: 0, sx: 0.06, sy: ROOF_Y - FLOOR_Y, sz: 0.06 },
    { x: HALF_W - 0.02, y: (ROOF_Y + FLOOR_Y) / 2, z: 0.2, rz: 0, sx: 0.06, sy: ROOF_Y - FLOOR_Y, sz: 0.06 },
    { x: 0, y: ROOF_Y - 0.02, z: 0.2, rz: 0, sx: HALF_W * 2, sy: 0.06, sz: 0.06 },
  ];
  group.add(instancedBoxes(kit, trim.mat, trimItems));

  // Floor plates beside the rail, and small roof detail.
  const detail: Placement[] = [];
  for (let i = 0; i < 90; i++) {
    const roof = rand() < 0.6;
    const x = (rand() * 2 - 1) * HALF_W;
    if (!roof && Math.abs(x) < 1.8) continue;
    detail.push({
      x,
      y: roof ? ROOF_Y + rand() * 0.5 : FLOOR_Y - 0.3 - rand() * 0.3,
      z: -rand() * len,
      rz: 0,
      sx: 0.3 + rand() * 1.6,
      sy: 0.2 + rand() * 0.7,
      sz: 0.4 + rand() * 2.4,
    });
  }
  group.add(instancedBoxes(kit, kit.steel, detail));

  // Lit cores behind the armour. Hidden until the plates swing away.
  const cores: Placement[] = [];
  for (const sx of [-1, 1]) {
    for (let c = 0; c < COLS; c++) {
      const z = -((c + 0.5) / COLS) * len;
      cores.push({ x: sx * (HALF_W + 0.9), y: (ROOF_Y + FLOOR_Y) / 2, z, rz: 0, sx: 0.25, sy: ROOF_Y - FLOOR_Y - 1, sz: 0.25 });
      cores.push({ x: sx * (HALF_W + 1.3), y: (ROOF_Y + FLOOR_Y) / 2, z, rz: 0, sx: 0.1, sy: 0.1, sz: len / COLS - 0.4 });
    }
  }
  group.add(instancedBoxes(kit, kit.glows.magenta.mat, cores));

  // Armour plates. Each hangs from a hinge on its far edge and swings outward around the vertical axis.
  const plateW = len / COLS - 0.15;
  const plateH = (ROOF_Y - FLOOR_Y) / ROWS - 0.12;
  const hinges: { hinge: THREE.Group; side: number; delay: number }[] = [];
  for (const side of [-1, 1]) {
    for (let c = 0; c < COLS; c++) {
      for (let r = 0; r < ROWS; r++) {
        const hinge = new THREE.Group();
        hinge.position.set(side * HALF_W, FLOOR_Y + (r + 0.5) * (plateH + 0.12), -(c + 1) * (len / COLS));
        const plate = boxMesh(kit, (c + r) % 2 ? kit.chrome : kit.steel, 0.22, plateH, plateW);
        plate.position.z = plateW / 2;
        const rib = boxMesh(kit, kit.dark, 0.3, plateH * 0.5, plateW * 0.6);
        rib.position.set(-side * 0.05, 0, plateW / 2);
        const ram = boxMesh(kit, kit.chrome, 0.12, 0.12, plateW * 0.9);
        ram.position.set(side * 0.35, plateH * 0.3, plateW / 2);
        hinge.add(plate, rib, ram);
        group.add(hinge);
        hinges.push({ hinge, side, delay: r * 0.35 + c * 0.2 + rand() * 0.15 });
      }
    }
  }

  // Roof pistons.
  const pistons: { rod: THREE.Mesh; phase: number }[] = [];
  for (const x of [-3.6, 3.6]) {
    const housing = boxMesh(kit, kit.dark, 1.4, 1.2, 1.4);
    housing.position.set(x, ROOF_Y - 0.2, -len / 2);
    const rod = new THREE.Mesh(kit.cyl, kit.chrome);
    rod.scale.set(0.38, 2.6, 0.38);
    rod.position.set(x, ROOF_Y - 1.2, -len / 2);
    const foot = boxMesh(kit, kit.glows.magenta.mat, 0.9, 0.06, 0.9);
    foot.position.y = -0.5;
    foot.scale.set(0.9 / 0.38, 0.06 / 2.6, 0.9 / 0.38);
    rod.add(foot);
    group.add(housing, rod);
    pistons.push({ rod, phase: x > 0 ? 0.5 : 0 });
  }

  return {
    group,
    update(t, rel) {
      for (const h of hinges) {
        // Plates further up and further back open later, so the wall peels rather than snaps.
        const open = 1 - smoothstep(len * (0.7 + h.delay), len * (2.3 + h.delay), rel);
        h.hinge.rotation.y = h.side * open * 1.9;
      }
      for (const p of pistons) {
        const c = cycle(kit.loop, t.beat + p.phase * 2, 2);
        p.rod.position.y = ROOF_Y - 1.2 - 1.7 * pulse(c, 4);
      }
    },
  };
};
