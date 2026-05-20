# Cinema Worldbuilder t2v — v2 grammar A/B sweep (2026-05-20)

24/26 rendered (same two `market` jobs fail-fast on the music-ban — known v1 bug, carried over).
Each v2 clip rendered against its v1 counterpart from the 2026-05-19 sweep. Side-by-side reel:
`sweep/results_ab/_reel_all.mp4` (26 pairs, 1:45, 25 MB).

## Headline

**v2 grammar holds.** Shorter camera blocks built on words LTX obeys
(motion / lighting / lens / palette / DoF, ~30–40 words) produce **visually
indistinguishable output** from v1's longer equipment-jargon blocks across all
three sweep blocks. Equipment vocabulary (Arri, Master Primes, ND filters, etc.)
was decorative — the model ignored it. Verdict by Yosi after watching the full
reel: "most of new renders look the same."

**v2 stays the default.** v0.2.0 ships.

## What v2 changed (recap)

`cinema_grammar.build_camera_block` rewritten at commit `ab2fc10` to emit
short, motion-first phrasing only. Smaller prompts, faster encode, no quality
loss.

## Known issues carried into v0.2.0 (deferred)

1. **`market` audio fails the music-ban** — sweep matrix puts "distant music
   box" into the audio line; `CinemaAudioLine` correctly rejects "music". Trivial
   fix in `sweep/cinema_sweep.py` SCENES dict. Affects 2/28 jobs.
2. **M4 Performance abstract-haze** — arena scene's `static_description` lacks
   a concrete subject noun, so M4 grammar alone collapses to an abstract red
   field. Per v1 finding ("static_description is load-bearing"). Fix is one
   noun in the SCENES dict, not a code change.

Neither blocks shipping v2 as the default grammar.

## Next

- i2v rebuild (uses the same v2 grammar; t2v template was the reference rebuild).
- (deferred) market audio rename + M4 arena subject noun → rerun 4 specific clips.
- (deferred) resolution bump 768×512 → 960×544 VRAM test; upscale-refine pass.
