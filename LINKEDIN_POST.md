# LinkedIn post draft — Cinema Worldbuilder / LTX 2.3 findings

Attach: `sweep/fp8_compare/q2k_vs_fp8_full_reel.mp4` (or the Q2_K-only showcase if you want to lead with the pack's range, not the model upgrade).

Hashtags: `#LTXVideo #ComfyUI #AIVideo #DiffusionModels #TechnicalArtist #GenerativeVideo`
Tag Lightricks if you want them to see it: `@Lightricks`

---

## Draft

Spent a weekend running a controlled A/B sweep on **LTX 2.3** to understand how it actually responds to prompt content. Three findings I didn't expect — sharing because they'd have saved me a lot of time up front.

I built a small ComfyUI node pack — `comfyui-cinema-worldbuilder` — to use as the instrument. Three nodes (CameraBlock, AudioLine, PromptComposer) that compose a disciplined cinematic prompt from five fixed inputs. The pack isn't the point; it's what let me hold one prompt skeleton constant and vary one variable per cell across a 26-pair sweep at fixed model, seed, sampler, and sigma schedule.

**Finding 1 — Equipment vocabulary is decorative.**
Compressing the camera/lens block by **48% (180 → 94 words)** produces visually indistinguishable output. CLIP image-embedding cosine similarity across the 26 paired clips: **0.967 ± 0.071 paired** vs **0.699 ± 0.076 control** (random non-matching pairs). About a 3.5σ effect size. Arri, Master Primes, ND filter indices, anamorphic squeeze — LTX 2.3 doesn't read it. Motion verb, lighting word, focal length, palette name — that's what conditions the model. The rest is decorative.

**Finding 2 — `static_description` is load-bearing; camera grammar is a grade layer.**
The camera-vocabulary phrasing applies a palette, a motion vocabulary, and a stage lighting cue — but it does **not** carry scene content. Strip the static scene noun and even rich camera prompts collapse to abstract lens-mush. Camera grammar earns its place as a finishing grade, not a foundation. Don't ship "all camera, no scene."

**Finding 3 — `LTXVScheduler` defaults leave the distilled-1.1 schedule undenoised.**
The common community-default `LTXVScheduler(steps=8, max_shift=2.05, base_shift=0.95, stretch=true, terminal=0.0)` produces soft, slightly grainy output that looks like an unfinished refine pass. The clean fix is a `ManualSigmas` schedule from Lightricks' official 1.1 reference: `1., 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`. Different scheduler, fully denoised output. The Kijai and Lightricks reference workflows ship this directly — but `LTXVScheduler` is the more discoverable entry point, and soft output is a confusing first impression for new users.

**Bonus — the model also got better mid-study.**
Started on the LTX 2.3 22B Q2_K GGUF (quick, fits in 12 GB). Mid-week, ported to the **dev-fp8 + distill LoRA** chain on the matching Comfy-Org canonical template — visible quality jump on the same prompts. The Q2_K → fp8 A/B reel attached. Same model family, same prompts, two quant chains. Look at it.

The code, the sweep matrix, the side-by-side reels, the per-clip CLIP-similarity numbers, and the writeup are all in the repo. Methodology over product — the nodes were instrumentation; the findings are the actual deliverable.

If anyone from the Lightricks team is reading: love this model. The three doc notes above would help new users land cleanly.

🔗 Repo: github.com/Pro2004-a11/comfyui-cinema-worldbuilder
📄 Full writeup: `FINDINGS_FOR_LTX.md` in the repo

#LTXVideo #ComfyUI #AIVideo #DiffusionModels #TechnicalArtist #GenerativeVideo

---

## Word count: ~520 (in target)

## Alt opening hooks

If the current opener doesn't grab, try one of these:

1. **Finding-first:** "LTX 2.3 ignores equipment vocabulary in your prompts. Spent a weekend proving it with a 26-pair A/B sweep — three findings inside."
2. **Number-first:** "−48% prompt length, indistinguishable output. CLIP-similarity 0.97 across 26 paired clips. Here's what I learned controlled-testing LTX 2.3 this week."
3. **Contrarian:** "Stop tuning T-stops and ND filters in your LTX prompts. It does nothing. Three things I empirically verified about LTX 2.3 this week."
4. **Build-story:** "Built three ComfyUI nodes for cinematic prompts. Used them as instrumentation. Found three things about LTX 2.3 the docs don't say."

## Attachment recommendations

- **Primary attachment:** `sweep/fp8_compare/q2k_vs_fp8_full_reel.mp4` (1:47, 45 MB) — the Q2_K vs fp8 A/B reel. Best for the "model got better" beat and pulls double-duty as a quality showcase.
- **Alternative:** `sweep/showcase/cinema_showcase_reel.mp4` (~27s) — pure per-mode showcase, smaller file, lets the post focus on findings rather than the model upgrade.
- Could also do two posts: one for findings + showcase reel, follow-up the next week with the model-upgrade A/B reel.

## What to tweak before posting

- [ ] Replace `Pro2004-a11` with the actual GitHub handle / org
- [ ] Decide whether to `@`-tag `@Lightricks` (raises visibility but can read as opportunistic — your call)
- [ ] Add a 1-2 line bio at the bottom if LinkedIn doesn't auto-pull it
- [ ] Pick the opener — current vs one of the four alts
- [ ] Confirm attachment choice
