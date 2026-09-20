// Zone 3: the nanite chamber. The tunnel widens. A swarm of tiny chrome bodies flows around the rail
// and snaps into a lattice on every second bar. The swarm moves in the vertex shader.
import * as THREE from "three";
import { cycle, type Rng } from "../../core/timeline";
import { instancedBoxes, onRing, railBed, ringFrame, type Kit, type ModuleBuilder, type Placement } from "../kit";
import { FLOOR_Y } from "./iris";

const R_CHAMBER = 10;
const SWARM_PER_MODULE = 4200;

const SWARM_VERTEX = /* glsl */ `
  // aSeed: x start angle, y radius, z start z (0..1 of module), w speed class
  vec4 sd = aSeed;
  float turns = floor(1.0 + sd.w * 3.0);                       // whole turns per 8 beats
  float ang = sd.x * 6.2831853 + uSwarm.x * 6.2831853 * turns;
  float rad = sd.y + 0.6 * sin(uSwarm.x * 6.2831853 * 2.0 + sd.x * 40.0);
  float zz = -fract(sd.z + uSwarm.x * (1.0 + floor(sd.w * 2.0))) * uSwarm.z;
  vec3 flow = vec3(cos(ang) * rad, sin(ang) * rad * 0.82 + 0.4, zz);
  // Lattice target: snap the flow position to a grid, shaped into shells around the rail.
  float cell = 0.9;
  vec3 snapped = floor(flow / cell + 0.5) * cell;
  vec3 pos = mix(flow, snapped, uSwarm.y);
  float grow = mix(1.0, 2.4, uSwarm.y);
  transformed = transformed * grow + pos;
`;

function swarmMaterial(uSwarm: { value: THREE.Vector3 }): THREE.MeshStandardMaterial {
  const mat = new THREE.MeshStandardMaterial({ color: 0xeaf6ff, metalness: 1, roughness: 0.12 });
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uSwarm = uSwarm;
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nattribute vec4 aSeed;\nuniform vec3 uSwarm;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\n" + SWARM_VERTEX);
  };
  // All swarm meshes share one program.
  mat.customProgramCacheKey = () => "nanite-swarm";
  return mat;
}

interface Shared {
  mat: THREE.MeshStandardMaterial;
  uSwarm: { value: THREE.Vector3 };
  geo: THREE.OctahedronGeometry;
}
const shared = new WeakMap<Kit, Shared>();
function getShared(kit: Kit): Shared {
  let s = shared.get(kit);
  if (!s) {
    // x: flow position in an 8-beat cycle. y: lattice morph 0..1. z: module length.
    const uSwarm = { value: new THREE.Vector3(0, 0, kit.loop.spec.unitsPerBeat) };
    s = { uSwarm, mat: swarmMaterial(uSwarm), geo: new THREE.OctahedronGeometry(0.055, 0) };
    shared.set(kit, s);
  }
  return s;
}

function buildSwarm(kit: Kit, rand: Rng): THREE.InstancedMesh {
  const s = getShared(kit);
  const seeds = new Float32Array(SWARM_PER_MODULE * 4);
  for (let i = 0; i < SWARM_PER_MODULE; i++) {
    // Bias radii toward two shells, so the lattice reads as nested structures, not fog.
    const shell = rand() < 0.55 ? 3.2 + rand() * 1.2 : 6.0 + rand() * 2.6;
    seeds.set([rand(), shell, rand(), rand()], i * 4);
  }
  // The per-instance seeds live on a clone, because each module has its own seeds.
  const geo = s.geo.clone();
  geo.setAttribute("aSeed", new THREE.InstancedBufferAttribute(seeds, 4));
  const mesh = new THREE.InstancedMesh(geo, s.mat, SWARM_PER_MODULE);
  const id = new THREE.Matrix4();
  for (let i = 0; i < SWARM_PER_MODULE; i++) mesh.setMatrixAt(i, id);
  mesh.frustumCulled = false;
  return mesh;
}

export const buildNanite: ModuleBuilder = (kit, slot, rand) => {
  const len = kit.loop.spec.unitsPerBeat;
  const group = new THREE.Group();
  // The chamber mouth narrows back to the tunnel radius at both ends of the zone.
  const edge = Math.min(slot.local, slot.zoneSize - 1 - slot.local);
  const r = edge === 0 ? 6 : edge === 1 ? 8 : R_CHAMBER;
  group.add(ringFrame(kit, r, slot.downbeat ? kit.glows.white : kit.glows.cyan, 20));
  group.add(railBed(kit, len, FLOOR_Y));

  // Sparse ribs instead of a wall. The chamber should feel open and dark.
  const ribs: Placement[] = [];
  for (let i = 0; i < 20; i++) {
    const a = (i / 20) * Math.PI * 2;
    ribs.push(onRing(r + 0.4, a, -len / 2, 0.22, 0.5, len));
    if (i % 2 === 0) ribs.push(onRing(r + 0.1, a, -len * (0.2 + rand() * 0.6), 0.7, 0.4, 1.4 + rand() * 2));
  }
  group.add(instancedBoxes(kit, kit.steelPanel, ribs));
  const lights: Placement[] = [];
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2 + slot.index * 0.63;
    lights.push(onRing(r - 0.1, a, -len / 2, 0.08, 0.05, len * 0.7));
  }
  group.add(instancedBoxes(kit, kit.glows.cyan.mat, lights));

  // Rail pylons: the rail is a bridge through the chamber.
  const pylons: Placement[] = [];
  for (const z of [-len * 0.25, -len * 0.75]) pylons.push({ x: 0, y: FLOOR_Y - 3.6, z, rz: 0, sx: 0.5, sy: 7, sz: 0.5 });
  group.add(instancedBoxes(kit, kit.darkPanel, pylons));

  if (edge > 0) group.add(buildSwarm(kit, rand));

  return {
    group,
    update(t) {
      // Written by every nanite module each render. The value is the same for all of them.
      const s = getShared(kit);
      const c8 = cycle(kit.loop, t.beat, 8);
      // Snap to the lattice on beats 5-8 of each 8, with a fast attack and slow release.
      const snap = Math.min(smooth(0.5, 0.56, c8), 1 - smooth(0.9, 1.0, c8));
      s.uSwarm.value.set(c8, snap, len);
    },
  };
};

function smooth(a: number, b: number, x: number): number {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}
