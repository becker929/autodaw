// Frame pipeline: scene -> bloom (HDR) -> average of subframes -> tone map -> canvas.
// Averaging happens in linear HDR, before tone mapping. That is what makes bright streaks blur like film.
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { hash01, timeAt, type Loop } from "../core/timeline";
import type { World } from "./world";

const FULLSCREEN_VS = /* glsl */ `
  varying vec2 vUv;
  void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }
`;

const ACCUM_FS = /* glsl */ `
  uniform sampler2D tFrame;
  uniform float uWeight;
  varying vec2 vUv;
  void main() { gl_FragColor = vec4(texture2D(tFrame, vUv).rgb * uWeight, 1.0); }
`;

const FINAL_FS = /* glsl */ `
  uniform sampler2D tAccum;
  uniform vec2 uGrainSeed;
  uniform float uAberration;
  varying vec2 vUv;

  vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
  }
  float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
  }
  void main() {
    vec2 c = vUv - 0.5;
    float r2 = dot(c, c);
    // Chromatic aberration grows toward the frame edge, like a wide lens.
    vec2 off = c * r2 * uAberration;
    vec3 hdr = vec3(
      texture2D(tAccum, vUv + off).r,
      texture2D(tAccum, vUv).g,
      texture2D(tAccum, vUv - off).b);
    hdr *= 1.0 - 1.15 * r2;                       // vignette
    vec3 col = aces(hdr * 0.9);
    col = pow(col, vec3(1.0 / 2.2));
    // A toe: pull the darkest tones to true black. On an LED wall, a grey pedestal lights every pixel.
    col = max(col - 0.045, 0.0) / (1.0 - 0.045);
    // Grain also hides banding in the dark gradients after video compression.
    // Scaled by brightness, so black stays black.
    col += (hash(gl_FragCoord.xy + uGrainSeed) - 0.5) * 0.03 * smoothstep(0.0, 0.12, max(col.r, max(col.g, col.b)));
    gl_FragColor = vec4(col, 1.0);
  }
`;

// Sub-pixel camera offsets, one per subframe. A Halton sequence covers the pixel evenly.
function halton(i: number, base: number): number {
  let f = 1;
  let r = 0;
  while (i > 0) {
    f /= base;
    r += f * (i % base);
    i = Math.floor(i / base);
  }
  return r;
}

export interface Pipeline {
  renderFrame(frame: number): void;
}

export function buildPipeline(renderer: THREE.WebGLRenderer, world: World, loop: Loop): Pipeline {
  const { width, height, subframes } = loop.spec;
  const hdr = { type: THREE.HalfFloatType, depthBuffer: true, samples: 4 } as const;
  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(width, height, hdr));
  composer.renderToScreen = false;
  composer.addPass(new RenderPass(world.scene, world.camera));
  composer.addPass(new UnrealBloomPass(new THREE.Vector2(width, height), 0.22, 0.5, 1.5));

  const accum = new THREE.WebGLRenderTarget(width, height, { type: THREE.HalfFloatType, depthBuffer: false });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2));
  quad.frustumCulled = false;
  const quadScene = new THREE.Scene().add(quad);
  const quadCam = new THREE.Camera();

  const accumMat = new THREE.ShaderMaterial({
    uniforms: { tFrame: { value: null }, uWeight: { value: 1 / subframes } },
    vertexShader: FULLSCREEN_VS,
    fragmentShader: ACCUM_FS,
    blending: THREE.CustomBlending,
    blendEquation: THREE.AddEquation,
    blendSrc: THREE.OneFactor,
    blendDst: THREE.OneFactor,
    depthTest: false,
    depthWrite: false,
  });
  const finalMat = new THREE.ShaderMaterial({
    uniforms: {
      tAccum: { value: accum.texture },
      uGrainSeed: { value: new THREE.Vector2() },
      uAberration: { value: 0.018 },
    },
    vertexShader: FULLSCREEN_VS,
    fragmentShader: FINAL_FS,
    depthTest: false,
    depthWrite: false,
  });

  return {
    renderFrame(frame) {
      renderer.setRenderTarget(accum);
      renderer.setClearColor(0x000000, 1);
      renderer.clear();
      renderer.autoClear = false;
      for (let s = 0; s < subframes; s++) {
        world.update(timeAt(loop, frame, s));
        const jx = halton(s + 1, 2) - 0.5;
        const jy = halton(s + 1, 3) - 0.5;
        world.camera.setViewOffset(width, height, jx, jy, width, height);
        renderer.autoClear = true;
        composer.render();
        renderer.autoClear = false;
        accumMat.uniforms.tFrame!.value = composer.readBuffer.texture;
        quad.material = accumMat;
        renderer.setRenderTarget(accum);
        renderer.render(quadScene, quadCam);
      }
      world.camera.clearViewOffset();
      renderer.autoClear = true;
      // The grain pattern depends on the frame index inside the loop, so it also loops.
      const f = ((frame % loop.frames) + loop.frames) % loop.frames;
      (finalMat.uniforms.uGrainSeed!.value as THREE.Vector2).set(hash01(f) * 911, hash01(f + 7777) * 733);
      quad.material = finalMat;
      renderer.setRenderTarget(null);
      renderer.render(quadScene, quadCam);
    },
  };
}
