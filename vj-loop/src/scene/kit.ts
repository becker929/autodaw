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
  /** Plain metals. Use these on parts that move, because the panel pattern below is fixed in world space. */
  chrome: THREE.MeshStandardMaterial;
  steel: THREE.MeshStandardMaterial;
  dark: THREE.MeshStandardMaterial;
  /** Metals with fine panel lines. Use these on static structure. */
  chromePanel: THREE.MeshStandardMaterial;
  steelPanel: THREE.MeshStandardMaterial;
  darkPanel: THREE.MeshStandardMaterial;
  glows: Record<keyof typeof COLORS, Glow>;
  box: THREE.BoxGeometry;
  cyl: THREE.CylinderGeometry;
  /** Shared shader uniforms. The world writes them once per render. */
  /** Positions inside the 1, 2, 4 and 8 beat cycles, from `cycle()`. Shaders must use these, never raw time. */
  uCycles: { value: THREE.Vector4 };
  /** Camera position on the track, wrapped to one lap. Shaders add it to world z to get track z. */
  uTrackZ: { value: number };
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

const PANEL_VERTEX = /* glsl */ `
  vec4 panelWorld = vec4(transformed, 1.0);
  #ifdef USE_INSTANCING
    panelWorld = instanceMatrix * panelWorld;
  #endif
  vPanelPos = (modelMatrix * panelWorld).xyz;
  vPanelPos.z += uTrackZ; // from camera-relative z to position on the track
`;

// Panel seams and per-panel finish, computed from world position at two scales.
// Both cell sizes divide the lap length, so the pattern is the same after a full lap.
const PANEL_FRAGMENT = /* glsl */ `
  {
    vec3 faceN = abs(normalize(cross(dFdx(vPanelPos), dFdy(vPanelPos))));
    float seam = 0.0;
    float finish = 0.0;
    for (int i = 0; i < 2; i++) {
      float cell = i == 0 ? uPanelCells.x : uPanelCells.y;
      vec3 q = vPanelPos / cell;
      vec3 w = clamp(fwidth(q) * 1.5, 0.0, 0.5);
      vec3 d = abs(fract(q) - 0.5);
      vec3 edge = smoothstep(0.5 - 0.035 - w, 0.5 - w * 0.5, d);
      // A seam only shows on faces it runs across, not on the face it is parallel to.
      float line = max(max(edge.x * (1.0 - faceN.x), edge.y * (1.0 - faceN.y)), edge.z * (1.0 - faceN.z));
      // Fade the fine scale out with distance so it never shimmers.
      float keep = 1.0 - smoothstep(0.15, 0.5, max(w.x, max(w.y, w.z)));
      vec3 id = floor(q);
      // Wrap the panel index along the track by the number of cells in one lap.
      // Without this, every panel would get a new finish each lap and the loop would not close.
      id.z = mod(id.z, i == 0 ? uPanelCells.z : uPanelCells.w);
      float h = fract(sin(dot(id, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
      seam = max(seam, line * keep * (i == 0 ? 1.0 : 0.6));
      finish += (h - 0.5) * keep * (i == 0 ? 0.6 : 0.4);
    }
    diffuseColor.rgb *= (1.0 - 0.7 * seam) * (1.0 + 0.35 * finish);
    roughnessFactor = clamp(roughnessFactor + 0.35 * seam + 0.22 * finish, 0.03, 1.0);
  }
`;

function withPanels(base: THREE.MeshStandardMaterial, cells: THREE.Vector4, uTrackZ: { value: number }): THREE.MeshStandardMaterial {
  const mat = base.clone();
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uPanelCells = { value: cells };
    shader.uniforms.uTrackZ = uTrackZ;
    shader.vertexShader = shader.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vPanelPos;\nuniform float uTrackZ;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\n" + PANEL_VERTEX);
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vPanelPos;\nuniform vec4 uPanelCells; // xy: cell sizes, zw: cells per lap")
      .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\n" + PANEL_FRAGMENT)
      // Structure right beside the camera is a fast, large smear. Left bright, it flashes a big part of the
      // frame at random times, which is the main photosensitivity risk. So it fades toward black up close.
      .replace("#include <fog_fragment>", "#include <fog_fragment>\ngl_FragColor.rgb *= mix(0.22, 1.0, smoothstep(2.5, 13.0, vFogDepth));");
  };
  mat.customProgramCacheKey = () => "panel-metal";
  return mat;
}

/** The largest cell size at or below `want` that divides `length` a whole number of times. */
export function cellDividing(length: number, want: number): number {
  return length / Math.ceil(length / want);
}

export function makeKit(loop: Loop): Kit {
  const chrome = new THREE.MeshStandardMaterial({ color: 0xf2f5f8, metalness: 1, roughness: 0.07 });
  const steel = new THREE.MeshStandardMaterial({ color: 0x9aa3ad, metalness: 1, roughness: 0.32 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x15181c, metalness: 0.9, roughness: 0.45 });
  const uTrackZ = { value: 0 };
  const cellA = cellDividing(loop.length, 0.62);
  const cellB = cellDividing(loop.length, 0.155);
  const cells = new THREE.Vector4(cellA, cellB, Math.round(loop.length / cellA), Math.round(loop.length / cellB));
  return {
    loop,
    chromePanel: withPanels(chrome, cells, uTrackZ),
    steelPanel: withPanels(steel, cells, uTrackZ),
    darkPanel: withPanels(dark, cells, uTrackZ),
    chrome,
    steel,
    dark,
    glows: {
      cyan: glow(COLORS.cyan, 1.5, 2.2),
      magenta: glow(COLORS.magenta, 1.5, 2.2),
      orange: glow(COLORS.orange, 1.8, 2.4),
      white: glow(COLORS.white, 1.2, 1.8),
    },
    box: new THREE.BoxGeometry(1, 1, 1),
    cyl: new THREE.CylinderGeometry(1, 1, 1, 16, 1),
    uCycles: { value: new THREE.Vector4() },
    uTrackZ,
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
  g.add(new THREE.Mesh(new THREE.TorusGeometry(r + 0.35, 0.32, 10, 64), kit.darkPanel));
  const lightRing = new THREE.Mesh(new THREE.TorusGeometry(r - 0.02, 0.035, 6, 96), light.mat);
  g.add(lightRing);
  const items: Placement[] = [];
  for (let i = 0; i < clamps; i++) {
    const a = ((i + 0.5) / clamps) * Math.PI * 2;
    items.push(onRing(r + 0.2, a, 0, 1.1, 0.7, 0.9));
    items.push(onRing(r + 0.05, a, 0, 0.35, 0.35, 1.3));
  }
  g.add(instancedBoxes(kit, kit.chromePanel, items));
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
  g.add(instancedBoxes(kit, kit.darkPanel, dark));
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
