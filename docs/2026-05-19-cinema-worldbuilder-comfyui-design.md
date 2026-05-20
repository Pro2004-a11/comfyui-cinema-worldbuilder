# Cinema Worldbuilder — ComfyUI Node Pack — Design Spec

**Date:** 2026-05-19
**Status:** Approved for implementation (spec v2 — revised after 3-agent review)
**Project:** `comfyui-cinema-worldbuilder`
**Install target:** `D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder\`

> **v2 changelog** — revised after three parallel agent reviews (ComfyUI V3 API,
> LTX pipeline, architecture/scope): node API corrected from V1 to true V3; `fps`
> no longer wired (INT/FLOAT link bug); `MAX_FRAMES` 121→97; `runtime_seconds` cap
> 6.0→4.0; LTX models made an explicit prerequisite; `MODE_LABEL_TO_KEY` and named
> default constants added; banned-audio moved to `validate_inputs`; no-names/brand/
> age-blind drop acknowledged as a v1 cut.

---

## 1. Overview

`cinema-worldbuilder` is a Claude skill that composes cinematic text prompts for the
Seedance video model (run on Higgsfield). It is a pure prompt-director: it picks one of
five locked "cinema modes", fills a canonical ARRI/Panavision camera recipe, enforces a
diegetic-audio rule (no music), and outputs a structured paragraph the user pastes into
Seedance. It never renders anything.

This project ports that grammar **into ComfyUI as a custom-node pack**, so a user can
author a cinematic video prompt directly in the ComfyUI graph — picking mode and lens
from dropdowns, typing the scene — and run it through the local **LTX 2.3** video
pipeline to produce an actual `.mp4` with native diegetic audio. No Higgsfield, no
Claude, no cloud GPU.

The deliverable is a standalone ComfyUI plugin: three custom nodes plus one ready-made
example workflow.

## 2. Goals / Non-Goals

**Goals (v1)**
- Three ComfyUI custom nodes, true **V3 API** (see §5), encoding the cinema grammar.
- The grammar (5 modes, canonical camera blocks, lens list, audio templates, default
  constants, label↔key map) lives as plain data, decoupled from node code.
- Frame-count output valid for LTX 2.3 and safe for a 12 GB RTX 4070 Ti.
- The diegetic-audio "no music" rule enforced in-graph (pre-execution validation).
- One loadable example workflow wiring the nodes into the proven LTX 2.3 t2v pipeline,
  verified to render a video end-to-end.

**Non-Goals (v1 — explicit cuts)**
- **No Claude skill.** A Claude-side companion (image reading, prose authoring, mode
  auto-selection, the source skill's 5-line pre-prompt confirmation) is deferred to v2.
  The 5-line confirmation is an LLM conversational gate with no analogue in a node graph.
- **No multi-shot / N-shot sequences.** One graph = one LTX latent = one continuous
  clip. Stitched multi-shot prompts are a documented limitation; N shots = N graphs +
  post-concatenation by the user.
- **No i2v example workflow.** The nodes are model-agnostic (they emit strings + ints),
  so they already function in a hand-built image-to-video graph; a pre-wired two-pass
  i2v example is v2.
- **No reference-image reading.** That required an LLM; it belongs to the v2 Claude skill.
- **No programmatic name / brand / age-blind enforcement.** The source skill marks
  no-character-names, no-brand-names, and age-blind language as CRITICAL rules. The three
  prose inputs of `CinemaPromptComposer` are free text the user types directly, so these
  cannot be enforced the way the no-music rule is. v1 documents the rules in the README
  and node tooltips only; a `[WARN]`-only `PROSE_DISCOURAGED` substring check is v2.
- **No bilingual (EN+ZH) output.**
- No "do-everything" mega-node; exactly three focused nodes.

## 3. Architecture

A single ComfyUI custom-node package, registered with the **V3 extension API**.

```
comfyui-cinema-worldbuilder/
├── __init__.py              # CinemaWorldbuilderExtension(ComfyExtension) + comfy_entrypoint()
├── nodes.py                 # the 3 io.ComfyNode classes (thin V3 adapter)
├── cinema_grammar.py        # mode tables, blocks, lens list, defaults, label map, pure functions
├── pyproject.toml           # see §8.2 for required fields
├── README.md
├── docs/
│   └── 2026-05-19-cinema-worldbuilder-comfyui-design.md   # this file
├── tests/
│   └── test_cinema_grammar.py   # pure-function unit tests (no ComfyUI import)
└── example_workflows/
    └── cinema_ltx23_t2v.json    # LTX 2.3 t2v graph with the 3 nodes pre-wired
```

No `requirements.txt` — `cinema_grammar.py` is pure stdlib; the omission is deliberate.
No `WEB_DIRECTORY` — the nodes have no frontend JavaScript.

**Separation of concerns.** `cinema_grammar.py` is pure data and pure functions (frame
math, audio assembly, block templating, label parsing) — independently unit-testable
with **no ComfyUI import**. `nodes.py` is a thin V3 adapter: it declares schemas and
calls into `cinema_grammar`. This keeps the testable logic free of the ComfyUI runtime.

**V3 registration.** `__init__.py` defines `CinemaWorldbuilderExtension(ComfyExtension)`
whose `get_node_list()` returns the three node classes, plus a module-level
`async def comfy_entrypoint()` returning an instance. There is **no**
`NODE_CLASS_MAPPINGS` (that is the V1 mechanism).

All three nodes set `category="Cinema Worldbuilder"`. `node_id`s are project-prefixed to
avoid global collision: `CinemaWorldbuilder_CameraBlock`, `CinemaWorldbuilder_AudioLine`,
`CinemaWorldbuilder_PromptComposer`; friendly `display_name`s are "Cinema Camera Block"
etc.

## 4. The Grammar Module — `cinema_grammar.py`

Plain data and stateless functions. No ComfyUI imports.

### 4.1 Data

- `MODES` — dict keyed `M1`…`M5`, each: `label`, `body`, `lens_family`, `camera_block`
  — the canonical drop-in paragraph from the source skill, with `{lens}`, `{runtime}`,
  `{palette}`, `{stage_lighting}` placeholders. The five blocks are copied verbatim from
  `cinema-worldbuilder/SKILL.md` (Modes 1–5).
- `MODE_CHOICES` — ordered display labels for the COMBO, e.g.
  `["M1 — Narrative", "M2 — Studio", "M3 — Action", "M4 — Performance", "M5 — Atmospheric"]`.
- `MODE_LABEL_TO_KEY` — dict mapping each display label → its `M1`…`M5` key. The COMBO
  yields a label; the node maps it to a key before lookup. This mapping is named data,
  not improvised in `nodes.py`.
- `LENS_CHOICES` — `["32", "35", "40", "50", "55", "75", "85", "100"]` (mm). Entries are
  **strings by design**: a ComfyUI COMBO is always string-valued, and the lens is only
  substituted into a text template — no numeric round-trip needed.
- `AUDIO_BANNED` — lowercase substrings forbidden in a diegetic audio line: `music`,
  `song`, `lyric`, `soundtrack`, `score`, `melody`, `beat drop`, `orchestral`,
  `synth pad`, `vocals`. (Extendable.)
- `AUDIO_TEMPLATE` — `"Audio: diegetic only — {sounds}, no music, {dialogue_clause}."`
- `PALETTE_DEFAULT` — `"neutral desaturated grade (default — no palette specified)"`.
- `STAGE_LIGHTING_DEFAULT` — `"neutral white stage wash (default — no stage lighting specified)"`.
- `FPS_CHOICES` — `["24", "25", "30"]`; default `"24"`. The source grammar is 24 fps
  throughout; a constrained set prevents degenerate frame math (e.g. fps=1).
- `MAX_FRAMES = 97` — hard ceiling for a single LTX 2.3 latent on a 12 GB RTX 4070 Ti
  (`97 = 8·12 + 1`; ≈ 4.04 s at 24 fps). This is the only proven t2v frame count at this
  model scale in `comfy_workflows`. `121` is documented there only for i2v on a 5090 —
  not a safe t2v default here.
- `MIN_FRAMES = 9` (`8·1 + 1`).

### 4.2 Functions

- `snap_frames(runtime_seconds: float, fps: int) -> (frame_count: int, runtime_actual: float)`
  `EmptyLTXVLatentVideo.length` has the live constraint `min=1, step=8` — i.e. valid
  values are `8k + 1`. Compute:
  ```
  raw    = runtime_seconds * fps
  k      = round((raw - 1) / 8)
  frames = clamp(8*k + 1, MIN_FRAMES, MAX_FRAMES)
  runtime_actual = frames / fps          # float division
  ```
  Snapping rounds to the **nearest** valid `8k+1`, so `runtime_actual` may differ from
  the request by up to ~0.33 s at 24 fps (half of 8 frames). `runtime_actual` is the
  honest number and is what gets baked into the camera-block text downstream.

- `parse_mode_label(label: str) -> str` — `MODE_LABEL_TO_KEY[label]`; raises
  `ValueError(f"unknown mode label: {label}")` on a bad label.

- `build_camera_block(mode_key, lens_mm, runtime_actual, palette, stage_lighting) -> str`
  Raises `ValueError(f"unknown mode: {mode_key}")` on a bad key. Fills the mode's
  `camera_block` template. `palette` (required by M3/M5) and `stage_lighting` (required
  by M4): when the relevant field is blank, substitutes `PALETTE_DEFAULT` /
  `STAGE_LIGHTING_DEFAULT` **and** emits a `print("[WARN] ...")` line so the degraded
  behavior is visible in the console, not just buried in output text. Placeholders not
  used by the chosen mode are dropped.

- `build_audio_line(sounds: str, spoken_dialogue: bool) -> str`
  Splits `sounds` on newlines/commas, strips, drops empties. Validates the **cleaned**
  list (and the joined string) against `AUDIO_BANNED` (case-insensitive); raises
  `ValueError` naming the offending token if any match. `dialogue_clause` is
  `"no dialogue except what is physically spoken in frame"` when `spoken_dialogue` is
  false, else `"dialogue limited to what is physically spoken in frame"`. Optional string
  arguments default to `""` (never a mutable default).

- `compose_prompt(style_and_mood, dynamic_description, static_description, camera_block, audio_line="") -> str`
  Joins into one continuous paragraph, fixed order, plain-text labels:
  `Style & Mood: … Dynamic Description: … Static Description: … {camera_block} {audio_line}`.
  Labels are plain text (no Markdown `**`) — the string feeds a CLIP text encoder, where
  `**` tokenizes as literal noise. A **blank prose input drops its entire label** (no
  empty `"Style & Mood: ."`); a blank `audio_line` is omitted cleanly. Internal newlines
  collapse to single spaces.

## 5. The Nodes — `nodes.py`

True ComfyUI **V3 API**. Each node inherits `io.ComfyNode` and implements two
classmethods: `define_schema(cls) -> io.Schema` and `execute(cls, ...) -> io.NodeOutput`.
Inputs are `io.<Type>.Input(...)` objects in `io.Schema(inputs=[...])`; outputs are
`io.<Type>.Output(...)` objects in `io.Schema(outputs=[...])`; `execute` returns
`io.NodeOutput(...)`. `execute` parameter names must equal the input ids. There is no
`INPUT_TYPES` dict and no `RETURN_TYPES`/`RETURN_NAMES`.

In the tables below the **Type** column names the V3 io class: `COMBO`→`io.Combo`,
`STRING`→`io.String`, `INT`→`io.Int`, `FLOAT`→`io.Float`, `BOOLEAN`→`io.Boolean`.

All three nodes are pure deterministic functions of their inputs: default value-based
caching is correct — no `fingerprint_inputs`/`IS_CHANGED`, no `not_idempotent`.

### 5.1 `CinemaCameraBlock` — the grammar engine
`node_id = CinemaWorldbuilder_CameraBlock`

| | id | Type | Notes |
|---|---|---|---|
| in | `mode` | COMBO | `options=MODE_CHOICES`, `default="M1 — Narrative"` |
| in | `lens_mm` | COMBO | `options=LENS_CHOICES`, `default="50"` |
| in | `runtime_seconds` | FLOAT | `default=4.0, min=0.5, max=4.0, step=0.5` |
| in | `fps` | COMBO | `options=FPS_CHOICES`, `default="24"` |
| in (opt) | `palette` | STRING | M3/M5 — palette words + hex; default `""` |
| in (opt) | `stage_lighting` | STRING | M4 — stage-light colour cast; default `""` |
| out | `camera_block` | STRING | filled canonical block |
| out | `frame_count` | INT | `8k+1`, clamped to `[9, 97]` |
| out | `fps` | INT | the parsed fps, for optional manual rewiring |
| out | `runtime_actual` | FLOAT | `frame_count / fps` |

`execute`: `key = parse_mode_label(mode)`; `fps_int = int(fps)`;
`frame_count, runtime_actual = snap_frames(runtime_seconds, fps_int)`;
`camera_block = build_camera_block(key, lens_mm, runtime_actual, palette, stage_lighting)`.
The runtime baked into `camera_block` is `runtime_actual` — single source of truth.

### 5.2 `CinemaAudioLine` — diegetic-audio guardrail
`node_id = CinemaWorldbuilder_AudioLine`

| | id | Type | Notes |
|---|---|---|---|
| in | `sounds` | STRING | `multiline=True`; one sound per line or comma-separated |
| in | `spoken_dialogue` | BOOLEAN | `default=False` |
| out | `audio_line` | STRING | assembled diegetic audio line |

Validation: a `validate_inputs(cls, sounds, spoken_dialogue)` classmethod scans `sounds`
for `AUDIO_BANNED` substrings and returns an error **string** (naming the token) instead
of `True` when one is found. This runs in ComfyUI's validation phase, **before** any
node executes — so a music reference fails the graph cleanly, with no traceback and
before the expensive LTX sampler runs. `cinema_grammar.build_audio_line` keeps its
`ValueError` as the library-level invariant and unit-test target; `execute` calls it
normally (the `validate_inputs` pass has already guaranteed clean input for widget data).

### 5.3 `CinemaPromptComposer` — the assembler
`node_id = CinemaWorldbuilder_PromptComposer`

| | id | Type | Notes |
|---|---|---|---|
| in | `style_and_mood` | STRING | `multiline=True` |
| in | `dynamic_description` | STRING | `multiline=True` |
| in | `static_description` | STRING | `multiline=True` |
| in | `camera_block` | STRING | `force_input=True` — from `CinemaCameraBlock` |
| in (opt) | `audio_line` | STRING | `force_input=True` — from `CinemaAudioLine`; default `""` |
| out | `prompt` | STRING | single continuous paragraph → `CLIPTextEncode.text` |

## 6. Graph Data Flow

```
CinemaCameraBlock ─ camera_block ─────────────────────────┐
                  ─ frame_count (INT) ─┬─► EmptyLTXVLatentVideo.length   (INT)
                                       └─► LTXVEmptyLatentAudio.frames_number (INT)
                  ─ fps (INT) ............ not wired in the example (see below)
CinemaAudioLine    ─ audio_line ──────────────────────────┐
CinemaPromptComposer (camera_block + audio_line + 3 prose) ┘
                  └─ prompt ─► CLIPTextEncode (positive) ─► LTX 2.3 sampler ─► SaveVideo
```

`frame_count` is one `8k+1` INT feeding both latent nodes — both inputs are INT, and the
proven recipe uses the same count for video and audio (97/97), so a single shared output
is correct. `LTXVEmptyLatentAudio.frames_number` is `step=1, max=1000`; it *accepts* any
integer — passing the video count is a deliberate A/V-duration-lock choice, not a schema
requirement.

**`fps` is NOT wired in the example workflow.** The three fps consumers have mismatched
types — `LTXVConditioning.frame_rate` is FLOAT, `LTXVEmptyLatentAudio.frame_rate` is INT,
`CreateVideo.fps` is FLOAT — and ComfyUI will not connect an INT output to a FLOAT input
slot. The example bakes literal widget values (`24` / `24.0`) into all three, exactly as
the proven recipe does. The node's `fps` output exists only for advanced users who
rewire manually; the fps COMBO's job is to feed the frame math, not the graph.

The negative prompt is a plain `CLIPTextEncode` the user fills — not a cinema node.

## 7. Example Workflow — `cinema_ltx23_t2v.json`

UI-format (graph) JSON, loadable via ComfyUI's Open. It is the proven **LTX 2.3 t2v**
pipeline from `comfy_workflows` (single-pass), with the three Cinema nodes pre-wired in
front of the positive `CLIPTextEncode` and into the latent inputs per §6.

Node chain: `CheckpointLoaderSimple` + `LoraLoaderModelOnly` (distilled) +
`LTXAVTextEncoderLoader` (consumes `text_encoder`, `ckpt_name`, `device`) +
`LTXVAudioVAELoader` (consumes `ckpt_name`) → `CLIPTextEncode` ×2 (pos/neg) →
`LTXVConditioning` → `EmptyLTXVLatentVideo` + `LTXVEmptyLatentAudio` →
`LTXVConcatAVLatent` → `SamplerCustomAdvanced` → `LTXVSeparateAVLatent` →
`VAEDecodeTiled` + `LTXVAudioVAEDecode` → `CreateVideo` → `SaveVideo`.

Fixed example values, chosen for the 4070 Ti (not as fallbacks):
- Resolution **768×512** (the proven t2v resolution).
- `VAEDecodeTiled.temporal_size` **64** — the recipe's `4096` decodes all frames at once
  and will VRAM-spike on 12 GB; `64` tiles the temporal decode.
- `fps` literals `24` / `24.0` across `LTXVConditioning`, `LTXVEmptyLatentAudio`,
  `CreateVideo`.

### 7.1 Model prerequisites (BLOCKING)

These three files are **not installed on this machine today** — the example cannot
render until they are present. They are a stated prerequisite, not a run-time fixup:

- Checkpoint: `ltx-2.3-22b-dev-fp8.safetensors` → `models/checkpoints/`
- Distilled LoRA: `ltx-2.3-22b-distilled-lora-384.safetensors` → `models/loras/`
- Text encoder for `LTXAVTextEncoderLoader` — `comfy_workflows` names
  `gemma_3_12B_it_fp4_mixed.safetensors`, but that file is **not present** in the live
  `LTXAVTextEncoderLoader.text_encoder` options. Build step 4 pins the actual encoder
  name against live `/object_info` (or downloads the gemma encoder).

Use `comfy_local`'s model resolver / `findmodel` to source these from HuggingFace; they
are multi-GB downloads requiring explicit user confirmation.

## 8. Build Sequence

1. `cinema_grammar.py` — port the 5 mode tables and canonical blocks as data; add
   `MODE_LABEL_TO_KEY`, the default constants, `FPS_CHOICES`; implement `snap_frames`,
   `parse_mode_label`, `build_camera_block`, `build_audio_line`, `compose_prompt`.
2. `tests/test_cinema_grammar.py` — unit tests (§9); run green before touching nodes.
3. `nodes.py` + `__init__.py` (V3 extension registration) + `pyproject.toml` (§8.2).
4. Verify LTX models present via `/object_info` (§7.1); pin the text-encoder name.
   Restart ComfyUI; smoke-test: `/object_info` lists the three `CinemaWorldbuilder_*`
   nodes; run a `CinemaCameraBlock` and inspect outputs.
5. Build `example_workflows/cinema_ltx23_t2v.json`; run it end-to-end via `comfy_local`'s
   client; confirm an `.mp4` with audio renders.
6. `README.md` — install, the 3 nodes, the example, the v1 limitations (incl. the
   name/brand/age-blind rules that are documentation-only in v1).

### 8.2 `pyproject.toml`

`[project]` with `name`, `version` (start `0.1.0`), `description`, `license`,
`requires-python = ">=3.10"`; `[project.urls] Repository`; `[tool.comfy]` with
`PublisherId` and `DisplayName`. (Required for any future ComfyUI Registry publish; the
package functions locally without it, but `version` must be present.)

## 9. Testing

**Unit (pytest, pure functions — no ComfyUI import):**
- `snap_frames`: returns `8k+1`; clamps to `[9, 97]`; `runtime_actual` consistent;
  `4.0 s@24 → 97`, `15 s@24 → clamped to 97`, `0.5 s@24 → 9`.
- `parse_mode_label`: each label maps to its key; bad label raises `ValueError`.
- `build_audio_line`: a banned token (`"orchestral swell"`, `"music"`, …) raises naming
  it; whitespace-padded banned token still caught (validation on the cleaned list);
  clean input assembles correctly; `spoken_dialogue` toggles the dialogue clause.
- `build_camera_block`: each mode fills correctly; M3/M5 use `PALETTE_DEFAULT` and M4
  uses `STAGE_LIGHTING_DEFAULT` when blank (and the `[WARN]` is emitted); unused
  placeholders dropped; unknown `mode_key` raises `ValueError`.
- `compose_prompt`: fixed order; newlines collapsed; blank prose input drops its label;
  optional `audio_line` omitted cleanly.

**Smoke (live ComfyUI):**
- After install + restart, `/object_info` shows all three `CinemaWorldbuilder_*` nodes.
- The example workflow submitted via `comfy_client` completes and writes an `.mp4`
  (requires §7.1 models present).

## 10. Risks & Mitigations

- **OOM on 12 GB.** Mitigated by `MAX_FRAMES = 97` (the only stated mitigation — the
  `runtime_seconds` widget cap is just the UI reflection of it), the example's
  **768×512** resolution, and `VAEDecodeTiled.temporal_size = 64`. If 97 frames still
  OOMs, lower resolution before raising the cap.
- **LTX node-/parameter-name drift.** The example workflow is validated against live
  `/object_info` in build step 4–5; `comfy_workflows` lists known parameter-name traps.
- **Text-encoder name.** The `comfy_workflows` gemma name is not present locally; build
  step 4 pins the real name or downloads the encoder before the example is finalized.
- **fps INT/FLOAT type mismatch.** Resolved by not wiring `fps` and baking literals (§6).

## 11. Future (v2+)

- Claude companion skill: reference-image reading, prose authoring, mode auto-select,
  the 5-line pre-prompt confirmation, then fills these nodes / submits the workflow.
- `PROSE_DISCOURAGED` `[WARN]`-only check in `compose_prompt` for name/brand/age-blind
  language (symmetric with the audio guardrail, non-raising to avoid false-positive
  graph failures).
- i2v example workflow (two-pass: resize → `LTXVPreprocess` → dual `LTXVImgToVideoInplace`
  → `LTXVCropGuides`).
- Multi-shot: an ffmpeg post-concat path for N-shot sequences.
- Bilingual EN+ZH output.
