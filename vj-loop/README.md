# vj-loop

vj-loop renders a seamless video loop for club visuals. The loop is a ride on a rail through a chrome factory, seen from the item on the sled. The default loop is 20 bars at 160 BPM. That is exactly 30 seconds, or 1800 frames at 60 frames per second.

The scene is built with three.js meshes and GLSL shaders. It renders in headless Chromium, one frame at a time, and ffmpeg encodes the frames to a video file. No frame depends on a clock, so a render is repeatable.

## Commands

Run these from `vj-loop/`.

```bash
npm ci
npm run check                                   # type check, unit tests, property tests
npm run seamcheck                               # pixel test: every zone closes after one lap; needs Chromium
npm run flashcheck                              # renders the loop small; checks flash rate and black level
npm run still -- 0,450,900 --width 1280 --height 720
npm run render                                  # full UHD render to out/factory-loop.mp4
npm run render -- --width 1280 --height 720 --subframes 4 --out out/preview.mp4
npm run render -- --codec prores               # ProRes 422 HQ in a .mov, for editing
npm run render -- --gop 1                      # every frame a keyframe: big file, instant seeking
```

Chromium comes from Playwright. If it is missing, run `npx playwright install chromium`.

Rendered files go to `out/`. Git ignores that folder.

## Flags

**Loop flags** are checked by the Zod schema `LoopSpec` in `src/core/timeline.ts`: `--bpm`, `--bars`, `--beatsPerBar`, `--fps`, `--width`, `--height`, `--subframes`, `--shutter`, `--unitsPerBeat`.

**Render flags** are checked in `scripts/flags.ts`: `--still`, `--out`, `--from`, `--to`, `--codec h264|hevc|prores`, `--crf`, `--gop`. The file extension of `--out` must match the codec: `.mp4` for h264 and hevc, `.mov` for prores.

A usage mistake prints one short message and exits with code 2. Nothing is rendered first.

The loop must be a whole number of frames. `--bpm 140 --bars 16` is 27.43 seconds, which is not a whole number of frames at 60 fps, so the tool refuses it. The number of beats must divide by 8. The track has four equal zones, and the scene animates on cycles of 1, 2, 4 and 8 beats. `validateSceneLoop` in `src/core/layout.ts` checks this before a browser starts.

## How the loop closes

The track is a closed lap. One module of track is one beat long, so a ring passes the camera on every beat. The camera travels one full lap per loop. Modules wrap around the camera, so the view ahead at the end of the loop is the view ahead at the start.

Every moving part is driven by one of these helpers in `src/core/timeline.ts`. Shaders never see raw time. They read the uniform `uCycles`, which holds the 1, 2, 4 and 8 beat cycle positions that `cycle` computed.

- `cycle(loop, beat, n)` gives the position inside a repeating cycle of `n` beats. It throws if `n` does not divide the loop.
- `wave(t, turns)` is a sine with a whole number of turns per loop. It throws on a fraction.
- `stepNoise` is random-looking flicker that repeats with the loop.
- `relAhead` is the distance from the camera to a module on the circular track.

`Math.random` and clocks are not used anywhere. Random layout comes from the seeded generator `rng`.

The camera stays at the origin and the track slides past it. This is called a floating origin. World positions then depend only on the wrapped track position, so the end of the loop matches the start to the bit. Shaders that need a position on the track add the uniform `uTrackZ` to world z. Any pattern indexed along the track must wrap its index by the number of cells per lap, as the panel shader in `src/scene/kit.ts` does.

`npm run seamcheck` proves this on pixels. It renders two probe frames inside each zone, and the same frames one lap later. It fails if any pixel differs by more than one level. Probing every zone matters, because a part that does not close is only visible while its zone is on screen.

## Layout

| Path | What it is |
|---|---|
| `src/core/` | Pure loop math and track layout. No three.js. Covered by `tests/`. |
| `src/scene/kit.ts` | Shared materials, glow colors, and builders for rings, rails, pipes and wall detail. |
| `src/scene/zones/` | The four zones: `iris` (iris gates), `forge` (robot arms, lasers, sparks), `nanite` (shader-driven swarm), `hall` (unfolding armor walls). |
| `src/scene/world.ts` | Builds the lap, the camera and the sled. Drives everything from a `Time`. |
| `src/scene/post.ts` | Bloom, subframe averaging for motion blur, tone mapping, grain. |
| `src/main.ts` | Page entry. Exposes `window.__vj` for the render script. |
| `src/core/flash.ts` | Pure flash and black-level analysis of a frame sequence. |
| `scripts/flags.ts` | Pure command-line parsing and render planning. Covered by `tests/`. |
| `scripts/session.ts` | Starts Vite and headless Chromium. Restarts the browser and retries a frame after a crash. |
| `scripts/render.ts` | Renders stills or pipes frames into ffmpeg. |
| `scripts/seamcheck.ts` | Black-box pixel test: determinism, and loop closure in every zone. |
| `scripts/flashcheck.ts` | Black-box pixel test: flashes per second and share of true black. |

## Video output

H.264 and HEVC files are tagged BT.709, limited range, with a keyframe every half second. Short keyframe gaps make seeking and looping fast in VJ software. The encode goes to a hidden `.partial-` file first. The final name appears only when the render succeeds.

The ProRes file is 10-bit, but the frames reach ffmpeg as 8-bit PNG, so it holds 8 bits of real precision.

The render page has hot reload and file watching turned off. Saving a source file during a render does not disturb it.

A frame is a pure function of its index, and renders do not depend on order. So if the page crashes, reloads, or loses its GPU context, the session starts a fresh browser and renders the same frame again. It prints a warning when it does. It gives up after two restarts on one frame. If ffmpeg stops early, the render stops at once with an error and removes the partial file.

## Club safety

The picture is made for an LED wall in a dark room. Two rules follow.

**Black is black.** The final pass pulls the darkest tones to zero, and grain is scaled by brightness. About half of all pixels in the loop are true black.

**Few large flashes.** Structure right beside the camera fades toward black, because it smears across a large part of the frame at random times. `npm run flashcheck` counts flashes the way broadcast photosensitivity guidance does (ITU-R BT.1702): a flash is a pair of opposite luminance changes of at least 0.1 over at least a quarter of the screen, and more than three in any second fails. The check is an estimate that catches regressions. It is not a certified Harding test.

## Motion blur

Each output frame is the average of `--subframes` renders spread over the shutter interval. The average is taken in linear HDR, before tone mapping, so bright lights streak like they do on film. Each subframe also shifts the camera by less than a pixel, which smooths edges.
