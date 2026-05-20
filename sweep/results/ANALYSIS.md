# Cinema Worldbuilder t2v — overnight sweep analysis (2026-05-19)

28 jobs, **26 rendered** in ~28 min, 2 failed (matrix bug, not render). Every mp4 has
its params burned top-left. `index.html` plays all clips grouped by block.

## Headline

**The sampling fix holds at scale.** All 26 clips are properly denoised — no soft/grainy
residual-noise haze anywhere. The `ManualSigmas` rebuild is solid across every mode and
scene. v1 quality is confirmed.

## Block A — mode coverage: PASS (one weak mode)

The five modes produce **visibly distinct registers** — the camera grammar reaches the
pixels:
- **M1 Narrative** — dark, low-key corridor, figure receding. Moody. ✓
- **M2 Studio** — bright high-key editorial portrait, photoreal skin. ✓ (strongest)
- **M3 Action** — two figures, real motion blur, dust, grit. ✓
- **M4 Performance** — **weak**: an abstract red haze over a crowd; no clear performer/subject.
- **M5 Atmospheric** — clean empty colonnade, holds geometry, no people. ✓

**Fix for M4:** the scene's `static_description` lacked a concrete subject — "pit-photographer
/ crowd / haze" grammar alone collapses to an abstract field. Any mode needs a real subject
noun in `static_description`.

## Block B — grammar A/B: the key finding

The camera-block grammar is a **grade/mood layer, not a content carrier.**
- **FULL** (grammar + camera block + audio) → moodier, lower-key, graded — the cinematic look.
- **PROSE** (scene text only) → more literal, brighter, cleaner composition.
- **CAMERA** (camera block + action verb, no `static_description`) → **broke on the alley**
  (abstract lens-mush) because there were no scene nouns; held on the bridge only because
  "steel truss bridge" was in the action line.

Conclusion: **`static_description` is load-bearing.** The camera grammar earns its place —
it applies a consistent cinematic grade — but it cannot carry a shot alone. FULL stays the
right default; never let `static_description` be empty.

## Block C — scene robustness

- **Hard geometry** (steel bridge) → crisp, perfect. ✓
- **Soft-organic** (serum swirl) → rendered a coherent organic macro texture; **did NOT
  collapse to cobweb.** The cobweb failure in the warp-bridge POC was a *v2v-refine*
  artifact — t2v-from-noise handles organic content fine.
- **Crowd** (market) → not tested; both jobs failed to submit (see below).

## Bugs / issues

1. **2 `market` jobs failed** — the sweep matrix put *"distant music box"* in the audio;
   `CinemaAudioLine`'s guardrail correctly rejected the token "music." Not a render bug —
   the music-ban fired in a real run, which is a positive validation. Fix: rename the
   audio, re-run the 2 clips.
2. **M4 abstract-haze** — see Block A fix above.

## How to improve — recommendations

1. **Subject discipline.** Empty/vague `static_description` → abstract haze (M4, alley
   CAMERA). Consider a `[WARN]` from `CinemaPromptComposer` when `static_description` is
   blank — the grammar is a finish, not a foundation.
2. **Resolution.** All clips were 768×512 — crisp but detail-limited. Worth a VRAM test at
   the official template base 960×544; bridge/portrait would gain sharpness.
3. **Second pass.** The official template's upscale-refine pass (needs a spatial-upscaler
   model, not installed) remains the top quality lever if more fidelity is wanted.
4. **FULL is the right default** — the camera grammar measurably applies a cinematic grade;
   it just must always sit on real scene content.
