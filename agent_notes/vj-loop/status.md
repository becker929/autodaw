# vj-loop status

## Spec (pinned 2026-09-20)

- A seamless 30 second loop. A ride on a rail through a chrome factory, seen from the item on the sled.
- Built with three.js meshes and shaders. Anthony chose this over a pure raymarched shader and over Blender.
- The deliverable is a rendered mp4 only. No live page, no audio reactivity.
- Tempo is 160 BPM. 20 bars is exactly 30 seconds.
- Target is UHD (3840x2160) at 60 fps.
- Lives in `vj-loop/` on branch `feature/vj-loop`. Commit and push to the `autodaw` remote. No PR unless asked.

## Defaults I chose

- One track module per beat, so a ring passes on every beat. Four zones of five bars each.
- Rail speed is 9 units per beat. 12 was too fast to read the machines.
- 180 degree shutter with 8 subframes for the final render.
- H.264 at CRF 14 by default. ProRes and HEVC are flags.
- Franchise looks are described, not named: "shape-shifting armor", not a brand.

## Final render (2026-09-20)

- `vj-loop/out/factory-loop.mp4`: 3840x2160, 60 fps, 1800 frames, 30.000 s, H.264 High, yuv420p, BT.709 limited range, 143 Mbps, 538 MB.
- It took about 25 minutes on the M1 at about 0.83 s per frame, with 8 subframes. The browser did not restart during the render.
- The file is git-ignored. It lives only in the worktree `.worktrees/vj-loop/`. Copy it out before removing that worktree.

## Open items

- Docker was not running on 2026-09-20, so checks ran on the host, not in a container.
- The repo has no CI workflow. `npm run check` is the check. `npm run seamcheck` and `npm run flashcheck` need a GPU or software GL.
- Chrome reflections come from one baked environment map. They do not show neighboring machines.
- The render page crashed once ("Target crashed") at about frame 1200 of a small full-loop run on 2026-09-20. The cause is unknown. It did not repeat on the next run. The session now restarts the browser and retries the frame; that recovery is proven by killing the renderer process mid-render and getting a bit-identical video.
- H.264 at 4:2:0 softens thin neon lines (red and blue PSNR about 33 dB against the source, green about 42 dB). Use `--codec prores` when that matters.
- 143 Mbps UHD H.264 may be heavy to decode live next to other layers. Playback in VJ software was not tested. Re-encode with a higher `--crf`, or render at 1920x1080, if it stutters.
- VJ software often prefers HAP or DXV. ffmpeg here was not checked for a HAP encoder. `--gop 1` is the nearest option today.
- The flash check is an estimate, not a certified Harding test. Get a certified test before any broadcast use.

## Gotchas

- When killing a test browser, kill by exact PID. A pattern like "chrom" also matches the user's own Chrome tabs.
- Any shader pattern indexed along the track must wrap its index by the cells per lap. The panel shader once changed every panel's finish each lap, and only the seam test caught it.
- Do not drive a shader from raw time. Float rounding of a large beat value flipped one spark across its wrap. Pass cycle positions from `cycle()`.
