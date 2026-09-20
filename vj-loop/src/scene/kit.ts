// Shared materials, geometry and builders for the factory modules.
import * as THREE from "three";
import type { Loop, Rng, Time } from "../core/timeline";
import type { ModuleSlot } from "../core/layout";

export const COLORS = {
  cyan: new THREE.Color(0x19e6ff),
  magenta: new THREE.Color(0xff1f9c),
  orange: new THREE.Color(0xff7a1a),
  white: new THREE.Color(0xdfeaff),
};

export interface Glow {
  mat: THREE.MeshBasicMaterial;
  color: THREE.Color;
  /** Brightness between beats. Values above 1 feed the bloom pass. */
  base: number;
  /** Extra brightness at the top of each beat. */
  kick: number;
}

export interface Kit {
  loop: Loop;
  chrome: THREE.MeshStandardMaterial;
  steel: THREE.MeshStandardMaterial;
  dark: THREE.MeshStandardMaterial;
  glows: Record<keyof typeof COLORS, Glow>;
  box: THREE.BoxGeometry;
  cyl: THREE.CylinderGeometry;
  /** Shared shader uniforms. The world writes them once per render. */
  uBeat: { value: number };
  uPhase: { value: number };
}

export interface FactoryModule {
  group: THREE.Group;
  /** `rel` is the distance from the camera to the module's leading ring. */
  update?(t: Time, rel: number): void;
}
export type ModuleBuilder = (kit: Kit, slot: ModuleSlot, rand: Rng) => FactoryModule;

function glow(color: THREE.Color, base: number, kick: number): Glow {
  // Basic material: emits light, ignores lighting. Not tone mapped here; the final pass does that.
  const mat = new THREE.MeshBasicMaterial({ color: color.clone(), toneMapped: false });
  return { mat, color, base, kick };
}

export function makeKit(loop: Loop): Kit {
  return {
    loop,
    chrome: new THREE.MeshStandardMaterial({ color: 0xf2f5f8, metalness: 1, roughness: 0.07 }),
    steel: new THREE.MeshStandardMaterial({ color: 0x9aa3ad, metalness: 1, roughness: 0.32 }),
    dark: new THREE.MeshStandardMaterial({ color: 0x15181c, metalness: 0.9, roughness: 0.45 }),
    glows: {
      cyan: glow(COLORS.cyan, 1.5, 2.2),
      magenta: glow(COLORS.magenta, 1.5, 2.2),
      orange: glow(COLORS.orange, 1.8, 2.4),
      white: glow(COLORS.white, 1.2, 1.8),
    },
    box: new THREE.BoxGeometry(1, 1, 1),
    cyl: new THREE.CylinderGeometry(1, 1, 1, 16, 1),
    uBeat: { value: 0 },
    uPhase: { value: 0 },
  };
}

/** Set the brightness of all glow materials. `beatPulse` and `barPulse` are in [0, 1]. */
export function driveGlows(kit: Kit, beatPulse: number, barPulse: number): void {
  for (const g of Object.values(kit.glows)) {
    const k = g.base + g.kick * (0.55 * beatPulse + 0.45 * barPulse);
    g.mat.color.copy(g.color).multiplyScalar(k);
  }
}

export function boxMesh(kit: Kit, mat: THREE.Material, sx: number, sy: number, sz: number): THREE.Mesh {
  const m = new THREE.Mesh(kit.box, mat);
  m.scale.set(sx, sy, sz);
  return m;
}

/** A cylinder along the z axis. */
export function tubeZ(kit: Kit, mat: THREE.Material, radius: number, length: number): THREE.Mesh {
  const m = new THREE.Mesh(kit.cyl, mat);
  m.rotation.x = Math.PI / 2;
  m.scale.set(radius, length, radius);
  return m;
}

const _m = new THREE.Matrix4();
const _q = new THREE.Quaternion();
const _p = new THREE.Vector3();
const _s = new THREE.Vector3();
const _e = new THREE.Euler();

export interface Placement {
  x: number;
  y: number;
  z: number;
  rz: number;
  sx: number;
  sy: number;
  sz: number;
}

/** One draw call for many boxes. This is how the walls get their dense small detail. */
export function instancedBoxes(kit: Kit, mat: THREE.Material, items: Placement[]): THREE.InstancedMesh {
  const mesh = new THREE.InstancedMesh(kit.box, mat, items.length);
  items.forEach((it, i) => {
    _e.set(0, 0, it.rz);
    _q.setFromEuler(_e);
    _p.set(it.x, it.y, it.z);
    _s.set(it.sx, it.sy, it.sz);
    mesh.setMatrixAt(i, _m.compose(_p, _q, _s));
  });
  mesh.instanceMatrix.needsUpdate = true;
  mesh.computeBoundingSphere();
  return mesh;
}

/** A placement on the inside of a cylinder of radius `r`, at angle `a`. Local x is tangent, local y is radial. */
export function onRing(r: number, a: number, z: number, sx: number, sy: number, sz: number): Placement {
  return { x: Math.cos(a) * r, y: Math.sin(a) * r, z, rz: a - Math.PI / 2, sx, sy, sz };
}

/** Random machine detail on the tunnel wall between two ribs. Leaves gaps, so black shows through. */
export function wallGreebles(rand: Rng, r: number, len: number, count: number, skipFloor = true): Placement[] {
  const out: Placement[] = [];
  for (let i = 0; i < count; i++) {
    const a = rand() * Math.PI * 2;
    // Keep the floor arc clear for the rail bed.
    if (skipFloor && Math.abs(a - Math.PI * 1.5) < 0.42) continue;
    const big = rand() < 0.18;
    const tang = big ? 0.9 + rand() * 1.6 : 0.15 + rand() * 0.6;
    const depth = big ? 0.25 + rand() * 0.5 : 0.1 + rand() * 0.9;
    const along = big ? 1.2 + rand() * 3.0 : 0.2 + rand() * 1.4;
    out.push(onRing(r + 0.2 + rand() * 0.9 - depth / 2, a, -rand() * len, tang, depth, along));
  }
  return out;
}

/** The structural rib at the front of a module: a dark hoop, chrome clamps, and a thin light ring. */
export function ringFrame(kit: Kit, r: number, light: Glow, clamps = 12): THREE.Group {
  const g = new THREE.Group();
  g.add(new THREE.Mesh(new THREE.TorusGeometry(r + 0.35, 0.32, 10, 64), kit.dark));
  const lightRing = new THREE.Mesh(new THREE.TorusGeometry(r - 0.02, 0.035, 6, 96), light.mat);
  g.add(lightRing);
  const items: Placement[] = [];
  for (let i = 0; i < clamps; i++) {
    const a = ((i + 0.5) / clamps) * Math.PI * 2;
    items.push(onRing(r + 0.2, a, 0, 1.1, 0.7, 0.9));
    items.push(onRing(r + 0.05, a, 0, 0.35, 0.35, 1.3));
  }
  g.add(instancedBoxes(kit, kit.chrome, items));
  return g;
}

/** Rails, sleepers and a lit centre strip for one module. */
export function railBed(kit: Kit, len: number, floorY: number): THREE.Group {
  const g = new THREE.Group();
  const chrome: Placement[] = [];
  const dark: Placement[] = [];
  for (const x of [-0.75, 0.75]) {
    chrome.push({ x, y: floorY + 0.16, z: -len / 2, rz: 0, sx: 0.14, sy: 0.2, sz: len });
    dark.push({ x, y: floorY + 0.03, z: -len / 2, rz: 0, sx: 0.4, sy: 0.08, sz: len });
  }
  const sleepers = 8;
  for (let i = 0; i < sleepers; i++) {
    const z = -((i + 0.5) / sleepers) * len;
    dark.push({ x: 0, y: floorY, z, rz: 0, sx: 2.6, sy: 0.1, sz: 0.5 });
    chrome.push({ x: -1.15, y: floorY + 0.08, z, rz: 0, sx: 0.18, sy: 0.12, sz: 0.3 });
    chrome.push({ x: 1.15, y: floorY + 0.08, z, rz: 0, sx: 0.18, sy: 0.12, sz: 0.3 });
  }
  g.add(instancedBoxes(kit, kit.chrome, chrome));
  g.add(instancedBoxes(kit, kit.dark, dark));
  // Dashed centre light. Dashes make speed readable.
  const dashes: Placement[] = [];
  for (let i = 0; i < 4; i++) {
    dashes.push({ x: 0, y: floorY + 0.07, z: -((i + 0.5) / 4) * len, rz: 0, sx: 0.07, sy: 0.03, sz: len / 4 - 1.2 });
  }
  g.add(instancedBoxes(kit, kit.glows.cyan.mat, dashes));
  return g;
}

/** Long light strips that run with the track. They make the streaks in the chrome. */
export function lightStrips(kit: Kit, r: number, len: number, left: Glow, right: Glow): THREE.Group {
  const g = new THREE.Group();
  const mk = (glowMat: Glow, angles: number[]) => {
    const items = angles.map((a) => onRing(r - 0.15, a, -len / 2, 0.12, 0.06, len - 2.4));
    g.add(instancedBoxes(kit, glowMat.mat, items));
  };
  mk(left, [Math.PI * 0.78, Math.PI * 1.12]);
  mk(right, [Math.PI * 0.22, Math.PI * -0.12]);
  return g;
}

/** Pipes that keep the same angle in every module, so they read as continuous runs. */
export function pipeRuns(kit: Kit, r: number, len: number, angles: number[]): THREE.Group {
  const g = new THREE.Group();
  for (const a of angles) {
    const p = tubeZ(kit, kit.steel, 0.16, len);
    p.position.set(Math.cos(a) * (r + 0.1), Math.sin(a) * (r + 0.1), -len / 2);
    g.add(p);
  }
  return g;
}
