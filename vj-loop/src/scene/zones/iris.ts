// Zone 1: a ring tunnel with an iris gate on every bar. Each gate opens just before the sled arrives.
import * as THREE from "three";
import { smoothstep } from "../../core/timeline";
import {
  boxMesh,
  instancedBoxes,
  lightStrips,
  pipeRuns,
  railBed,
  ringFrame,
  wallGreebles,
  type ModuleBuilder,
} from "../kit";

export const R = 6;
export const FLOOR_Y = -2.4;
const BLADES = 12;

export const buildIris: ModuleBuilder = (kit, slot, rand) => {
  const len = kit.loop.spec.unitsPerBeat;
  const group = new THREE.Group();
  group.add(ringFrame(kit, R, slot.downbeat ? kit.glows.magenta : kit.glows.cyan));
  group.add(railBed(kit, len, FLOOR_Y));
  group.add(lightStrips(kit, R, len, kit.glows.cyan, kit.glows.magenta));
  group.add(pipeRuns(kit, R, len, [0.5, 1.1, 2.0, 2.6, 3.6, 5.8]));
  const greebles = wallGreebles(rand, R, len, 260);
  group.add(instancedBoxes(kit, kit.steelPanel, greebles.filter((_, i) => i % 3 !== 0)));
  group.add(instancedBoxes(kit, kit.chromePanel, greebles.filter((_, i) => i % 3 === 0)));

  if (!slot.downbeat) return { group };

  // Iris gate. Each blade is a plate that slides outward and turns as the gate opens.
  const blades: THREE.Group[] = [];
  const gate = new THREE.Group();
  gate.position.z = -0.8;
  for (let i = 0; i < BLADES; i++) {
    const pivot = new THREE.Group();
    const plate = boxMesh(kit, i % 2 ? kit.chrome : kit.steel, R * 0.95, R * 0.9, 0.12);
    plate.position.z = (i % 2) * 0.14;
    const edge = boxMesh(kit, kit.glows.magenta.mat, R * 0.95, 0.05, 0.16);
    edge.position.set(0, -R * 0.45, (i % 2) * 0.14);
    pivot.add(plate, edge);
    gate.add(pivot);
    blades.push(pivot);
  }
  group.add(gate);

  return {
    group,
    update(_t, rel) {
      // Shut when far. Opens late, so the sled seems to just clear the blades. Fully open half a beat away.
      const open = 1 - smoothstep(len * 0.5, len * 1.9, rel);
      // Shut, the blades overlap past the centre, so nothing behind the gate shows through.
      const rc = THREE.MathUtils.lerp(R * 0.42, R * 1.4, open);
      blades.forEach((b, i) => {
        const a = (i / BLADES) * Math.PI * 2 + open * 0.5;
        b.position.set(Math.cos(a) * rc, Math.sin(a) * rc, 0);
        b.rotation.z = a - Math.PI / 2;
      });
    },
  };
};
