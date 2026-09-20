// Assembles the track and drives it from a Time. The track is a closed lap: modules wrap around
// the camera, so what lies ahead at the end of the loop is what lay ahead at the start.
import * as THREE from "three";
import { layoutTrack, type Zone } from "../core/layout";
import { cycle, mod, pulse, relAhead, rng, wave, type Loop, type Time } from "../core/timeline";
import { boxMesh, driveGlows, makeKit, type FactoryModule, type Kit, type ModuleBuilder } from "./kit";
import { buildForge } from "./zones/forge";
import { buildHall } from "./zones/hall";
import { buildIris } from "./zones/iris";
import { buildNanite } from "./zones/nanite";

const BUILDERS: Record<Zone, ModuleBuilder> = {
  iris: buildIris,
  forge: buildForge,
  nanite: buildNanite,
  hall: buildHall,
};

/** Modules stay drawn this far behind the camera, so nothing vanishes inside the frame. */
const BEHIND = 30;
/** Modules further ahead than this are hidden. Fog has taken them to black well before. */
const DRAW_AHEAD = 300;

export interface World {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  kit: Kit;
  update(t: Time): void;
}

/** A small lit scene, baked once into the reflection map. Chrome needs something to reflect. */
function bakeEnvironment(renderer: THREE.WebGLRenderer): THREE.Texture {
  const env = new THREE.Scene();
  const strip = (color: number, k: number, x: number, y: number, z: number, sx: number, sy: number, sz: number) => {
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(sx, sy, sz),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k) }),
    );
    m.position.set(x, y, z);
    env.add(m);
  };
  // Long strips along the direction of travel give chrome its streaks.
  strip(0x19e6ff, 4, -6, 3, 0, 0.25, 0.25, 60);
  strip(0xff1f9c, 4, 6, 3, 0, 0.25, 0.25, 60);
  strip(0x19e6ff, 2, -5, -4, 0, 0.2, 0.2, 60);
  strip(0xff1f9c, 2, 5, -4, 0, 0.2, 0.2, 60);
  strip(0xdfeaff, 2.5, 0, 7, 0, 1.2, 0.1, 40);
  // Rings ahead and behind.
  for (const z of [-14, -28, 14]) {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(6, 0.12, 6, 48),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(0xdfeaff).multiplyScalar(1.5) }),
    );
    ring.position.z = z;
    env.add(ring);
  }
  // Many small panels at mixed brightness. Sharp chrome needs fine detail to reflect, or it reads as grey.
  const rand = rng(77);
  for (let i = 0; i < 140; i++) {
    const a = rand() * Math.PI * 2;
    const r = 9 + rand() * 6;
    const tint = [0xdfeaff, 0x19e6ff, 0xff1f9c, 0xdfeaff][Math.floor(rand() * 4)]!;
    strip(tint, 0.3 + rand() * rand() * 5, Math.cos(a) * r, Math.sin(a) * r, (rand() * 2 - 1) * 40, 0.3 + rand() * 1.5, 0.3 + rand() * 1.5, 0.5 + rand() * 6);
  }
  const pmrem = new THREE.PMREMGenerator(renderer);
  const tex = pmrem.fromScene(env, 0.015, 0.1, 100).texture;
  pmrem.dispose();
  return tex;
}

/** The front lip of the carrier sled. It rides with the camera and anchors the point of view. */
function buildSled(kit: Kit): THREE.Group {
  const sled = new THREE.Group();
  // Kept low and slim. It should frame the view, not fill it.
  const lip = boxMesh(kit, kit.dark, 1.5, 0.08, 0.3);
  lip.position.set(0, -1.78, -2.0);
  lip.rotation.x = 0.3;
  const edge = boxMesh(kit, kit.glows.cyan.mat, 1.3, 0.015, 0.02);
  edge.position.set(0, -1.72, -2.15);
  for (const x of [-0.8, 0.8]) {
    const prong = boxMesh(kit, kit.chrome, 0.1, 0.12, 1.1);
    prong.position.set(x, -1.7, -2.5);
    prong.rotation.set(0.3, x > 0 ? 0.12 : -0.12, 0);
    sled.add(prong);
  }
  sled.add(lip, edge);
  return sled;
}

export function buildWorld(loop: Loop, renderer: THREE.WebGLRenderer): World {
  const kit = makeKit(loop);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x000000);
  scene.fog = new THREE.FogExp2(0x000000, 0.0105);
  scene.environment = bakeEnvironment(renderer);
  scene.environmentIntensity = 1.0;

  const { width, height } = loop.spec;
  const camera = new THREE.PerspectiveCamera(84, width / height, 0.1, DRAW_AHEAD + 40);
  camera.add(buildSled(kit));
  // Headlight. Gives near surfaces a moving highlight that the baked reflections cannot.
  const lamp = new THREE.PointLight(0xcfe8ff, 4, 40, 1.8);
  lamp.position.set(0, 1.6, -9);
  camera.add(lamp);
  scene.add(camera);

  const slots = layoutTrack(loop);
  const modules: { slotZ: number; mod: FactoryModule }[] = slots.map((slot) => {
    const mod = BUILDERS[slot.zone](kit, slot, rng(1000 + slot.index));
    scene.add(mod.group);
    return { slotZ: slot.z, mod };
  });

  return {
    scene,
    camera,
    kit,
    update(t) {
      const beatPulse = pulse(cycle(loop, t.beat, 1), 4.5);
      const barPulse = pulse(cycle(loop, t.beat, loop.spec.beatsPerBar), 2.2);
      driveGlows(kit, beatPulse, barPulse);
      kit.uBeat.value = t.beat;
      kit.uPhase.value = t.phase;
      lamp.intensity = 5 + 14 * beatPulse;

      // Floating origin: the camera stays at z = 0 and the track slides past it. World positions then
      // depend only on the wrapped track position, so phase 1 gives bit-identical geometry to phase 0.
      camera.position.set(0, 0, 0);
      kit.uTrackZ.value = mod(t.camZ, loop.length);
      // A slow roll and a kick of field of view on the beat. Whole turns per loop only.
      camera.rotation.set(0.012 * wave(t, 5), 0, 0.09 * wave(t, 2) + 0.03 * wave(t, 10, 0.25));
      camera.fov = 84 + 5 * beatPulse + 4 * barPulse;
      camera.updateProjectionMatrix();

      for (const m of modules) {
        const rel = relAhead(m.slotZ, t.camZ, loop.length, BEHIND);
        const on = rel < DRAW_AHEAD;
        m.mod.group.visible = on;
        if (!on) continue;
        m.mod.group.position.z = -rel;
        m.mod.update?.(t, rel);
      }
    },
  };
}
