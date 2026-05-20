# Four things I noticed about LTX 2.3 while building a prompt pack

*Yosi Refaeli — 2026-05-20*

Posted as an FYI, not as a request. The Lightricks team owns the model; I am
an independent practitioner who spent a weekend building a small ComfyUI prompt
pack and ran a controlled side-by-side sweep along the way. Four observations
were robust enough across my data that they felt worth writing down — three
empirical (with paired side-by-sides and a CLIP-similarity metric), one
craft-observational about the visual "look" of different quantizations of
the same model. None of this is a critique of the model — LTX 2.3 distilled
1.1 is genuinely good — and none of it is a sales pitch for the prompt pack,
which is checked in as methodology, not as a product.

All numbers below are reproducible from the repo. Caveats and scope at the
bottom; please read those before generalizing.

---

## Setup

| | |
|---|---|
| Model checkpoint | `ltx-2.3-22b-distilled-1.1-Q2_K.gguf` (Kijai/LTX2.3_comfy) |
| CLIP encoder for the model | `gemma-3-12b-it-IQ4_XS.gguf` + `ltx23_embeddings_connector.safetensors` |
| Video VAE / Audio VAE | `ltx23_video_vae.safetensors` / `ltx23_audio_vae.safetensors` |
| Runtime | ComfyUI 0.16.4, Windows 11, RTX 4070 Ti 12 GB |
| Output per clip | 768×512, 24 fps, 97 latent frames (≈ 4 s) |
| Sampler | `SamplerCustomAdvanced` + `RandomNoise` + `CFGGuider` (cfg 1.0) + `euler_ancestral` |
| Sigmas | `ManualSigmas` `"1., 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"` |
| Seeds used per cell | 42 and 7 (both shown in the A/B reel) |

Every comparison below holds all of the above constant. The only thing that
changes between paired cells is the specific prompt-content variable named in
that finding. Code: `sweep/cinema_sweep.py` (v1) → `sweep/results/`,
`sweep/cinema_sweep_v2.py` (v2) → `sweep/results_v2/`, A/B compositor
`sweep/ab_compare.py` → `sweep/results_ab/_reel_all.mp4` (26 paired clips, 1:45).

---

## Observation 1 — equipment vocabulary appears decorative

### What I tested

Two camera-block templates for the same scene, differing only in vocabulary
density and length:

- **v1 (jargon-heavy):** camera body, lens series, T-stop, ND filter index,
  anamorphic squeeze, film-grain emulation, dolly speed, rack-focus moments,
  rolling-shutter compensation. 180 words / 1160 chars.
- **v2 (intent only):** motion verb, lighting palette word, focal length
  number, depth-of-field cue. 94 words / 621 chars.

Same scene `static_description`, `dynamic_description`, audio, seed, sampler,
sigmas. Repeated across two more scenes (`bridge`, `serum`), five modes
(M1–M5), and three structural variants (FULL / PROSE / CAMERA) — **26 paired
clips total**.

### What I saw

26/26 pairs read visually indistinguishable to me — same motion, same denoise
state, same palette, same framing. To put a number on "indistinguishable" I
also ran CLIP image-embedding cosine similarity on the midframe of each pair,
using `openai/clip-vit-base-patch32`:

| | mean | std | min | max | n |
|---|---:|---:|---:|---:|---:|
| paired (v1 ↔ v2, same scene) | **0.967** | 0.071 | 0.689 | 1.000 | 26 |
| control (v1 vs v2 of different scene) | **0.699** | 0.076 | 0.600 | 0.910 | 26 |

The paired distribution sits ≈ 3.5 σ of the control distribution above the
control mean. The single pair that scored 0.689 (the "alley CAMERA-only"
variant, where I had stripped the static description — see Observation 2) is
where the v2 grammar happens to land on a different abstract pattern than v1.
For all other pairs the score is ≥ 0.93.

CLIP-similarity is a noisy single-frame metric — it does not say two clips are
"the same video." It says their visual content at the sampled frame is much
closer to each other than to randomly chosen other clips in the same sweep.
Combined with the 26-pair captioned reel (which is the actual evidence), it's
the strongest reading of "the v1↔v2 grammar change is below LTX 2.3's
prompt-sensitivity threshold for this configuration."

### Where the claim ends

This was tested on `ltx-2.3-22b-distilled-1.1-Q2_K.gguf` at 768×512, 24 fps, 97
frames, with the specific sigma schedule above and Gemma-3-12B CLIP
encoder. I have no data on whether the same holds for the full bf16 weights,
the fp8_scaled or mxfp8 quantizations, longer clips, higher resolutions, or
different sigma schedules. I'd guess most of the finding survives quantization
swaps — the prompt-encoding side is unchanged — but I haven't run it.

### Possible action if useful

If the equipment-vocabulary insensitivity holds on the full-precision weights,
a short note in the LTX 2.3 prompting guide would help users coming from a
filmmaking background skip the time they otherwise spend tuning T-stops and
ND grades the model doesn't read. Not necessary if it's already in the docs
and I missed it.

---

## Observation 2 — `static_description` is load-bearing; camera vocabulary acts as a grade layer

### What I tested

For two scenes (`alley`, `bridge`) I ran three prompt structures at fixed seed
and sampler:

- **FULL:** `style + dynamic_description + static_description + camera_block + audio_line`
- **PROSE:** `style + dynamic_description + static_description` only (no camera block)
- **CAMERA:** `dynamic_description + camera_block` only (no `static_description`, no audio)

I also separately observed in the mode-coverage block that M4 Performance,
applied to an arena scene whose `static_description` lacked a concrete subject
noun, rendered an abstract red haze. The same M4 grammar applied to scenes
with a concrete subject noun rendered correctly.

### What I saw

- FULL: clean cinematic register on both scenes.
- PROSE: clean, slightly brighter, scene content intact on both.
- CAMERA: **broke on `alley`** — collapsed to a lens-mush pattern with no
  recognizable scene. **Held on `bridge`** because the `dynamic_description`
  line literally contained "steel truss bridge", which incidentally restored a
  scene anchor.

### Reading

The camera-vocabulary phrasing in LTX 2.3 prompts behaves as a grade and mood
modifier — it consistently applies a palette, a motion vocabulary, and a stage
lighting cue — but it does not carry scene content. When the scene noun phrase
is missing, the model has nothing to anchor and degrades quietly rather than
loudly.

### Where the claim ends

Same scope as Observation 1: this is on the distilled 1.1 Q2_K config above,
two scenes, one sigma schedule. The CAMERA-only collapse mode is the kind of
edge that some users will hit and others never will, depending on how they
structure their prompts.

### Possible action if useful

A short docs note that the scene/static description carries the content and
the cinematography vocabulary is a grade layer would help users avoid the
"all camera, no scene" failure mode silently. In tooling, a soft warning when
the static description is empty would catch this at compose time.

---

## Observation 3 — the default `LTXVScheduler` settings appear to leave the distilled-1.1 schedule undenoised

### What I tested

I started with a fairly common community-workflow pattern:

```
LTXVScheduler(steps=8, max_shift=2.05, base_shift=0.95, stretch=true, terminal=0.0)
```

with the LTX 2.3 22B distilled 1.1 Q2_K weights. The output visibly carried
residual noise — soft, slightly grainy, the way an unfinished refine pass
looks. Bumping `terminal` from `0.0` to `0.1` partially recovered. The clean
fix that produced consistently denoised output was to swap the scheduler for
an explicit `ManualSigmas` schedule taken from a Lightricks 1.1 reference
workflow:

```
"1., 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"
```

with `SamplerCustomAdvanced` driving it. The 26-pair v2 sweep above used this
schedule throughout — none of the clips show the residual-noise haze.

### Reading

I can't tell from the outside whether this is a `LTXVScheduler` bug, a
distilled-vs-base weight mismatch, or my own misconfiguration — the failure
mode is consistent though, and it happens with what looks like the
default-shaped settings. The pre-rebuild commit in this repo
(`5278115` → fix `e6fb8e9` → rebuild `58ffe65`) captures the before/after if
anyone wants to reproduce. The Lightricks reference workflows I've seen ship
`ManualSigmas` directly for distilled-1.1, so this is probably known
internally; the friction is that the community workflows people copy from
do not.

### Where the claim ends

I only tested this on the Q2_K quantization. I haven't verified whether
`LTXVScheduler` is also misbehaving on the other distilled-1.1 quants or on
the base bf16 weights.

### Possible action if useful

If `LTXVScheduler` is not safe with the distilled-1.1 weights under common
default settings, a doc warning on the scheduler node's tooltip and/or the
model card would prevent users who don't already have a known-good template
on hand from getting soft residual-noise output as a first impression.

---

## Observation 4 (craft note) — different quantizations of the same model produce visibly different "looks"

### What I tested

Mid-study I ported the workflow from the **Q2_K GGUF base** (`ltx-2.3-22b-distilled-1.1-Q2_K.gguf` loaded via `UnetLoaderGGUF`) to the **dev-fp8 + distill LoRA chain** (`ltx-2.3-22b-dev-fp8.safetensors` via `CheckpointLoaderSimple` + `LoraLoaderModelOnly` @ strength 0.5) matching the Comfy-Org canonical template. Same Cinema Worldbuilder prompts, same scenes, same prompt content. Two scenes × five camera modes = 10 paired clips.

### What I saw

The two chains don't differ only in technical fidelity — they have **distinct visual personalities**:

- **FP8 + distill LoRA chain**: sharper edges, higher contrast, more saturated and assertive color grade. Highlights bloom harder. Feels like footage from a modern digital cinema camera that has already been color-graded.
- **Q2_K GGUF base**: softer highlight rolloff, less saturated overall, slightly milky. Feels closer to a flatter / less-graded "old film" or documentary capture style.

This isn't a "fp8 is better" or "Q2_K is better" finding — it's a craft observation. The right pick depends on the project:

| Project type | Likely better fit |
|---|---|
| Advertising, music video, fashion, hero shots | FP8 + distill LoRA |
| Documentary, drama, vérité, naturalistic narrative | Q2_K GGUF |

### Reading

I'm not certain whether the look difference originates in the quantization scheme itself (fp8 vs Q2_K precision affecting color/contrast retention), the distill-LoRA application (Lightricks may have tuned it for a particular aesthetic target), or a combination. The two chains *are* different topologies, not just different precisions, so the cause isn't isolated. The observation stands either way: when picking a chain, consider the look you're after, not only the spec sheet.

### Where the claim ends

Two chains × ten paired clips × two scenes — eyeballing only, no perceptual metric run on the contrast/saturation difference. The "old film" / "modern cinema" language is subjective categorization. Different scenes might shift the rank.

### Possible action if useful

Worth a doc note that the LoRA-on-dev path and the GGUF-distilled path are *not* drop-in equivalents from a creative-direction standpoint. Users picking a base for a specific project should preview both before committing the render budget.

---

## Smaller things I tripped on along the way

These are not study findings — they are integration notes from my afternoon,
mentioned only because two of them looked like ComfyUI core / ecosystem issues
rather than user error:

- **`mxfp8_block32`** quantization (the format used by the Lightricks 1.1
  reference workflow's transformer file) is not registered in ComfyUI 0.16.4's
  `comfy/quant_ops.py:QUANT_ALGOS` and fails with `KeyError: 'mxfp8'` at
  weight load. Registered formats in this build: `float8_e4m3fn`,
  `float8_e5m2`, `nvfp4`. Possibly already fixed in a newer ComfyUI; I didn't
  upgrade.
- **`LatentUpscaleModelLoader`** uses the V3 schema API, where
  `define_schema()`'s options list is captured at first call. A file dropped
  into `models/latent_upscale_models/` after server start does not appear in
  the dropdown without a server restart.
- **`LTXVAudioVAELoader`** on my install read from `models/checkpoints/`
  rather than `models/vae/`. `VAELoaderKJ` (`models/vae/`) accepted both the
  video and audio LTX 2.3 VAEs and was the working substitute.

---

## How to reproduce

```
git clone <this repo> ComfyUI/custom_nodes/comfyui-cinema-worldbuilder
python -m pytest tests/                              # 20 unit tests for the prompt composer
python sweep/cinema_sweep_v2.py --check              # validates the 28-job matrix without rendering
python sweep/cinema_sweep_v2.py                      # full sweep (~30 min on RTX 4070 Ti)
python sweep/ab_compare.py                           # builds the 26-pair side-by-side reel
python sweep/clip_similarity.py                      # CLIP-cosine on the 26 pairs (~1 min on GPU)
```

You'll need the LTX 2.3 stack listed in **Setup** above and a local ComfyUI on
`localhost:8188`. Running the sweep regenerates the captioned mp4s under
`sweep/results/` and `sweep/results_v2/`. The CLIP-similarity script
(`sweep/clip_similarity.py`) writes its full per-clip table to
`sweep/results_v2/clip_similarity.json`.

## What this writeup is not

- **Not a benchmark.** No FVD, no LPIPS, no human-rater study. CLIP-cosine on a
  midframe is a sanity check, not a perceptual quality measure.
- **Not a product pitch.** The ComfyUI nodes in this repo are sweep
  instrumentation; they let me hold one prompt skeleton constant and vary one
  variable per cell. They are not a recommended workflow on top of LTX 2.3
  and there is no claim that they produce better video than disciplined
  prose.
- **Not a generalization beyond what I tested.** Each observation is scoped
  to the exact configuration in the **Where the claim ends** subsection.

Corrections, replications on other LTX 2.3 configurations, or "actually
this is in the docs at <url>" are all welcome.
