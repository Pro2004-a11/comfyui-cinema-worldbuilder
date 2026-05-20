# LinkedIn post draft — Cinema Worldbuilder / LTX 2.3 findings

Attach: `sweep/fp8_compare/q2k_vs_fp8_full_reel.mp4` (1:47, 45 MB) — the Q2_K vs FP8 A/B reel.

Hashtags: `#LTXVideo #ComfyUI #AIVideo #GenerativeVideo #TechnicalArtist #FilmTech`
Optionally tag: `@Lightricks` (raises visibility, slightly more opportunistic — your call)

---

## Draft (the one to post)

Three things I learned about Lightricks' **LTX 2.3** model after a weekend of controlled A/B testing 👇

*(Spoiler: half of what we filmmakers obsess over in our prompts is invisible to the model.)*

The setup: I built a small ComfyUI node pack — **`comfyui-cinema-worldbuilder`** — three nodes that compose disciplined cinematic prompts (camera mode, lens, diegetic-audio guardrails). Used it as instrumentation to vary ONE variable at a time across 26 paired clips at fixed seed, sampler, and sigmas.

The pack isn't the point. What it surfaced is.

---

**1️⃣ All that camera jargon? Decorative.**

*"Shot on Arri Alexa, Master Prime lenses, ND 1.2 filter, anamorphic squeeze..."* — the model reads none of it.

I cut my camera blocks in half (180 → 94 words). Output looked the same. CLIP similarity ~0.97 on the paired frames — effectively identical clips.

**What actually conditions LTX 2.3:** motion verb + lighting word + focal length + palette name. The rest is filmmaker LARP. Save the tokens.

---

**2️⃣ Camera grammar = lighting grade, NOT scene content.**

I tried prompting only the camera — *"slow dolly in, golden hour, 50mm, shallow DoF, warm amber and teal"* — and got back beautifully-graded lens-mush. No subject. No story.

The camera vocabulary acts like a color grade in post: polish on top, no foundation underneath. The scene noun does ALL the heavy lifting.

**Translation for filmmakers:** write the *shot*, not just the *shot list*. Name what's IN frame, not only how it's shot.

---

**3️⃣ The "soft grainy output" bug isn't your prompt — it's the scheduler.**

If your LTX 2.3 distilled output looks fuzzy and unfinished, it's not your fault. The default `LTXVScheduler` settings most community workflows ship with leave the schedule undenoised on the distilled weights.

Swap it for explicit `ManualSigmas` using Lightricks' reference values — different scheduler, fully clean output.

Easy mistake to inherit. Worth a doc warning, IMO.

---

**🎁 Bonus: the model itself got better mid-study.**

Switched from the Q2_K GGUF base to the dev-fp8 + distill LoRA chain (matching the Lightricks **Comfy-Org canonical template** that landed mid-week). Same Cinema Worldbuilder prompts. Visibly sharper output, cleaner motion, better skin in close-ups.

A/B reel attached — same prompts, two LTX 2.3 model variants. Q2_K on the left, fp8+LoRA on the right.

---

Code, sweep matrix, side-by-side reels, CLIP-similarity numbers, full writeup — all in the repo. **Methodology over product** — the nodes were the instrumentation; the findings are the actual deliverable.

If anyone from the Lightricks team is reading: love this model. Those three notes above would land cleanly in the docs. 🙏

🔗 **github.com/Pro2004-a11/comfyui-cinema-worldbuilder**

#LTXVideo #ComfyUI #AIVideo #GenerativeVideo #TechnicalArtist #FilmTech

---

## Word count: ~420 (in target — punchy, scannable)

## Alt opening hooks

If the current opener doesn't grab, swap in:

1. **Spoiler-first:** "Half of what we filmmakers put in our AI video prompts is invisible to the model. Spent a weekend proving it. Three findings 👇"
2. **Number-first:** "Cut my prompts in half. Output stayed identical. Three things about LTX 2.3 I didn't expect 👇"
3. **Contrarian:** "Stop putting Arri Alexa, Master Primes, and ND 1.2 in your LTX prompts. They do nothing. Here's what I tested 👇"
4. **Story-first:** "Built a ComfyUI node pack to write better video prompts. Ended up learning three things about the LTX 2.3 model itself 👇"

## Attachment recommendations

- **Primary:** `q2k_vs_fp8_full_reel.mp4` (release asset, github.com/Pro2004-a11/comfyui-cinema-worldbuilder/releases/tag/v0.2.0) — the A/B reel. Pulls double-duty: shows the pack's range AND demonstrates the model upgrade beat.
- **Alternative:** trim the mp4 to a ~30-sec highlight before upload if LinkedIn's autoplay-without-sound bothers you — short reels get more loop-time on feed.

## What to tweak before posting

- [ ] Pick the opener — current vs one of the four alts
- [ ] Decide whether to `@`-tag `@Lightricks` (raises visibility but reads slightly opportunistic — your call)
- [ ] Confirm the attached reel — full 1:47 or trimmed highlight
- [ ] LinkedIn caps post text at ~3000 chars. Current draft is well under (~2400). You have headroom to add 1-2 sentences if something feels missing.

## What changed from v1 of this draft

- Sigma values, σ-numbers, "distilled-1.1" naming, base_shift / terminal terms — all out
- Each finding now opens with a punchy one-liner before the explanation
- Added "filmmaker LARP" and "write the shot, not the shot list" — quotable lines
- Emoji-anchored numbered findings for scannability
- Closing tightened, "methodology over product" line preserved
- Length dropped from ~520 → ~420 words
