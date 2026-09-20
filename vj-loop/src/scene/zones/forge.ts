// Zone 2: the laser forge. Robot arms weld over the rail, laser gates fire across it, sparks fall.
import * as THREE from "three";
import { cycle, stepNoise, type Rng } from "../../core/timeline";
import {
  boxMesh,
  instancedBoxes,
  lightStrips,
  pipeRuns,
  railBed,
  ringFrame,
  wallGreebles,
  type Kit,
  type ModuleBuilder,
} from "../kit";
import { FLOOR_Y, R } from "./iris";

interface Arm {
  shoulder: THREE.Group;
  elbow: THREE.Group;
  wrist: THREE.Group;
  seed: number;
}

function buildArm(kit: Kit, angle: number, z: number, seed: number): { root: THREE.Group; arm: Arm; tip: THREE.Object3D } {
  // The root sits on the wall. Its local -y axis points at the tunnel centre.
  const root = new THREE.Group();
  root.position.set(Math.cos(angle) * (R - 0.2), Math.sin(angle) * (R - 0.2), z);
  root.rotation.z = angle - Math.PI / 2;
  const base = boxMesh(kit, kit.dark, 1.3, 0.6, 1.3);
  root.add(base);

  const shoulder = new THREE.Group();
  shoulder.position.y = -0.4;
  const upper = boxMesh(kit, kit.chrome, 0.42, 2.4, 0.42);
  upper.position.y = -1.2;
  const upperRib = boxMesh(kit, kit.dark, 0.5, 1.2, 0.2);
  upperRib.position.y = -1.2;
  shoulder.add(upper, upperRib, jointDisc(kit, 0.42));

  const elbow = new THREE.Group();
  elbow.position.y = -2.4;
  const fore = boxMesh(kit, kit.steel, 0.3, 2.0, 0.3);
  fore.position.y = -1.0;
  elbow.add(fore, jointDisc(kit, 0.34));

  const wrist = new THREE.Group();
  wrist.position.y = -2.0;
  const head = boxMesh(kit, kit.chrome, 0.5, 0.5, 0.5);
  const nozzle = boxMesh(kit, kit.dark, 0.14, 0.5, 0.14);
  nozzle.position.y = -0.45;
  const tip = boxMesh(kit, kit.glows.orange.mat, 0.16, 0.16, 0.16);
  tip.position.y = -0.74;
  wrist.add(head, nozzle, tip, jointDisc(kit, 0.26));

  elbow.add(wrist);
  shoulder.add(elbow);
  root.add(shoulder);
  return { root, arm: { shoulder, elbow, wrist, seed }, tip };
}

function jointDisc(kit: Kit, r: number): THREE.Mesh {
  const d = new THREE.Mesh(kit.cyl, kit.steel);
  d.rotation.x = Math.PI / 2;
  d.scale.set(r, 0.62, r);
  return d;
}

const SPARK_VS = /* glsl */ `
  uniform float uBeat;
  uniform float uSecPerBeat;
  uniform float uSize;
  attribute vec4 aVel;   // xyz velocity, w life in beats (1, 2 or 4)
  attribute float aSeed;
  varying float vFade;
  void main() {
    float life = aVel.w;
    float age = fract(uBeat / life + aSeed);      // 0..1, repeats with the loop because life divides it
    float s = age * life * uSecPerBeat;
    vec3 p = position + aVel.xyz * s + vec3(0.0, -9.0, 0.0) * s * s;
    vFade = (1.0 - age) * (1.0 - age);
    vec4 mv = modelViewMatrix * vec4(p, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = uSize * vFade / max(0.5, -mv.z);
  }
`;
const SPARK_FS = /* glsl */ `
  varying float vFade;
  void main() {
    vec2 d = gl_PointCoord - 0.5;
    float a = smoothstep(0.5, 0.0, length(d));
    gl_FragColor = vec4(vec3(4.0, 1.6, 0.4) * a * vFade, 1.0);
  }
`;

function sparkMaterial(kit: Kit): THREE.ShaderMaterial {
  const { height, bpm } = kit.loop.spec;
  return new THREE.ShaderMaterial({
    // uBeat is the kit's shared uniform object, so the world drives every spark system at once.
    uniforms: { uBeat: kit.uBeat, uSecPerBeat: { value: 60 / bpm }, uSize: { value: height * 0.018 } },
    vertexShader: SPARK_VS,
    fragmentShader: SPARK_FS,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    transparent: true,
  });
}

function buildSparks(rand: Rng, origins: THREE.Vector3[], perOrigin: number, mat: THREE.ShaderMaterial): THREE.Points {
  const n = origins.length * perOrigin;
  const pos = new Float32Array(n * 3);
  const vel = new Float32Array(n * 4);
  const seed = new Float32Array(n);
  let k = 0;
  for (const o of origins) {
    for (let i = 0; i < perOrigin; i++, k++) {
      pos.set([o.x, o.y, o.z], k * 3);
      const a = rand() * Math.PI * 2;
      const sp = 2 + rand() * 7;
      vel.set([Math.cos(a) * sp, 1 + rand() * 6, Math.sin(a) * sp, [1, 1, 2, 4][Math.floor(rand() * 4)]!], k * 4);
      seed[k] = rand();
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("aVel", new THREE.BufferAttribute(vel, 4));
  geo.setAttribute("aSeed", new THREE.BufferAttribute(seed, 1));
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  return pts;
}

const sparkMats = new WeakMap<Kit, THREE.ShaderMaterial>();
function forgeSparkMaterial(kit: Kit): THREE.ShaderMaterial {
  let m = sparkMats.get(kit);
  if (!m) sparkMats.set(kit, (m = sparkMaterial(kit)));
  return m;
}

export const buildForge: ModuleBuilder = (kit, slot, rand) => {
  const len = kit.loop.spec.unitsPerBeat;
  const group = new THREE.Group();
  group.add(ringFrame(kit, R, slot.downbeat ? kit.glows.white : kit.glows.orange, 16));
  group.add(railBed(kit, len, FLOOR_Y));
  group.add(lightStrips(kit, R, len, kit.glows.orange, kit.glows.cyan));
  group.add(pipeRuns(kit, R, len, [0.5, 1.1, 2.0, 2.6, 3.6, 5.8]));
  const greebles = wallGreebles(rand, R, len, 320);
  group.add(instancedBoxes(kit, kit.steelPanel, greebles.filter((_, i) => i % 2 === 0)));
  group.add(instancedBoxes(kit, kit.darkPanel, greebles.filter((_, i) => i % 2 === 1)));

  // Arms on every module, mirrored left and right, on the upper half of the ring.
  const arms: Arm[] = [];
  const sparkOrigins: THREE.Vector3[] = [];
  const side = slot.local % 2 === 0 ? 1 : -1;
  for (const [a, z] of [
    [Math.PI / 2 + side * 0.9, -len * 0.3],
    [Math.PI / 2 - side * 1.25, -len * 0.75],
  ] as const) {
    const built = buildArm(kit, a, z, slot.index * 13 + arms.length);
    group.add(built.root);
    arms.push(built.arm);
    sparkOrigins.push(new THREE.Vector3(Math.cos(a) * 1.4, Math.sin(a) * 1.4 - 0.6, z));
  }
  group.add(buildSparks(rand, sparkOrigins, 140, forgeSparkMaterial(kit)));

  // Laser gate on the downbeat module: beams cross the tunnel as chords of the ring.
  const beams: THREE.Mesh[] = [];
  if (slot.downbeat) {
    for (let i = 0; i < 6; i++) {
      const beam = new THREE.Mesh(kit.cyl, kit.glows.orange.mat);
      const a = (i / 6) * Math.PI + 0.26;
      const off = (i % 2 ? 1 : -1) * (1.6 + (i % 3) * 1.1);
      beam.position.set(-Math.sin(a) * off, Math.cos(a) * off, -len / 2 - i * 0.3);
      beam.rotation.z = a - Math.PI / 2;
      const chord = 2 * Math.sqrt(R * R - off * off);
      beam.scale.set(0.035, chord, 0.035);
      group.add(beam);
      beams.push(beam);
    }
  }

  return {
    group,
    update(t) {
      const c4 = cycle(kit.loop, t.beat, 4) * Math.PI * 2;
      const c2 = cycle(kit.loop, t.beat, 2) * Math.PI * 2;
      for (const arm of arms) {
        const ph = arm.seed * 1.7;
        arm.shoulder.rotation.x = 0.35 * Math.sin(c4 + ph);
        arm.shoulder.rotation.z = 0.25 * Math.sin(c4 + ph * 0.6 + 1.0);
        arm.elbow.rotation.x = -0.5 + 0.45 * Math.sin(c2 + ph);
        arm.wrist.rotation.x = 0.4 * Math.sin(c2 * 2 + ph);
      }
      beams.forEach((b, i) => {
        // Beams switch on sixteenth notes. stepNoise repeats with the loop.
        b.visible = stepNoise(kit.loop, t.beat, 4, slot.index * 31 + i) > 0.35;
      });
    },
  };
};
