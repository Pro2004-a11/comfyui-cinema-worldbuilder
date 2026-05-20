#!/usr/bin/env python3
"""Composite v1 vs v2 sweep mp4s side-by-side (hstack) for every matching ID.

Reads from results/ (v1) and results_v2/ (v2), writes pairs to results_ab/<id>.mp4
with V1 / V2 labels burned on. Re-runnable: skips pairs whose output is fresh.
"""
import os, sys, subprocess, datetime, io

PACK    = r"D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder"
V1_DIR  = os.path.join(PACK, "sweep", "results")
V2_DIR  = os.path.join(PACK, "sweep", "results_v2")
AB_DIR  = os.path.join(PACK, "sweep", "results_ab")
FONT    = "C:/Windows/Fonts/consolab.ttf"
os.makedirs(AB_DIR, exist_ok=True)

def stack(v1, v2, dst, label_v1="V1 long camera blocks", label_v2="V2 short motion/lens/DoF"):
    # drawtext uses ':' as kv separator — escape colons in paths and text.
    fontesc = FONT.replace("\\", "/").replace(":", r"\:")
    esc = lambda s: s.replace(":", r"\:").replace("'", r"\'")
    vf = (
        f"[0:v]scale=512:-2,drawtext=fontfile='{fontesc}'"
        f":text='{esc(label_v1)}':x=10:y=h-th-10:fontsize=18:fontcolor=white"
        f":box=1:boxcolor=black@0.7:boxborderw=6[a];"
        f"[1:v]scale=512:-2,drawtext=fontfile='{fontesc}'"
        f":text='{esc(label_v2)}':x=10:y=h-th-10:fontsize=18:fontcolor=white"
        f":box=1:boxcolor=black@0.7:boxborderw=6[b];"
        f"[a][b]hstack=inputs=2[v]"
    )
    cmd = ["ffmpeg", "-y", "-i", v1, "-i", v2,
           "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast",
           "-c:a", "aac", dst]
    subprocess.run(cmd, check=True, capture_output=True)

def main():
    v1s = {f for f in os.listdir(V1_DIR) if f.endswith(".mp4")}
    v2s = {f for f in os.listdir(V2_DIR) if f.endswith(".mp4")}
    pairs = sorted(v1s & v2s)
    print(f"[ab] {len(pairs)} matched pairs (v1={len(v1s)}, v2={len(v2s)})", flush=True)
    if not pairs:
        return

    built, skipped, failed = [], [], []
    for fn in pairs:
        src1 = os.path.join(V1_DIR, fn)
        src2 = os.path.join(V2_DIR, fn)
        dst  = os.path.join(AB_DIR, fn)
        # skip if fresh
        if os.path.exists(dst) and os.path.getmtime(dst) > max(os.path.getmtime(src1), os.path.getmtime(src2)):
            skipped.append(fn); continue
        try:
            stack(src1, src2, dst)
            built.append(fn)
            print(f"  ok  {fn}", flush=True)
        except subprocess.CalledProcessError as e:
            failed.append(fn)
            print(f"  FAIL {fn}: {e.stderr.decode('utf-8','replace')[-200:]}", flush=True)

    # HTML index grouped by block
    rows = []
    for blk in ("A", "B", "C"):
        recs = [p for p in pairs if p.startswith(blk + "_")]
        if not recs:
            continue
        rows.append(f"<h2>Block {blk}</h2><div class=grid>")
        for fn in recs:
            label = fn[:-4]
            rows.append(
                f'<div class=cell><div class=cap>{label}</div>'
                f'<video src="{fn}" controls width=800></video></div>')
        rows.append("</div>")
    html = ("<!doctype html><meta charset=utf-8><title>Cinema sweep V1 vs V2</title>"
            "<style>body{font:13px system-ui;background:#0e0e0e;color:#eee;margin:20px}"
            ".grid{display:flex;flex-direction:column;gap:18px}.cell{background:#1c1c1c;"
            "padding:10px;border-radius:6px}.cap{font-weight:700;margin-bottom:6px}"
            "h2{border-bottom:1px solid #333;padding-bottom:4px}</style>"
            f"<h1>Cinema sweep — V1 (left) vs V2 (right) — {datetime.datetime.now():%Y-%m-%d %H:%M}</h1>"
            f"<p>{len(pairs)} matched pairs. Built {len(built)}, reused {len(skipped)}, failed {len(failed)}.</p>"
            + "".join(rows))
    io.open(os.path.join(AB_DIR, "index.html"), "w", encoding="utf-8").write(html)
    print(f"[ab] DONE — built {len(built)}, skipped {len(skipped)}, failed {len(failed)}", flush=True)
    print(f"[ab] open {os.path.join(AB_DIR, 'index.html')}", flush=True)

    # --- single-timeline reel: every A/B pair concatenated in block order --
    reel = os.path.join(AB_DIR, "_reel_all.mp4")
    ordered = sorted(pairs, key=lambda f: (f[0], f))  # A_*, B_*, C_*
    concat_list = os.path.join(AB_DIR, "_concat.txt")
    with io.open(concat_list, "w", encoding="utf-8") as fp:
        for fn in ordered:
            mp4 = os.path.join(AB_DIR, fn).replace("\\", "/")
            if os.path.exists(mp4):
                fp.write(f"file '{mp4}'\n")
    try:
        # re-encode (uniform codec/params from stack()) so concat is safe
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast",
             "-c:a", "aac", "-movflags", "+faststart", reel],
            check=True, capture_output=True)
        print(f"[ab] reel: {reel}  ({len(ordered)} pairs)", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"[ab] reel FAILED: {e.stderr.decode('utf-8','replace')[-400:]}", flush=True)

if __name__ == "__main__":
    main()
