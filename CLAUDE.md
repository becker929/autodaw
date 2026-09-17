# CLAUDE.md — autodaw workspace

autodaw is a workspace for agent-assisted music production in Ableton Live 12. It holds several separate projects side by side. Each project has its own `pyproject.toml` and its own `.venv`. There is no shared Python package at the root.

## Repo state

The git index still tracks the old SerumEvolver code (`autodaw/`, `experiment_*.py`, a React frontend, a root `Makefile`). That code targeted REAPER and Serum. It is deleted from the working tree but the deletion is not committed. The current projects below are untracked.

Do not run `git add -A` or `git commit -a` here. That would commit hundreds of deletions plus private media and transcripts in one step. Stage explicit paths only, and ask Anthony before committing anything that changes what the repo tracks.

**Remote**: `autodaw` → `https://github.com/becker929/autodaw` (the remote is named `autodaw`, not `origin`).

## Layout

| Path | What it is |
|---|---|
| `hands/` | The main code project. DAW control layer for Ableton Live 12, plus the "vibe" feedback stack. See below. |
| `clap-poc/` | Proof of concept for fine-tuning the CLAP audio-text model (`laion/larger_clap_music`) on synthetic kick/hat audio. Read `clap-poc/REPORT.md` first. |
| `Marcin coaching/` | Lesson transcripts from 1-on-1 Ableton coaching. `INDEX.md` maps lessons to project files. `process_lessons.py` downloads from SwissTransfer and transcribes with whisper-cpp. |
| `dr1lmusic-transcripts/` | Transcripts of the dr1lmusic YouTube channel (hard techno tutorials). Built with `download_subtitles.sh` (yt-dlp) and `generate_markdown.py`. `index.md` lists all videos. |
| `research-guidance-UX` | Notes (Markdown, no extension) on music HCI literature and UX design for music software. |
| `compost` | Symlink to `~/_tmsmsm/daw-library/compost`. Outside this repo. Do not write through it without asking. |
| `Archive/` | Old experiments (REAPER, Serum, pymoo, pedalboard) and sample/demo folders. Git-ignored. Read-only reference. |
| `Live projects/` | Empty placeholder for Ableton project folders. |

The coaching and transcript folders are personal study material. Treat them as data. Do not publish them.

## hands

`hands` turns a declarative project config into Ableton Live actions:

```
ProjectConfig (JSON) → codegen → list[Step] → StepRunner → TCP → Ableton Live
```

`hands/README.md` has the module table and CLI reference. Key facts:

- Python 3.12+, managed with `uv`. Models are frozen Pydantic v2 in `src/hands/models.py`. JSON schemas in `schemas/` are generated from them.
- `src/hands/transport.py` defines the `McpTransport` protocol. `LiveMcpTransport` talks TCP to the Ableton MCP server on `127.0.0.1:16619`. `DryRunTransport` and `MockTransport` never touch Ableton.
- `hands build` is a dry run by default. `--no-dry-run` and `hands execute` change the open Live set. Confirm with Anthony before driving a live Ableton session.
- The Ableton crash-avoidance rules live in `hands/.cursor/skills/ableton-guide/SKILL.md`. Read it before writing any LOM (Live Object Model) code. `scripts/setup_letta_tools.py` reads that file by path, so do not move it. Keep it in sync with `~/.agents/skills/ableton-live-control/reference/lom-guide.md`.
- `sweeps/` maps device knobs to audio measures. Read `sweeps/README.md`, then `PLAN.md`, `STATUS.md`, and `HANDOFF.md`, in that order. The measuring tool (`ears`) is not in this repo. It lives at `~/_agent_scratch/ears_lab/`.
- `frontend/` is a Next.js app (the vibe UI). Secrets come from `frontend/.env`. Never print or commit it.

### Commands

Run these from `hands/`:

```bash
uv run pytest tests/ -v       # unit tests; fully offline via MockTransport
make build-python             # mypy type check
make build-frontend           # Next.js production build
make test-e2e                 # Cypress; starts and stops its own dev server
make start / make stop        # full vibe stack: Letta (Docker), vibe server, Ableton MCP bridge, frontend
make status                   # which services are running
```

The vibe stack uses ports 8283 (Letta), 8080 (vibe), 9010 (Ableton MCP bridge), and 3000 (frontend). Service logs go to `/tmp/vibe-*.log` and `/tmp/ableton-mcp-bridge.log`. `make watchdog` runs a self-healing monitor that is separate from `make start`; stop it with `make stop-watchdog`.

## clap-poc

Run the scripts by file path from `clap-poc/`. They use flat imports (`from synth import ...`), so `python -m src.train` does not work. `PYTORCH_ENABLE_MPS_FALLBACK=1` lets unsupported ops fall back to CPU on Apple Silicon.

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python src/smoke_test.py      # load model, run one inference
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python src/train.py --help    # e.g. --unfreeze-audio none|proj|full
PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/python src/benchmark.py       # M1 throughput and cloud cost estimate
```

Training runs on an M1 with 16 GB. `REPORT.md` records the memory limits found there. Large runs need a cloud GPU.

## Conventions

- Each project is self-contained. Do not import across `hands`, `clap-poc`, and the transcript tools. `hands` shares data with other tools only through the JSON schemas in `hands/schemas/`.
- Use `uv run` inside each project directory, so the right `.venv` is used.
- `.cursor/rules/phrasing.mdc` asks for a terse, factual tone with no cheerleading ("Great!", "Perfect!", "You're right!"). Follow it.
