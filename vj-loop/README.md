# vj-loop

vj-loop renders a seamless video loop for club visuals. The loop is a ride on a rail through a chrome factory, seen from the item on the sled. The default loop is 20 bars at 160 BPM. That is exactly 30 seconds, or 1800 frames at 60 frames per second.

The scene is built with three.js meshes and GLSL shaders. It renders in headless Chromium, one frame at a time, and ffmpeg encodes the frames to a video file. No frame depends on a clock, so a render is repeatable.

## Commands

Run these from `vj-loop/`.

```bash
npm ci
npm run check                                   # type check, unit tests, property tests
npm run seamcheck                               # pixel test of the loop seam; needs Chromium
npm run still -- 0,450,900 --width 1280 --height 720
npm run render                                  # full UHD render to out/factory-loop.mp4
npm run render -- --width 1280 --height 720 --subframes 4 --out out/preview.mp4
npm run render -- --codec prores               # 10-bit ProRes 422 HQ for editing
```

Chromium comes from Playwright. If it is missing, run `npx playwright install chromium`.

Rendered files go to `out/`. Git ignores that folder.

## Flags

**Loop flags** are checked by the Zod schema `LoopSpec` in `src/core/timeline.ts`: `--bpm`, `--bars`, `--beatsPerBar`, `--fps`, `--width`, `--height`, `--subframes`, `--shutter`, `--unitsPerBeat`.

**Render flags** are in `scripts/render.ts`: `--still`, `--out`, `--from`, `--to`, `--codec h264|hevc|prores`, `--crf`.

The loop must be a whole number of frames. `--bpm 140 --bars 16` is 27.43 seconds, which is not a whole number of frames at 60 fps, so the tool refuses it. The number of beats must also divide by four, because the track has four equal zones.

## How the loop closes

The track is a closed lap. One module of track is one beat long, so a ring passes the camera on every beat. The camera travels one full lap per loop. Modules wrap around the camera, so the view ahead at the end of the loop is the view ahead at the start.

Every moving part is driven by one of these helpers in `src/core/timeline.ts`:

- `cycle(loop, beat, n)` gives the position inside a repeating cycle of `n` beats. It throws if `n` does not divide the loop.
- `wave(t, turns)` is a sine with a whole number of turns per loop. It throws on a fraction.
- `stepNoise` is random-looking flicker that repeats with the loop.
- `relAhead` is the distance from the camera to a module on the circular track.

`Math.random` and clocks are not used anywhere. Random layout comes from the seeded generator `rng`.

## Layout

| Path | What it is |
|---|---|
| `src/core/` | Pure loop math and track layout. No three.js. Covered by `tests/`. |
| `src/scene/kit.ts` | Shared materials, glow colors, and builders for rings, rails, pipes and wall detail. |
| `src/scene/zones/` | The four zones: `iris` (iris gates), `forge` (robot arms, lasers, sparks), `nanite` (shader-driven swarm), `hall` (unfolding armor walls). |
| `src/scene/world.ts` | Builds the lap, the camera and the sled. Drives everything from a `Time`. |
| `src/scene/post.ts` | Bloom, subframe averaging for motion blur, tone mapping, grain. |
| `src/main.ts` | Page entry. Exposes `window.__vj` for the render script. |
| `scripts/session.ts` | Starts Vite and headless Chromium. |
| `scripts/render.ts` | Renders stills or pipes frames into ffmpeg. |
| `scripts/seamcheck.ts` | Black-box pixel test: determinism, loop closure, seam continuity. |

## Motion blur

Each output frame is the average of `--subframes` renders spread over the shutter interval. The average is taken in linear HDR, before tone mapping, so bright lights streak like they do on film. Each subframe also shifts the camera by less than a pixel, which smooths edges.
