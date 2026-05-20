#!/usr/bin/env python3
"""Build the Q2_K-GGUF vs FP8-dev-LoRA full-showcase comparison reel.

Takes the 10 Q2_K showcase clips and the 10 fp8 cinema renders, builds a
side-by-side A/B per (scene, mode), wraps in title cards, concatenates into
one reel for Yosi to review side-by-side.

Inputs:
  Q2_K:  D:\\ComfyUI_windows_portable\\ComfyUI\\output\\showcase\\<scene>_<mode>_*-audio.mp4
  FP8 :  D:\\ComfyUI_windows_portable\\ComfyUI\\output\\fp8_smoke\\cinema_<scene>_<mode>_fp8_*.mp4

Output:
  sweep/fp8_compare/q2k_vs_fp8_full_reel.mp4
"""
import os, sys, io, glob, subprocess, datetime

PACK    = r"D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder"
OUT     = r"D:\ComfyUI_windows_portable\ComfyUI\output"
DST_DIR = os.path.join(PACK, "sweep", "fp8_compare")
REEL    = os.path.join(DST_DIR, "q2k_vs_fp8_full_reel.mp4")
FONT_BOLD = "C:/Windows/Fonts/consolab.ttf"
FONT_REG  = "C:/Windows/Fonts/consola.ttf"
os.makedirs(DST_DIR, exist_ok=True)

SCENES = ["alley", "gym"]
MODES  = [
    ("M1", "Narrative",   "55"),
    ("M2", "Studio",      "75"),
    ("M3", "Action",      "40"),
    ("M4", "Performance", "55"),
    ("M5", "Atmospheric", "35"),
]

def _esc_path(p): return p.replace("\\", "/").replace(":", r"\:")
def _esc_text(s): return s.replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")

def find_q2k(scene, short_mode):
    cands = sorted(glob.glob(os.path.join(OUT, "showcase", f"{scene}_{short_mode}_*-audio.mp4")))
    if cands: return cands[-1]
    cands = sorted(glob.glob(os.path.join(OUT, "showcase", f"{scene}_{short_mode}_*.mp4")))
    return [c for c in cands if "-audio" not in c][-1] if cands else None

def find_fp8(scene, short_mode):
    cands = sorted(glob.glob(os.path.join(OUT, "fp8_smoke", f"cinema_{scene}_{short_mode}_fp8_*.mp4")))
    return cands[-1] if cands else None

def ab_stack(q2k, fp8, dst, scene, mode_name, lens):
    fontesc = _esc_path(FONT_BOLD)
    title = f"{scene.upper()} - {mode_name} - {lens}mm"
    vf = (
        f"[0:v]scale=960:540:force_original_aspect_ratio=decrease,"
        f"pad=960:540:(ow-iw)/2:(oh-ih)/2:black,"
        f"drawtext=fontfile='{fontesc}':text='Q2_K GGUF':x=20:y=20:fontsize=28:fontcolor=white:"
        f"box=1:boxcolor=black@0.82:boxborderw=10[L];"
        f"[1:v]scale=960:540:force_original_aspect_ratio=decrease,"
        f"pad=960:540:(ow-iw)/2:(oh-ih)/2:black,"
        f"drawtext=fontfile='{fontesc}':text='FP8 dev + distill LoRA':x=20:y=20:fontsize=28:fontcolor=white:"
        f"box=1:boxcolor=black@0.82:boxborderw=10[R];"
        f"[L][R]hstack=inputs=2,"
        f"drawtext=fontfile='{fontesc}':text='{_esc_text(title)}':x=(w-text_w)/2:y=h-th-20:"
        f"fontsize=32:fontcolor=white:box=1:boxcolor=black@0.85:boxborderw=14,"
        f"pad=1920:1080:0:(1080-540)/2:black[v]"
    )
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "1", "-i", q2k, "-stream_loop", "1", "-i", fp8,
                    "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "veryfast", "-c:a", "aac", dst],
                   check=True, capture_output=True)

def make_title_card(main, sub, dst, duration=2.5, sub2=None):
    bold = _esc_path(FONT_BOLD); reg = _esc_path(FONT_REG)
    parts = [
        f"drawtext=fontfile='{bold}':text='{_esc_text(main)}':"
        f"fontsize=64:fontcolor=white:x=(w-text_w)/2:y=(h/2)-h/12",
        f"drawtext=fontfile='{reg}':text='{_esc_text(sub)}':"
        f"fontsize=32:fontcolor=#cccccc:x=(w-text_w)/2:y=(h/2)+h/24",
    ]
    if sub2:
        parts.append(
            f"drawtext=fontfile='{reg}':text='{_esc_text(sub2)}':"
            f"fontsize=22:fontcolor=#888888:x=(w-text_w)/2:y=(h/2)+h/8"
        )
    vf = ",".join(parts)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"color=c=black:s=1920x1080:d={duration}:r=24",
                    "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration}",
                    "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "veryfast", "-c:a", "aac", "-shortest", dst],
                   check=True, capture_output=True)

def concat(parts, dst):
    listf = os.path.join(DST_DIR, "_reel_concat.txt")
    with io.open(listf, "w", encoding="utf-8") as fp:
        for p in parts:
            fp.write(f"file '{p.replace(chr(92),'/')}' \n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart", dst],
                   check=True, capture_output=True)

def main():
    parts = []
    intro = os.path.join(DST_DIR, "_intro.mp4")
    make_title_card("Q2_K GGUF  vs  FP8 dev + distill LoRA",
                    "same Cinema Worldbuilder prose, two LTX 2.3 model variants",
                    intro, duration=3.0,
                    sub2="2 scenes x 5 modes = 10 paired clips")
    parts.append(intro)

    built = 0; missing = 0
    for scene in SCENES:
        for short, mode_name, lens in MODES:
            q2k = find_q2k(scene, short)
            fp8 = find_fp8(scene, short)
            if not (q2k and fp8):
                print(f"  WARN missing {scene}_{short} (q2k={bool(q2k)}, fp8={bool(fp8)})")
                missing += 1
                continue
            dst = os.path.join(DST_DIR, f"AB_{scene}_{short}.mp4")
            ab_stack(q2k, fp8, dst, scene, mode_name, lens)
            parts.append(dst)
            built += 1
            print(f"  built AB_{scene}_{short}")

    outro = os.path.join(DST_DIR, "_outro.mp4")
    make_title_card("Cinema Worldbuilder", "v0.2.0 -- LTX 2.3 model A/B",
                    outro, duration=3.0)
    parts.append(outro)

    concat(parts, REEL)
    print(f"\n[reel] built {built}, missing {missing}")
    print(f"[reel] OUT: {REEL}")

if __name__ == "__main__":
    main()
