# Cinema Worldbuilder — ComfyUI Node Pack

Three ComfyUI nodes that bring the **cinema-worldbuilder** prompt grammar into the
graph — a locked cinematography vocabulary (five film modes, canonical ARRI /
Panavision camera recipes, diegetic-audio discipline) — and drive **local LTX 2.3**
video generation. Author a film-grade shot by picking a mode and lens and typing the
scene; out comes a single continuous-paragraph prompt wired straight into the LTX
pipeline.

## Install

The pack lives in `ComfyUI/custom_nodes/comfyui-cinema-worldbuilder/`. After placing
it there (or cloning it in), **restart ComfyUI**. On load you should see
`comfyui-cinema-worldbuilder` in the console with no `IMPORT FAILED`. If a workflow
says "Installation Required" for the Cinema nodes, hard-refresh the browser tab
(Ctrl+F5) — the frontend caches its node list at page load.

No third-party Python dependencies. Tests: `python -m pytest tests/ -v` (20 tests).

## The three nodes (category: **Cinema Worldbuilder**)

### Cinema Camera Block
Picks a film mode and fills its canonical camera recipe.
- **Inputs:** `mode` (`M1 - Narrative` / `M2 - Studio` / `M3 - Action` /
  `M4 - Performance` / `M5 - Atmospheric`), `lens_mm`, `runtime_seconds` (0.5–4.0),
  `fps` (24/25/30); optional `palette` (used by M3/M5), `stage_lighting` (used by M4).
- **Outputs:** `camera_block` (the filled recipe text), `frame_count` (an
  LTX-valid `8k+1` count, capped at 97 ≈ 4 s for a 12 GB GPU), `fps`,
  `runtime_actual`.

### Cinema Audio Line
Builds the diegetic audio line. Type the scene's real sounds (footsteps, rain,
fabric…). **Music is rejected** — any music/score/lyrics token fails the graph at
validation. `spoken_dialogue` toggles the dialogue clause.

### Cinema Prompt Composer
Assembles the final single-paragraph prompt from your `style_and_mood`,
`dynamic_description`, `static_description`, plus the `camera_block` and
`audio_line` wires. Its `prompt` output goes into a `CLIPTextEncode`.

Typical wiring: `CameraBlock` + `AudioLine` → `PromptComposer` → `CLIPTextEncode`
(positive) → LTX 2.3 sampler. `CameraBlock.frame_count` → `EmptyLTXVLatentVideo.length`
and `LTXVEmptyLatentAudio.frames_number`.

## Example workflows

In `example_workflows/` — each in two formats: `*.json` (API-prompt, for headless
submission) and `*_ui.json` (graph format, open in the ComfyUI canvas).

| Workflow | What it does |
|----------|--------------|
| `cinema_ltx23_t2v` | Text-to-video — the primary workflow. |
| `cinema_ltx23_i2v` | Image-to-video — a `LoadImage` first frame via `LTXVAddGuide`. |
| `cinema_ltx23_v2v` | Video-to-video refine — adapted from a known-good warp-refine graph. |

Load a `*_ui.json` in the canvas, edit the Cinema node widgets, hit Queue.
**i2v** needs an image in `ComfyUI/input/`; **v2v** needs a video there (see each
file's `_comment`).

### Required models (LTX 2.3 GGUF stack)

All loaded by the example workflows; confirmed present on the development machine:

- `models/unet/ltx-2.3-22b-distilled-1.1-Q2_K.gguf` (`UnetLoaderGGUF`)
- `models/text_encoders/` — `gemma-3-12b-it-IQ4_XS.gguf` + `ltx23_embeddings_connector.safetensors` (`DualCLIPLoaderGGUF`, type `ltxv`)
- `models/vae/ltx23_video_vae.safetensors`, `models/vae/ltx23_audio_vae.safetensors` (`VAELoaderKJ`)

`LTXVChunkFeedForward` (chunks=2) keeps the 22B model inside 12 GB VRAM.

## v1 limitations

- **One continuous clip per run** — no multi-shot / N-shot stitched sequences.
  For multiple shots, run multiple graphs and concatenate in post.
- **~4 s runtime cap** (97 frames at 24 fps) — the single-latent ceiling for
  LTX 2.3 22B on a 12 GB RTX 4070 Ti. Longer runtimes snap down to the cap.
- **Only the no-music rule is enforced.** The cinema-worldbuilder discipline also
  forbids character names, real brand names, and age words in the prose — those
  three are *author guidance* for the free-text fields, not enforced by the nodes.
  Keep prose descriptive (hair, wardrobe, role), brand-neutral, and age-blind.
- No Claude-side companion (reference-image reading, prose authoring, mode
  auto-selection) — that is a future addition.

## Layout

```
comfyui-cinema-worldbuilder/
├── __init__.py          # V3 ComfyExtension registration
├── nodes.py             # the 3 io.ComfyNode classes (thin adapters)
├── cinema_grammar.py    # mode tables, camera blocks, pure functions (no ComfyUI import)
├── tests/               # pytest unit tests for cinema_grammar
├── example_workflows/   # 3 workflows × API + UI format
└── docs/                # design spec + implementation plan
```
