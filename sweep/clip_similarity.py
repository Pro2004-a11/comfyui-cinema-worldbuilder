#!/usr/bin/env python3
"""CLIP image-embedding similarity between v1 jargon-grammar and v2 short-grammar
sweep clips. One number per pair: cosine similarity of mid-frame CLIP embeddings.

Reports mean/std/min/max across the 26 paired clips, plus a control distribution
(cross-pair similarity from randomly shuffled v2 cells) to bound the random floor.

Run with the ComfyUI portable Python so torch+transformers are available:
  D:/ComfyUI_windows_portable/python_embeded/python.exe sweep/clip_similarity.py
"""
import os, json, subprocess, tempfile, statistics, random
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

PACK   = r"D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder"
V1_DIR = os.path.join(PACK, "sweep", "results")
V2_DIR = os.path.join(PACK, "sweep", "results_v2")
OUT    = os.path.join(PACK, "sweep", "results_v2", "clip_similarity.json")
MODEL_ID = "openai/clip-vit-base-patch32"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def extract_midframe(mp4, png):
    """Pull a single frame near the temporal middle of the clip (frame 48 of 97)."""
    subprocess.run(["ffmpeg", "-y", "-i", mp4,
                    "-vf", "select=eq(n\\,48)", "-vframes", "1", png],
                   check=True, capture_output=True)

@torch.no_grad()
def embed(model, proc, img):
    """Image embedding via vision_model.pooler_output + visual_projection.
    Robust across transformers 4.x and 5.x API changes."""
    inputs = proc(images=img, return_tensors="pt").to(DEVICE)
    pooled = model.vision_model(pixel_values=inputs["pixel_values"]).pooler_output
    emb = model.visual_projection(pooled)
    return emb / emb.norm(dim=-1, keepdim=True)

def main():
    v1s = {f for f in os.listdir(V1_DIR) if f.endswith(".mp4")}
    v2s = {f for f in os.listdir(V2_DIR) if f.endswith(".mp4")}
    pairs = sorted(v1s & v2s)
    print(f"[clip] {len(pairs)} paired clips")

    print(f"[clip] loading {MODEL_ID} on {DEVICE}...")
    model = CLIPModel.from_pretrained(MODEL_ID).to(DEVICE)
    model.requires_grad_(False)
    proc  = CLIPProcessor.from_pretrained(MODEL_ID)

    v1_emb, v2_emb = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        for fn in pairs:
            for tag, src_dir, store in (("v1", V1_DIR, v1_emb), ("v2", V2_DIR, v2_emb)):
                png = os.path.join(tmp, f"{tag}_{fn}.png")
                extract_midframe(os.path.join(src_dir, fn), png)
                img = Image.open(png).convert("RGB")
                store[fn] = embed(model, proc, img).cpu()
            print(f"  encoded {fn}")

    # paired similarity: same-scene v1 vs v2 (the headline)
    paired = [(fn, float((v1_emb[fn] * v2_emb[fn]).sum())) for fn in pairs]

    # control: v1 of scene K vs v2 of a different randomly chosen scene
    rng = random.Random(42)
    keys = list(pairs)
    control = []
    for k in keys:
        peer = rng.choice([p for p in keys if p != k])
        control.append((k, peer, float((v1_emb[k] * v2_emb[peer]).sum())))

    def stat(xs):
        return dict(mean=statistics.mean(xs), std=statistics.stdev(xs),
                    minv=min(xs), maxv=max(xs), n=len(xs))
    paired_vals  = [s for _, s in paired]
    control_vals = [s for _, _, s in control]
    paired_stat  = stat(paired_vals)
    control_stat = stat(control_vals)

    report = dict(
        model=MODEL_ID,
        n_pairs=len(pairs),
        paired   = dict(stats=paired_stat, items=[{"id": k, "sim": s} for k, s in paired]),
        control  = dict(stats=control_stat, items=[{"id": k, "peer": p, "sim": s} for k, p, s in control]),
        interpretation=(
            "paired = same-scene v1-jargon vs v2-intent (the comparison we care about). "
            "control = same v1 frame paired with v2 frame from a randomly chosen different scene. "
            "Higher paired mean and lower control mean = v1/v2 are visually closer to each other "
            "than they are to random other scenes, supporting the claim that the grammar change is "
            "below the model's prompt-sensitivity threshold."
        ),
    )
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print(f"  paired   mean={paired_stat['mean']:.4f}  std={paired_stat['std']:.4f}"
          f"  min={paired_stat['minv']:.4f}  max={paired_stat['maxv']:.4f}  n={paired_stat['n']}")
    print(f"  control  mean={control_stat['mean']:.4f}  std={control_stat['std']:.4f}"
          f"  min={control_stat['minv']:.4f}  max={control_stat['maxv']:.4f}  n={control_stat['n']}")
    print()
    print(f"[clip] wrote {OUT}")

if __name__ == "__main__":
    main()
