// Browser entry. The render script drives this page through window.__vj. Nothing here reads a clock.
import * as THREE from "three";
import { deriveLoop, LoopSpec } from "./core/timeline";
import { buildPipeline, type Pipeline } from "./scene/post";
import { buildWorld } from "./scene/world";

interface VjApi {
  /** Build the scene. Returns facts the render script logs and checks. */
  init(spec: unknown): { frames: number; seconds: number; gpu: string };
  /** Draw one output frame to the canvas. */
  renderFrame(frame: number): void;
  /** Draw one output frame and return it as a PNG data URL. */
  capture(frame: number): string;
}
declare global {
  interface Window {
    __vj: VjApi;
  }
}

let pipeline: Pipeline | null = null;
let gl: WebGLRenderingContext | WebGL2RenderingContext | null = null;
const canvas = document.getElementById("c") as HTMLCanvasElement;

window.__vj = {
  init(rawSpec) {
    const loop = deriveLoop(LoopSpec.parse(rawSpec));
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(1);
    renderer.setSize(loop.spec.width, loop.spec.height, false);
    renderer.toneMapping = THREE.NoToneMapping;
    const world = buildWorld(loop, renderer);
    pipeline = buildPipeline(renderer, world, loop);
    gl = renderer.getContext();
    const ext = gl.getExtension("WEBGL_debug_renderer_info");
    const gpu = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : "unknown";
    return { frames: loop.frames, seconds: loop.seconds, gpu };
  },
  renderFrame(frame) {
    if (!pipeline || !gl) throw new Error("init first");
    pipeline.renderFrame(frame);
    // A lost context draws nothing and raises no error. The frame would be black, so fail loudly instead.
    if (gl.isContextLost()) throw new Error(`The WebGL context was lost at frame ${frame}. The GPU was reset or ran out of memory.`);
  },
  capture(frame) {
    this.renderFrame(frame);
    return canvas.toDataURL("image/png");
  },
};
