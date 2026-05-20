#!/usr/bin/env python3
"""Build evidence figures for FINDINGS_FOR_LTX.md.

Reads existing sweep outputs (no rendering); produces self-contained MP4s:
  figure_1_jargon_decorative.mp4   <- 26-pair v1-vs-v2 A/B with research title card
  figure_2_static_load_bearing.mp4 <- Block B alley FULL/PROSE/CAMERA triptych

Both figures stand alone as supporting evidence for the findings doc.
"""
import os, io, subprocess, datetime

PACK     = r"D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder"
V1_DIR   = os.path.join(PACK, "sweep", "results")
V2_DIR   = os.path.join(PACK, "sweep", "results_v2")
AB_DIR   = os.path.join(PACK, "sweep", "results_ab")
FIG_DIR  = os.path.join(PACK, "sweep", "figures")
FONT_BOLD = "C:/Windows/Fonts/consolab.ttf"
FONT_REG  = "C:/Windows/Fonts/consola.ttf"
os.makedirs(FIG_DIR, exist_ok=True)

def _esc_path(p): return p.replace("\\", "/").replace(":", r"\:")
def _esc_text(s): return s.replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")

def make_title_card(lines, dst, duration=4.0, w=1920, h=1080, bg="#0b0d10"):
    """lines: list of (text, fontsize, color, y_offset_from_center)."""
    bold = _esc_path(FONT_BOLD); reg = _esc_path(FONT_REG)
    parts = []
    for text, size, color, dy in lines:
        font = bold if size >= 48 else reg
        parts.append(
            f"drawtext=fontfile='{font}':text='{_esc_text(text)}':"
            f"fontsize={size}:fontcolor={color}:x=(w-text_w)/2:y=(h/2)+({dy})"
        )
    vf = ",".join(parts)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"color=c={bg}:s={w}x{h}:d={duration}:r=24",
                    "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration}",
                    "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "veryfast", "-c:a", "aac", "-shortest", dst],
                   check=True, capture_output=True)

def concat(parts, dst):
    listf = os.path.join(FIG_DIR, "_concat.txt")
    with io.open(listf, "w", encoding="utf-8") as fp:
        for p in parts:
            fp.write(f"file '{p.replace(chr(92),'/')}' \n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart", dst],
                   check=True, capture_output=True)

def normalize(src, dst, width=1920, height=1080):
    """Scale-pad any input mp4 to 1920x1080 so concat doesn't reject mixed sizes."""
    subprocess.run(["ffmpeg", "-y", "-i", src,
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                           f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "veryfast", "-c:a", "aac", dst],
                   check=True, capture_output=True)

# ============================================================================
# Figure 1 — Finding 1: equipment vocabulary is decorative
# ============================================================================
def figure_1():
    src_reel = os.path.join(AB_DIR, "_reel_all.mp4")
    if not os.path.exists(src_reel):
        raise FileNotFoundError(f"missing {src_reel} — run sweep/ab_compare.py first")
    intro = os.path.join(FIG_DIR, "_fig1_intro.mp4")
    make_title_card([
        ("Figure 1",                                                          36, "#888888", "-h/3"),
        ("Equipment vocabulary is decorative",                                52, "white",   "-h/8"),
        ("180 -> 94 word camera block, 26 paired clips, indistinguishable.",  28, "#c8c8c8", "-h/24"),
        ("LEFT  v1 jargon grammar  (Arri, ND filters, Master Primes...)",     22, "#99aabb",    "h/16"),
        ("RIGHT v2 intent only     (motion, lighting, lens, palette, DoF)",   22, "#99aabb",    "h/12"),
        ("LTX 2.3 22B distilled 1.1 Q2_K  |  seed-paired, all else frozen",   18, "#666666", "h/4"),
    ], intro, duration=5.0)

    normalized = os.path.join(FIG_DIR, "_fig1_reel_norm.mp4")
    normalize(src_reel, normalized)

    dst = os.path.join(FIG_DIR, "figure_1_jargon_decorative.mp4")
    concat([intro, normalized], dst)
    print(f"  built {dst}")
    return dst

# ============================================================================
# Figure 2 — Finding 2: static_description is load-bearing
# ============================================================================
def figure_2():
    # Block B alley FULL / PROSE / CAMERA at seed 42 — proves the CAMERA-only collapse.
    full   = os.path.join(V1_DIR, "B_alley_FULL_s42.mp4")
    prose  = os.path.join(V1_DIR, "B_alley_PROSE_s42.mp4")
    camera = os.path.join(V1_DIR, "B_alley_CAMERA_s42.mp4")
    for p in (full, prose, camera):
        if not os.path.exists(p):
            raise FileNotFoundError(p)
    intro = os.path.join(FIG_DIR, "_fig2_intro.mp4")
    make_title_card([
        ("Figure 2",                                                          36, "#888888", "-h/3"),
        ("static_description is load-bearing",                                52, "white",   "-h/8"),
        ("Same alley scene, three prompt variants.",                          28, "#c8c8c8", "-h/24"),
        ("FULL   style + dynamic + static + camera_block + audio",            22, "#99aabb",    "h/24"),
        ("PROSE  style + dynamic + static  (no camera grammar)",              22, "#99aabb",    "h/12"),
        ("CAMERA dynamic + camera_block    (no static, no audio)  -> breaks", 22, "#ff9999", "h/6"),
        ("Camera grammar acts as a grade layer, not a content carrier.",      20, "#666666", "h/3"),
    ], intro, duration=5.0)

    # Stack three variants horizontally as a 3-way triptych
    triptych = os.path.join(FIG_DIR, "_fig2_triptych.mp4")
    font = _esc_path(FONT_BOLD)
    def cell(name, label):
        return (f"scale=640:360:force_original_aspect_ratio=decrease,"
                f"pad=640:360:(ow-iw)/2:(oh-ih)/2:black,"
                f"drawtext=fontfile='{font}':text='{_esc_text(label)}':"
                f"x=12:y=h-th-12:fontsize=22:fontcolor=white:"
                f"box=1:boxcolor=black@0.82:boxborderw=8[{name}]")
    fc = (f"[0:v]{cell('a','FULL')};"
          f"[1:v]{cell('b','PROSE')};"
          f"[2:v]{cell('c','CAMERA  no static_description')};"
          f"[a][b][c]hstack=inputs=3,pad=1920:1080:0:(1080-360)/2:black[v]")
    subprocess.run(["ffmpeg", "-y", "-i", full, "-i", prose, "-i", camera,
                    "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "veryfast", "-c:a", "aac", triptych],
                   check=True, capture_output=True)
    # Loop 2x via stream_loop on the encoded triptych so viewers get a 2nd pass.
    looped = os.path.join(FIG_DIR, "_fig2_triptych_looped.mp4")
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "1", "-i", triptych,
                    "-c", "copy", looped], check=True, capture_output=True)

    dst = os.path.join(FIG_DIR, "figure_2_static_load_bearing.mp4")
    concat([intro, looped], dst)
    print(f"  built {dst}")
    return dst

if __name__ == "__main__":
    f1 = figure_1()
    try:
        f2 = figure_2()
    except FileNotFoundError as e:
        print(f"  SKIP figure 2: {e}")
        f2 = None
    print(f"\nfigures/ contains:")
    for p in (f1, f2):
        if p and os.path.exists(p):
            sz = os.path.getsize(p)
            print(f"  {sz:>10} B  {p}")
