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

## Open items

See the list at the end of this file. Update it when things change.

- Docker was not running on 2026-09-20, so checks ran on the host, not in a container.
- The repo has no CI workflow. `npm run check` is the check. `npm run seamcheck` needs a GPU or software GL.
- Chrome reflections come from one baked environment map. They do not show neighboring machines.
