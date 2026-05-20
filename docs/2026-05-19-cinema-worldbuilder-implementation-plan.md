# Cinema Worldbuilder ComfyUI Node Pack — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a ComfyUI custom-node pack that turns the cinema-worldbuilder prompt grammar into three drag-and-drop nodes driving the local LTX 2.3 video pipeline.

**Architecture:** Pure data + pure functions live in `cinema_grammar.py` (no ComfyUI import, unit-tested with pytest). `nodes.py` is a thin V3-API adapter (`io.ComfyNode`) that calls into the grammar module. `__init__.py` registers the three nodes via the V3 `ComfyExtension` mechanism. One example workflow wires the nodes into the proven LTX 2.3 t2v pipeline.

**Tech Stack:** Python 3.10+, ComfyUI V3 node API (`comfy_api.latest`), pytest, LTX 2.3 video model.

**Spec:** `docs/2026-05-19-cinema-worldbuilder-comfyui-design.md` (read it before starting).

**Project root:** `D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder\` — referred to below as `<ROOT>`. All commands run from `<ROOT>`.

**Source text for the camera blocks:** `C:\Users\yosir\Downloads\_cwb_inspect\cinema-worldbuilder\SKILL.md` (Modes 1–5). The finished templated blocks are reproduced verbatim in Task 2 — no need to open the source unless verifying.

---

## Task 1: Project skeleton

**Files:**
- Create: `<ROOT>\.gitignore`
- Create: `<ROOT>\pyproject.toml`
- Create: `<ROOT>\__init__.py` (empty stub)
- Create: `<ROOT>\README.md` (stub)
- Create: `<ROOT>\tests\__init__.py` (empty)

- [ ] **Step 1: Initialise git in the project folder**

Run: `git init` (from `<ROOT>`)
Expected: `Initialized empty Git repository`

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.pytest_cache/
projects/
```

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[project]
name = "comfyui-cinema-worldbuilder"
version = "0.1.0"
description = "Cinema Worldbuilder grammar as ComfyUI nodes for LTX 2.3 video prompting"
license = { text = "MIT" }
requires-python = ">=3.10"

[project.urls]
Repository = "https://github.com/yosir/comfyui-cinema-worldbuilder"

[tool.comfy]
PublisherId = "yosir"
DisplayName = "Cinema Worldbuilder"
```

- [ ] **Step 4: Create empty `__init__.py` and `tests\__init__.py`**

Both files are empty placeholders; real content lands in later tasks.

- [ ] **Step 5: Create `README.md` stub**

```markdown
# Cinema Worldbuilder — ComfyUI Node Pack

Three nodes that bring the cinema-worldbuilder grammar into ComfyUI for LTX 2.3
video prompting. See `docs/` for the design spec. Full README: Task 16.
```

- [ ] **Step 6: Commit**

```bash
git add .gitignore pyproject.toml __init__.py README.md tests/__init__.py
git commit -m "chore: project skeleton"
```

---

## Task 2: Grammar data — `cinema_grammar.py` constants

**Files:**
- Create: `<ROOT>\cinema_grammar.py`
- Test: `<ROOT>\tests\test_cinema_grammar.py`

- [ ] **Step 1: Write the failing test**

Create `tests\test_cinema_grammar.py`:

```python
import cinema_grammar as cg


def test_mode_data_integrity():
    assert len(cg.MODE_CHOICES) == 5
    for label in cg.MODE_CHOICES:
        assert label in cg.MODE_LABEL_TO_KEY
        key = cg.MODE_LABEL_TO_KEY[label]
        assert key in cg.MODES
    for key, mode in cg.MODES.items():
        for field in ("label", "body", "lens_family", "camera_block", "requires"):
            assert field in mode, f"{key} missing {field}"


def test_frame_bounds():
    assert cg.MIN_FRAMES == 9
    assert cg.MAX_FRAMES == 97
    assert (cg.MAX_FRAMES - 1) % 8 == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cinema_grammar.py -v` (from `<ROOT>`)
Expected: FAIL — `ModuleNotFoundError: No module named 'cinema_grammar'`

- [ ] **Step 3: Create `cinema_grammar.py` with all constants**

```python
"""Cinema Worldbuilder grammar — pure data and pure functions. No ComfyUI import."""

MAX_FRAMES = 97   # 8*12+1 — LTX 2.3 single-latent ceiling on a 12 GB RTX 4070 Ti
MIN_FRAMES = 9    # 8*1+1

FPS_CHOICES = ["24", "25", "30"]

LENS_CHOICES = ["32", "35", "40", "50", "55", "75", "85", "100"]

PALETTE_DEFAULT = "neutral desaturated grade (default - no palette specified)"
STAGE_LIGHTING_DEFAULT = "neutral white stage wash (default - no stage lighting specified)"

AUDIO_BANNED = [
    "music", "song", "lyric", "soundtrack", "score", "melody",
    "beat drop", "orchestral", "synth pad", "vocals",
]
AUDIO_TEMPLATE = "Audio: diegetic only - {sounds}, no music, {dialogue_clause}."

# Canonical camera blocks transcribed verbatim from cinema-worldbuilder/SKILL.md,
# with [XX]->{lens}/{runtime}, [palette descriptor]->{palette},
# [stage-lighting...]->{stage_lighting}.
MODES = {
    "M1": {
        "label": "M1 - Narrative",
        "body": "ARRI Alexa 35",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": [],
        "camera_block": (
            "Shot on ARRI Alexa 35 in ProRes 4444 LogC4, Panavision Ultra Vintage "
            "2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 filter, "
            "handheld with natural breath and slight shake, photoreal cinematic grit "
            "with oval bokeh and horizontal streak flares, warm anamorphic falloff "
            "toward frame edges, Kodak Vision3 250D film emulation grade with slight "
            "halation on highlights and 800 ASA grain structure, teal-amber color "
            "split with cool teal-blue shadows and warm amber highlights, organic "
            "lens breathing on focus racks, shallow depth of field, 24fps base "
            "shutter 180 degrees, total runtime roughly {runtime} seconds."
        ),
    },
    "M2": {
        "label": "M2 - Studio",
        "body": "ARRI Alexa Mini LF",
        "lens_family": "Cooke S4/i spherical",
        "requires": [],
        "camera_block": (
            "Shot on ARRI Alexa Mini LF in ProRes 4444 LogC4, Cooke S4/i spherical "
            "prime {lens}mm at T2 with Tiffen Black Pro-Mist 1/2 filter, locked-off "
            "tripod with optional 4-to-6 inch slow push-in, photoreal editorial "
            "fashion film aesthetic with gentle halation bloom on highlights and "
            "soft warm falloff in the Cooke signature, fine 400 ASA film grain "
            "structure retaining warmth in the shadows, highlights allowed to bloom "
            "slightly around fabric and chrome surfaces, saturated editorial grade "
            "with warm-retained blacks not crushed to pure black, slight skin tone "
            "warmth from the Cooke color rendition, 24fps base shutter 180 degrees, "
            "total runtime roughly {runtime} seconds. Not CGI, not plastic, "
            "shot-on-film analog aesthetic with real-world lens character."
        ),
    },
    "M3": {
        "label": "M3 - Action",
        "body": "ARRI Alexa 35",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": ["palette"],
        "camera_block": (
            "Shot on ARRI Alexa 35 in ProRes 4444 LogC4, Panavision Ultra Vintage "
            "2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 filter, "
            "all camera work is handheld and shaky throughout with constant operator "
            "micro-jitter, reactive movement, and chaotic shake, no stabilized or "
            "locked-off or dolly-smooth shots anywhere, gritty "
            "documentary-meets-sci-fi war film aesthetic with no stylization and "
            "everything grounded in physical realism, Kodak Vision3 250D film "
            "emulation with 800 ASA grain structure, {palette} with dusty "
            "atmospheric haze, slight halation on highlights, 24fps base shutter "
            "180 degrees, total runtime roughly {runtime} seconds."
        ),
    },
    "M4": {
        "label": "M4 - Performance",
        "body": "ARRI Alexa 35",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": ["stage_lighting"],
        "camera_block": (
            "Shot on ARRI Alexa 35 in ProRes 4444 LogC4, Panavision Ultra Vintage "
            "2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 filter, "
            "mixed handheld pit-photographer energy with rapid handhelds and shaky "
            "low-angle operator work and orbital handheld passes around the "
            "performers, hard cuts between angles, no stabilized or locked-off "
            "shots, photoreal concert documentary aesthetic, Kodak Vision3 250D "
            "film emulation with fine grain structure overlaid throughout, slightly "
            "desaturated cool tones with warm highlight bloom and deep blacks "
            "holding shadow detail, {stage_lighting}, heavy volumetric haze with "
            "dust suspended in every beam, real sweat sheen on skin and real fabric "
            "darkening from exertion, gentle halation on light sources, 24fps base "
            "shutter 180 degrees, total runtime roughly {runtime} seconds."
        ),
    },
    "M5": {
        "label": "M5 - Atmospheric",
        "body": "ARRI Alexa Mini LF",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": ["palette"],
        "camera_block": (
            "Shot on ARRI Alexa Mini LF in ProRes 4444 LogC4, Panavision Ultra "
            "Vintage 2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 "
            "filter, locked-off or extremely slow push-in motion only, no handheld "
            "energy, photoreal atmospheric environment plate aesthetic, Kodak "
            "Vision3 250D film emulation with fine 400 ASA grain structure, "
            "palette-driven grade with {palette}, strong negative space, deep depth "
            "of field, light atmospheric haze with dust particles suspended in air, "
            "weathered material detail with oxidized metal and dust-covered glass "
            "and cracked paint and moisture stains, slight anamorphic flares on any "
            "directional light sources, 24fps base shutter 180 degrees, total "
            "runtime roughly {runtime} seconds. No humans, no silhouettes, no "
            "living beings - the environment is the subject."
        ),
    },
}

MODE_CHOICES = [MODES[k]["label"] for k in ("M1", "M2", "M3", "M4", "M5")]
MODE_LABEL_TO_KEY = {MODES[k]["label"]: k for k in MODES}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cinema_grammar.py -v`
Expected: PASS — `test_mode_data_integrity`, `test_frame_bounds`

- [ ] **Step 5: Commit**

```bash
git add cinema_grammar.py tests/test_cinema_grammar.py
git commit -m "feat: cinema grammar data tables"
```

---

## Task 3: `snap_frames` function

**Files:**
- Modify: `<ROOT>\cinema_grammar.py`
- Test: `<ROOT>\tests\test_cinema_grammar.py`

- [ ] **Step 1: Write the failing test** — append to `tests\test_cinema_grammar.py`:

```python
def test_snap_frames_typical():
    frames, runtime = cg.snap_frames(4.0, 24)
    assert frames == 97
    assert abs(runtime - 97 / 24) < 1e-6


def test_snap_frames_clamps_high():
    frames, _ = cg.snap_frames(15.0, 24)
    assert frames == 97  # clamped to MAX_FRAMES


def test_snap_frames_clamps_low():
    frames, _ = cg.snap_frames(0.5, 24)
    assert frames == 9  # clamped to MIN_FRAMES


def test_snap_frames_is_always_8k_plus_1():
    for sec in (0.5, 1.0, 2.5, 3.0, 4.0):
        frames, _ = cg.snap_frames(sec, 24)
        assert (frames - 1) % 8 == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cinema_grammar.py::test_snap_frames_typical -v`
Expected: FAIL — `AttributeError: module 'cinema_grammar' has no attribute 'snap_frames'`

- [ ] **Step 3: Add `snap_frames` to `cinema_grammar.py`** (append at end of file):

```python
def snap_frames(runtime_seconds, fps):
    """Snap a requested runtime to a valid LTX 2.3 latent length (8k+1).

    EmptyLTXVLatentVideo.length has the live constraint min=1, step=8.
    Rounds to the NEAREST valid value, so runtime_actual may differ from the
    request by up to ~0.33 s at 24 fps. Returns (frame_count, runtime_actual).
    """
    raw = runtime_seconds * fps
    k = round((raw - 1) / 8)
    frames = max(MIN_FRAMES, min(8 * k + 1, MAX_FRAMES))
    runtime_actual = frames / fps
    return frames, runtime_actual
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cinema_grammar.py -v`
Expected: PASS — all `test_snap_frames_*` plus the Task 2 tests.

- [ ] **Step 5: Commit**

```bash
git add cinema_grammar.py tests/test_cinema_grammar.py
git commit -m "feat: snap_frames LTX frame-count math"
```

---

## Task 4: `parse_mode_label` function

**Files:**
- Modify: `<ROOT>\cinema_grammar.py`
- Test: `<ROOT>\tests\test_cinema_grammar.py`

- [ ] **Step 1: Write the failing test** — append:

```python
import pytest


def test_parse_mode_label_valid():
    assert cg.parse_mode_label("M3 - Action") == "M3"
    assert cg.parse_mode_label("M1 - Narrative") == "M1"


def test_parse_mode_label_bad():
    with pytest.raises(ValueError, match="unknown mode label"):
        cg.parse_mode_label("M9 - Nonsense")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cinema_grammar.py::test_parse_mode_label_valid -v`
Expected: FAIL — `AttributeError: ... has no attribute 'parse_mode_label'`

- [ ] **Step 3: Add `parse_mode_label`** (append to `cinema_grammar.py`):

```python
def parse_mode_label(label):
    """Map a MODE_CHOICES display label to its M1..M5 key."""
    try:
        return MODE_LABEL_TO_KEY[label]
    except KeyError:
        raise ValueError(f"unknown mode label: {label}") from None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cinema_grammar.py -v`
Expected: PASS — all tests.

- [ ] **Step 5: Commit**

```bash
git add cinema_grammar.py tests/test_cinema_grammar.py
git commit -m "feat: parse_mode_label"
```

---

## Task 5: `build_camera_block` function

**Files:**
- Modify: `<ROOT>\cinema_grammar.py`
- Test: `<ROOT>\tests\test_cinema_grammar.py`

- [ ] **Step 1: Write the failing test** — append:

```python
def test_build_camera_block_m1():
    block = cg.build_camera_block("M1", "55", 4.04, "", "")
    assert "55mm" in block
    assert "roughly 4.0 seconds" in block
    assert "ARRI Alexa 35" in block


def test_build_camera_block_m3_uses_palette():
    block = cg.build_camera_block("M3", "40", 3.0, "stormy desaturated palette", "")
    assert "stormy desaturated palette" in block


def test_build_camera_block_m3_default_palette(capsys):
    block = cg.build_camera_block("M3", "40", 3.0, "", "")
    assert cg.PALETTE_DEFAULT in block
    assert "[WARN]" in capsys.readouterr().out


def test_build_camera_block_m4_default_stage(capsys):
    block = cg.build_camera_block("M4", "55", 3.0, "", "")
    assert cg.STAGE_LIGHTING_DEFAULT in block
    assert "[WARN]" in capsys.readouterr().out


def test_build_camera_block_bad_mode():
    with pytest.raises(ValueError, match="unknown mode"):
        cg.build_camera_block("M9", "55", 3.0, "", "")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cinema_grammar.py::test_build_camera_block_m1 -v`
Expected: FAIL — `AttributeError: ... has no attribute 'build_camera_block'`

- [ ] **Step 3: Add `build_camera_block`** (append to `cinema_grammar.py`):

```python
def build_camera_block(mode_key, lens_mm, runtime_actual, palette, stage_lighting):
    """Fill the chosen mode's canonical camera block.

    Required fields per mode are listed in MODES[key]["requires"]. A blank
    required field falls back to a named default and prints a [WARN] line so the
    degraded behavior is visible. Placeholders not present in a block are ignored
    by str.format.
    """
    mode = MODES.get(mode_key)
    if mode is None:
        raise ValueError(f"unknown mode: {mode_key}")

    palette = palette.strip()
    stage_lighting = stage_lighting.strip()

    if "palette" in mode["requires"] and not palette:
        print(f"[WARN] cinema-worldbuilder: mode {mode_key} has no palette; "
              f"using default")
        palette = PALETTE_DEFAULT
    if "stage_lighting" in mode["requires"] and not stage_lighting:
        print(f"[WARN] cinema-worldbuilder: mode {mode_key} has no stage_lighting; "
              f"using default")
        stage_lighting = STAGE_LIGHTING_DEFAULT

    return mode["camera_block"].format(
        lens=lens_mm,
        runtime=f"{runtime_actual:.1f}",
        palette=palette,
        stage_lighting=stage_lighting,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cinema_grammar.py -v`
Expected: PASS — all tests.

- [ ] **Step 5: Commit**

```bash
git add cinema_grammar.py tests/test_cinema_grammar.py
git commit -m "feat: build_camera_block"
```

---

## Task 6: `build_audio_line` function

**Files:**
- Modify: `<ROOT>\cinema_grammar.py`
- Test: `<ROOT>\tests\test_cinema_grammar.py`

- [ ] **Step 1: Write the failing test** — append:

```python
def test_build_audio_line_clean():
    line = cg.build_audio_line("boots on gravel\nrain hiss, distant thunder", False)
    assert line.startswith("Audio: diegetic only - ")
    assert "boots on gravel" in line
    assert "rain hiss" in line
    assert "no music" in line
    assert "no dialogue except what is physically spoken in frame" in line


def test_build_audio_line_spoken_dialogue():
    line = cg.build_audio_line("footsteps", True)
    assert "dialogue limited to what is physically spoken in frame" in line


def test_build_audio_line_rejects_music():
    with pytest.raises(ValueError, match="orchestral"):
        cg.build_audio_line("footsteps, orchestral swell, wind", False)


def test_build_audio_line_rejects_padded_banned_token():
    with pytest.raises(ValueError, match="music"):
        cg.build_audio_line("footsteps\n   music   \nwind", False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cinema_grammar.py::test_build_audio_line_clean -v`
Expected: FAIL — `AttributeError: ... has no attribute 'build_audio_line'`

- [ ] **Step 3: Add `build_audio_line`** (append to `cinema_grammar.py`):

```python
def build_audio_line(sounds, spoken_dialogue):
    """Assemble the diegetic audio line. Raises ValueError if a banned (music)
    token appears in any cleaned sound entry."""
    items = [s.strip() for part in sounds.splitlines()
             for s in part.split(",")]
    items = [s for s in items if s]
    joined = ", ".join(items)
    haystack = joined.lower()
    for banned in AUDIO_BANNED:
        if banned in haystack:
            raise ValueError(
                f"banned audio token '{banned}' - the audio line is diegetic "
                f"only, no music/score/lyrics"
            )
    dialogue_clause = (
        "dialogue limited to what is physically spoken in frame"
        if spoken_dialogue
        else "no dialogue except what is physically spoken in frame"
    )
    return AUDIO_TEMPLATE.format(sounds=joined, dialogue_clause=dialogue_clause)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cinema_grammar.py -v`
Expected: PASS — all tests.

- [ ] **Step 5: Commit**

```bash
git add cinema_grammar.py tests/test_cinema_grammar.py
git commit -m "feat: build_audio_line with music-ban enforcement"
```

---

## Task 7: `compose_prompt` function

**Files:**
- Modify: `<ROOT>\cinema_grammar.py`
- Test: `<ROOT>\tests\test_cinema_grammar.py`

- [ ] **Step 1: Write the failing test** — append:

```python
def test_compose_prompt_full():
    out = cg.compose_prompt(
        "tense, observational",
        "she steps off the curb",
        "rose-pink haired woman in a white tank",
        "Shot on ARRI Alexa 35 ...",
        "Audio: diegetic only - rain, no music, no dialogue ...",
    )
    assert out.index("Style & Mood:") < out.index("Dynamic Description:")
    assert out.index("Dynamic Description:") < out.index("Static Description:")
    assert "\n" not in out
    assert "**" not in out


def test_compose_prompt_drops_blank_label():
    out = cg.compose_prompt("", "action here", "static here", "CAM", "")
    assert "Style & Mood:" not in out
    assert "Dynamic Description: action here" in out


def test_compose_prompt_omits_blank_audio():
    out = cg.compose_prompt("mood", "dyn", "stat", "CAM", "")
    assert out.rstrip().endswith("CAM")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cinema_grammar.py::test_compose_prompt_full -v`
Expected: FAIL — `AttributeError: ... has no attribute 'compose_prompt'`

- [ ] **Step 3: Add `compose_prompt`** (append to `cinema_grammar.py`):

```python
def _collapse(text):
    """Collapse whitespace/newlines in a free-text field to single spaces."""
    return " ".join(text.split())


def compose_prompt(style_and_mood, dynamic_description, static_description,
                   camera_block, audio_line=""):
    """Assemble the single continuous-paragraph prompt. Blank labelled prose
    sections are dropped entirely; a blank audio_line is omitted."""
    parts = []
    for label, value in (
        ("Style & Mood", style_and_mood),
        ("Dynamic Description", dynamic_description),
        ("Static Description", static_description),
    ):
        value = _collapse(value)
        if value:
            parts.append(f"{label}: {value}")
    camera_block = _collapse(camera_block)
    if camera_block:
        parts.append(camera_block)
    audio_line = _collapse(audio_line)
    if audio_line:
        parts.append(audio_line)
    return " ".join(parts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cinema_grammar.py -v`
Expected: PASS — all tests (full grammar module green).

- [ ] **Step 5: Commit**

```bash
git add cinema_grammar.py tests/test_cinema_grammar.py
git commit -m "feat: compose_prompt assembler"
```

---

## Task 8: `CinemaCameraBlock` node

**Files:**
- Create: `<ROOT>\nodes.py`

- [ ] **Step 1: Create `nodes.py` with the first node**

```python
"""ComfyUI V3 node adapters for the Cinema Worldbuilder grammar."""
from comfy_api.latest import io

from . import cinema_grammar as cg  # relative — avoids collision with ComfyUI's core nodes.py


class CinemaCameraBlock(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CinemaWorldbuilder_CameraBlock",
            display_name="Cinema Camera Block",
            category="Cinema Worldbuilder",
            description="Mode + lens + runtime -> canonical camera block + LTX frame count.",
            inputs=[
                io.Combo.Input("mode", options=cg.MODE_CHOICES,
                               default=cg.MODE_CHOICES[0]),
                io.Combo.Input("lens_mm", options=cg.LENS_CHOICES, default="50"),
                io.Float.Input("runtime_seconds", default=4.0, min=0.5, max=4.0,
                               step=0.5),
                io.Combo.Input("fps", options=cg.FPS_CHOICES, default="24"),
                io.String.Input("palette", multiline=True, optional=True,
                                default=""),
                io.String.Input("stage_lighting", multiline=True, optional=True,
                                default=""),
            ],
            outputs=[
                io.String.Output("camera_block"),
                io.Int.Output("frame_count"),
                io.Int.Output("fps"),
                io.Float.Output("runtime_actual"),
            ],
        )

    @classmethod
    def execute(cls, mode, lens_mm, runtime_seconds, fps, palette="",
                stage_lighting=""):
        key = cg.parse_mode_label(mode)
        fps_int = int(fps)
        frame_count, runtime_actual = cg.snap_frames(runtime_seconds, fps_int)
        camera_block = cg.build_camera_block(
            key, lens_mm, runtime_actual, palette or "", stage_lighting or "")
        return io.NodeOutput(camera_block, frame_count, fps_int, runtime_actual)
```

- [ ] **Step 2: Verify the file compiles**

Run: `python -m py_compile nodes.py`
Expected: no output, exit 0. (Behavioural verification happens after install — Task 12.)

- [ ] **Step 3: Commit**

```bash
git add nodes.py
git commit -m "feat: CinemaCameraBlock node"
```

---

## Task 9: `CinemaAudioLine` node

**Files:**
- Modify: `<ROOT>\nodes.py`

- [ ] **Step 1: Append `CinemaAudioLine` to `nodes.py`**

```python
class CinemaAudioLine(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CinemaWorldbuilder_AudioLine",
            display_name="Cinema Audio Line",
            category="Cinema Worldbuilder",
            description="Diegetic-only audio line. Rejects music/score/lyrics.",
            inputs=[
                io.String.Input("sounds", multiline=True, default=""),
                io.Boolean.Input("spoken_dialogue", default=False),
            ],
            outputs=[
                io.String.Output("audio_line"),
            ],
        )

    @classmethod
    def validate_inputs(cls, sounds, spoken_dialogue):
        """Pre-execution guard: fail the graph cleanly if music is referenced."""
        haystack = sounds.lower()
        for banned in cg.AUDIO_BANNED:
            if banned in haystack:
                return (f"Cinema Audio Line: banned token '{banned}' - the audio "
                        f"line is diegetic only, no music/score/lyrics.")
        return True

    @classmethod
    def execute(cls, sounds, spoken_dialogue):
        return io.NodeOutput(cg.build_audio_line(sounds, spoken_dialogue))
```

- [ ] **Step 2: Verify the file compiles**

Run: `python -m py_compile nodes.py`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add nodes.py
git commit -m "feat: CinemaAudioLine node with validate_inputs guard"
```

---

## Task 10: `CinemaPromptComposer` node

**Files:**
- Modify: `<ROOT>\nodes.py`

- [ ] **Step 1: Append `CinemaPromptComposer` to `nodes.py`**

```python
class CinemaPromptComposer(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CinemaWorldbuilder_PromptComposer",
            display_name="Cinema Prompt Composer",
            category="Cinema Worldbuilder",
            description="Assembles the single-paragraph Seedance-style prompt.",
            inputs=[
                io.String.Input("style_and_mood", multiline=True, default=""),
                io.String.Input("dynamic_description", multiline=True, default=""),
                io.String.Input("static_description", multiline=True, default=""),
                io.String.Input("camera_block", force_input=True),
                io.String.Input("audio_line", force_input=True, optional=True),
            ],
            outputs=[
                io.String.Output("prompt"),
            ],
        )

    @classmethod
    def execute(cls, style_and_mood, dynamic_description, static_description,
                camera_block, audio_line=""):
        return io.NodeOutput(cg.compose_prompt(
            style_and_mood, dynamic_description, static_description,
            camera_block, audio_line or ""))
```

- [ ] **Step 2: Verify the file compiles**

Run: `python -m py_compile nodes.py`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add nodes.py
git commit -m "feat: CinemaPromptComposer node"
```

---

## Task 11: V3 registration in `__init__.py`

**Files:**
- Modify: `<ROOT>\__init__.py`

- [ ] **Step 1: Replace `__init__.py` content**

```python
"""Cinema Worldbuilder — ComfyUI custom-node pack (V3 API)."""
from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from .nodes import CinemaCameraBlock, CinemaAudioLine, CinemaPromptComposer


class CinemaWorldbuilderExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [CinemaCameraBlock, CinemaAudioLine, CinemaPromptComposer]


async def comfy_entrypoint() -> CinemaWorldbuilderExtension:
    return CinemaWorldbuilderExtension()
```

- [ ] **Step 2: Verify it compiles**

Run: `python -m py_compile __init__.py`
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add __init__.py
git commit -m "feat: V3 extension registration"
```

---

## Task 12: Install smoke test

**Files:** none (verification only).

- [ ] **Step 1: Restart ComfyUI**

The pack is already inside `custom_nodes/`. Restart the ComfyUI server so it
loads the new pack (stop the running server, start it again — e.g. via
`D:\ComfyUI_windows_portable\run_nvidia_gpu.bat`). Watch the console for
`cinema-worldbuilder` import errors; there should be none.

- [ ] **Step 2: Confirm the three nodes registered**

Run:
```bash
curl -s http://localhost:8188/object_info/CinemaWorldbuilder_CameraBlock
curl -s http://localhost:8188/object_info/CinemaWorldbuilder_AudioLine
curl -s http://localhost:8188/object_info/CinemaWorldbuilder_PromptComposer
```
Expected: each returns a non-empty JSON object describing the node (not `{}` or 404).

- [ ] **Step 3: Functional smoke — run CinemaCameraBlock via the API**

Create `<ROOT>\tests\smoke_camera_block.json`:
```json
{
  "cam": {"class_type": "CinemaWorldbuilder_CameraBlock",
          "inputs": {"mode": "M1 - Narrative", "lens_mm": "55",
                     "runtime_seconds": 4.0, "fps": "24"}},
  "show": {"class_type": "PreviewAny", "inputs": {"source": ["cam", 0]}}
}
```
Submit it with the comfy_local client:
```bash
python "C:/Users/yosir/.claude/skills/comfy_local/scripts/comfy_client.py" run tests/smoke_camera_block.json
```
Expected: `prompt_id:` printed, job completes with no error. If `PreviewAny`
is unavailable on this install, instead submit only the `cam` node and confirm
`/history/{id}` shows status `success`.

- [ ] **Step 4: Commit the smoke fixture**

```bash
git add tests/smoke_camera_block.json
git commit -m "test: install smoke fixture"
```

---

## Task 13: Verify LTX 2.3 model prerequisites

**Files:** none (verification + recorded findings).

- [ ] **Step 1: Check which LTX models are installed**

Run:
```bash
python "C:/Users/yosir/.claude/skills/comfy_local/scripts/comfy_client.py" options CheckpointLoaderSimple ckpt_name
python "C:/Users/yosir/.claude/skills/comfy_local/scripts/comfy_client.py" options LoraLoaderModelOnly lora_name
python "C:/Users/yosir/.claude/skills/comfy_local/scripts/comfy_client.py" options LTXAVTextEncoderLoader text_encoder
```
Expected: note whether `ltx-2.3-22b-dev-fp8.safetensors`, `ltx-2.3-22b-distilled-lora-384.safetensors`, and an LTX text encoder are present.

- [ ] **Step 2: Resolve any missing model**

For each missing file, run the comfy_local resolver and present findings to the
user — do NOT download without confirmation (files are multi-GB):
```bash
python "C:/Users/yosir/.claude/skills/comfy_local/scripts/comfy_client.py" findmodel ltx-2.3-22b-dev-fp8
```
Record the exact installed names (especially the text encoder — the
`comfy_workflows` recipe names `gemma_3_12B_it_fp4_mixed.safetensors`, which may
not be present). These exact names are used as literals in Task 14.

- [ ] **Step 3: Record findings in the README models section** — note the
confirmed model filenames for the example workflow. (Committed with Task 16.)

---

## Task 14: Example workflow `cinema_ltx23_t2v.json`

**Files:**
- Create: `<ROOT>\example_workflows\cinema_ltx23_t2v.json`

- [ ] **Step 1: Build the UI-format workflow**

Create `example_workflows\cinema_ltx23_t2v.json` as a ComfyUI **graph (UI) format**
workflow. Base it on the proven LTX 2.3 t2v node chain in
`C:\Users\yosir\.claude\skills\comfy_workflows\skill.md` ("LTX 2.3 Text-to-Video —
Proven Pipeline"). Apply these project-specific changes:

- Add the three Cinema nodes: `CinemaWorldbuilder_CameraBlock`,
  `CinemaWorldbuilder_AudioLine`, `CinemaWorldbuilder_PromptComposer`.
- Wire `CinemaPromptComposer.prompt` → the **positive** `CLIPTextEncode.text`.
- Wire `CinemaCameraBlock.frame_count` → `EmptyLTXVLatentVideo.length` AND
  `LTXVEmptyLatentAudio.frames_number`.
- Wire `CinemaCameraBlock.camera_block` → `CinemaPromptComposer.camera_block`;
  `CinemaAudioLine.audio_line` → `CinemaPromptComposer.audio_line`.
- Do NOT wire `fps` — set literal `24` / `24.0` widget values on
  `LTXVConditioning.frame_rate`, `LTXVEmptyLatentAudio.frame_rate`, `CreateVideo.fps`.
- Set `EmptyLTXVLatentVideo` width=768, height=512.
- Set `VAEDecodeTiled.temporal_size` = 64 (not the recipe's 4096 — VRAM cap).
- Use the exact model filenames recorded in Task 13.
- Keep the negative `CLIPTextEncode` as a plain node with a short hand-written
  negative prompt.

- [ ] **Step 2: Validate node + input names against the live server**

For each LTX node in the workflow, confirm its type and input names exist:
```bash
python "C:/Users/yosir/.claude/skills/comfy_local/scripts/comfy_client.py" nodes | findstr LTX
```
Cross-check each node's inputs with `comfy_client.py` `object_info` calls. Fix any
name that diverges (`comfy_workflows` lists known parameter-name traps).

- [ ] **Step 3: Commit**

```bash
git add example_workflows/cinema_ltx23_t2v.json
git commit -m "feat: LTX 2.3 t2v example workflow with cinema nodes"
```

---

## Task 15: End-to-end render test

**Files:** none (verification only). Requires Task 13 models present.

- [ ] **Step 1: Convert the example to API format and submit**

The example is UI-format; convert it to API format (flat `{node_id: {class_type,
inputs}}`) — either by hand or via ComfyUI's "Save (API Format)" — saving as
`<ROOT>\tests\e2e_ltx23.json`. Submit it:
```bash
python "C:/Users/yosir/.claude/skills/comfy_local/scripts/comfy_client.py" run tests/e2e_ltx23.json 1800
```
Expected: `prompt_id:` printed, job completes, an output `.mp4` line printed.

- [ ] **Step 2: Confirm the video exists**

Check `D:\ComfyUI_windows_portable\ComfyUI\output\` for the rendered `.mp4`.
Expected: a playable video file with audio.

If the job OOMs: lower `EmptyLTXVLatentVideo` resolution before raising any cap;
re-run. Record the working resolution.

- [ ] **Step 3: Commit the e2e fixture**

```bash
git add tests/e2e_ltx23.json
git commit -m "test: end-to-end LTX render fixture"
```

---

## Task 16: README

**Files:**
- Modify: `<ROOT>\README.md`

- [ ] **Step 1: Write the full README**

Replace `README.md` with: install instructions (clone into `custom_nodes/`,
restart ComfyUI); the three nodes and their inputs/outputs; how to load the
example workflow; the confirmed LTX model filenames from Task 13; and the v1
limitations from the spec — single continuous clip only (no multi-shot),
~4 s max runtime on a 12 GB GPU, and that the no-character-names / no-brand-names
/ age-blind rules are author guidance for the prose fields, **not** enforced by
the nodes (only the no-music audio rule is enforced).

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: README"
```

---

## Self-Review Notes

- **Spec coverage:** §4 grammar data → Task 2; `snap_frames`/`parse_mode_label`/
  `build_camera_block`/`build_audio_line`/`compose_prompt` → Tasks 3–7; §5 three
  nodes → Tasks 8–10; §3 V3 registration → Task 11; §7.1 model prerequisite →
  Task 13; §7 example workflow → Task 14; §9 tests → Tasks 2–7 (unit) + 12/15
  (smoke); §8.2 pyproject → Task 1; README → Task 16. All covered.
- **Caching:** spec §5 says no `fingerprint_inputs`/`not_idempotent` — the nodes
  define neither, so default value-based caching applies. Correct, no task needed.
- **Type consistency:** `snap_frames` returns `(frame_count:int, runtime_actual:float)`
  used identically in Task 8; `parse_mode_label`→key→`build_camera_block` chain
  consistent; node `node_id`s match the curl checks in Task 12 and the spec.
