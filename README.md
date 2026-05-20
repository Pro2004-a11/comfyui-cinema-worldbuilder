# cinema-worldbuilder — prompt-sensitivity study of LTX 2.3

This repository is the code, data, and writeup for a small empirical study of
how **LTX 2.3 22B distilled 1.1** responds to prompt content variations and a
default sampling configuration.

The main artifact is the writeup:

> **[`FINDINGS_FOR_LTX.md`](./FINDINGS_FOR_LTX.md)** — three findings about
> LTX 2.3 prompt sensitivity, with side-by-side A/B evidence.

Three findings in one line each:

1. **Equipment vocabulary is decorative** — −48% prompt length, indistinguishable output across 26 pairs.
2. **`static_description` is load-bearing** — camera grammar is a grade layer, not a content carrier.
3. **`LTXVScheduler` defaults leave the distilled-1.1 schedule undenoised** — `ManualSigmas` is the clean fix.

The ComfyUI node pack in this repo is the methodology — three V3 nodes that
let the same prompt skeleton render with one variable changing per cell.
It is checked in as the reproducibility appendix, not as a product on its own.

## What's here

```
comfyui-cinema-worldbuilder/
├── FINDINGS_FOR_LTX.md          # the writeup — start here
├── cinema_grammar.py            # mode tables, camera-block builders, prompt composer (pure functions)
├── nodes.py                     # 3 io.ComfyNode adapters around cinema_grammar.py
├── tests/                       # 20 unit tests for cinema_grammar
├── example_workflows/           # the LTX 2.3 graphs used by the sweeps
│   ├── cinema_ltx23_t2v.json    # text-to-video — the primary sweep workflow
│   ├── cinema_ltx23_i2v.json    # image-to-video (post-rebuild)
│   ├── cinema_ltx23_v2v.json    # video-to-video refine
│   └── cinema_ltx23_t2v_hires.json   # two-stage 540p->1080p (engineering artifact, not part of the study)
└── sweep/
    ├── cinema_sweep.py          # v1 jargon-grammar sweep (28-job matrix)
    ├── cinema_sweep_v2.py       # v2 short-grammar sweep (28-job matrix)
    ├── ab_compare.py            # builds side-by-side A/B mp4s + a single concat reel
    ├── results/ANALYSIS.md      # v1 sweep analysis (load-bearing static_description finding)
    └── results_v2/ANALYSIS_v2.md # v2 sweep analysis (jargon-is-decorative finding)
```

The A/B evidence reel — 26 paired clips, v1 jargon-grammar on the left,
v2 short-grammar on the right — is regenerable but not checked into git
(large mp4s):

```
python sweep/ab_compare.py
# -> sweep/results_ab/_reel_all.mp4    1:45, 26 pairs
```

## Reproduce

The sweep matrix is reproducible end-to-end from the checked-in scripts.
Requirements: a local ComfyUI on `localhost:8188` with the LTX 2.3 stack
installed (see `FINDINGS_FOR_LTX.md` → **Setup**). No third-party Python
dependencies beyond ComfyUI itself.

```bash
# unit tests on the prompt composer
python -m pytest tests/ -v

# validate the 28-job matrix without rendering
python sweep/cinema_sweep_v2.py --check

# full sweep (~30 min on RTX 4070 Ti)
python sweep/cinema_sweep_v2.py

# build the side-by-side A/B reel
python sweep/ab_compare.py
```

The nodes register as **Cinema Worldbuilder** in ComfyUI under
`category: Cinema Worldbuilder`. They are intentionally thin — most logic
lives in the pure-function `cinema_grammar.py` so the methodology is
testable without a ComfyUI runtime.

## The nodes (used as sweep instrumentation)

| Node | Purpose in the study |
|---|---|
| `CinemaWorldbuilder_CameraBlock` | Generates the camera-vocabulary text block at fixed (mode, lens) settings. Lets us swap v1 jargon for v2 intent-only with one input change. |
| `CinemaWorldbuilder_AudioLine` | Diegetic audio line builder with a music-token guardrail. Caught one bad scene in the sweep matrix (`market`/"distant music box") — kept in place. |
| `CinemaWorldbuilder_PromptComposer` | Assembles `style + dynamic + static + camera_block + audio_line` into a single positive prompt. The point of separation: each input is one independent variable for the sweep. |

The nodes are **not** a recommended workflow on top of LTX 2.3. They exist so
the experiments are reproducible and the prompt skeleton is held constant
across sweep cells.

## Limitations of this study

See `FINDINGS_FOR_LTX.md` → **Out of scope**. Briefly: no quantitative perceptual
metrics, single distilled-1.1 Q2_K configuration, visual-inspection-grade
evidence only.

## License & contact

[License TBD]. Yosi Refaeli — feedback, corrections, replications all welcome.
