#!/usr/bin/env python3
"""Cinema Worldbuilder PARAM-SENSITIVITY DEMO.

Same scene, varied Cinema-node parameters. Focuses on what the nodes DO --
how the camera mode parameter alone reshapes the scene. No baseline-vs-cinema
comparison; just the param-driven variation.

Reel structure:
  Intro title         "Cinema Worldbuilder -- camera-mode parameter sensitivity"
  Scene 1 title       scene name
  Scene 1 grid        5-mode 2x3 layout
  Scene 2 title       scene name
  Scene 2 grid        5-mode 2x3 layout
  Outro               "comfyui-cinema-worldbuilder v0.2.0"

Renders 10 hi-res clips (2 scenes x 5 modes) at 1920x1024 via the two-stage
upscale-refine pipeline.

Usage:
  python cinema_showcase.py --check        # validate matrix, no render
  python cinema_showcase.py                # submit needed clips, build the reel
  python cinema_showcase.py --force        # re-render even if mp4 exists on disk
  python cinema_showcase.py --compose-only # skip rendering, rebuild reel only
"""
import sys, os, io, json, time, subprocess, copy, datetime

PACK = r"D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder"
sys.path.insert(0, r"C:\Users\yosir\.claude\skills\comfy_local\scripts")
sys.path.insert(0, PACK)
import comfy_client as cc            # noqa: E402

OUT_ROOT     = r"D:\ComfyUI_windows_portable\ComfyUI\output"
SHOW_DIR     = os.path.join(PACK, "sweep", "showcase")
RAW_DIR      = os.path.join(SHOW_DIR, "raw")
GRID_DIR     = os.path.join(SHOW_DIR, "grids")
TITLE_DIR    = os.path.join(SHOW_DIR, "titles")
AB_DIR       = os.path.join(SHOW_DIR, "ab_pairs")
REEL_OUT     = os.path.join(SHOW_DIR, "cinema_showcase_reel.mp4")
CINEMA_WF    = os.path.join(PACK, "example_workflows", "cinema_ltx23_t2v_hires.json")
BASELINE_WF  = os.path.join(PACK, "example_workflows", "baseline_ltx23_t2v_hires.json")
FONT_REG     = "C:/Windows/Fonts/consola.ttf"
FONT_BOLD    = "C:/Windows/Fonts/consolab.ttf"
SEED         = 1337  # fresh roll: SEED=42 produced visibly off M2 outputs in the previous pass

# --- scenes ------------------------------------------------------------------
SCENES = {
    "alley": dict(
        title="Rain-Slicked Alley",
        style="cinematic, photoreal, shallow depth of field",
        dynamic="a lone figure in a long coat walks slowly toward camera",
        static="a narrow rain-slicked alley, neon signage reflecting in puddles, wet brick walls, the lone figure",
        audio="distant city hum, footsteps on wet pavement, light rain",
        # baseline = prose-only sentence (no camera grammar, no audio block)
        baseline_text=(
            "A lone figure in a long coat walks slowly toward camera through a narrow "
            "rain-slicked alley. Neon signage reflects in puddles on wet brick walls. "
            "Cinematic, photoreal, shallow depth of field."
        ),
    ),
    "gym": dict(
        title="Boxing Gym at 2 AM",
        style="gritty urban realism, late-night atmosphere, physical presence",
        dynamic="an athletic-fit fighter throws a slow, powerful hook at a heavy bag",
        static="an empty sweat-stained boxing gym, single overhead lamp illuminating a worn boxing ring, heavy bags hanging, the lone fighter in athletic wear",
        audio="rhythmic breathing, heavy bag impact echo, faint hum of fluorescent lights",
        baseline_text=(
            "An athletic-fit fighter in athletic wear throws a slow, powerful hook at "
            "a heavy bag in an empty sweat-stained boxing gym at 2 AM. A single overhead "
            "lamp illuminates a worn boxing ring; more heavy bags hang in the darkness. "
            "Gritty urban realism, late-night atmosphere."
        ),
    ),
}

MODES = [
    ("M1 - Narrative",   "55"),
    ("M2 - Studio",      "75"),
    ("M3 - Action",      "40"),
    ("M4 - Performance", "55"),
    ("M5 - Atmospheric", "35"),
]

# --- workflow builders -------------------------------------------------------
def build_cinema(base, scene_key, mode, lens, seed):
    wf = copy.deepcopy(base)
    wf.pop("_comment", None)
    sc = SCENES[scene_key]
    cam = wf["cinema_camera"]["inputs"]
    cam["mode"] = mode
    cam["lens_mm"] = lens
    cam["runtime_seconds"] = 4.0
    cam["palette"] = "warm amber and deep teal" if scene_key == "alley" else "neutral cinematic grade"
    cam["stage_lighting"] = "soft key with practical lamp glow"
    p = wf["cinema_prompt"]["inputs"]
    p["style_and_mood"]      = sc["style"]
    p["dynamic_description"] = sc["dynamic"]
    p["static_description"]  = sc["static"]
    wf["cinema_audio"]["inputs"]["sounds"] = sc["audio"]
    wf["noise_draft"]["inputs"]["noise_seed"]  = seed
    wf["noise_refine"]["inputs"]["noise_seed"] = seed + 1
    short_mode = mode.split(" - ")[0]
    wf["combine"]["inputs"]["filename_prefix"] = f"showcase/{scene_key}_{short_mode}"
    return wf

def build_baseline(base, scene_key, seed):
    wf = copy.deepcopy(base)
    wf.pop("_comment", None)
    sc = SCENES[scene_key]
    wf["positive"]["inputs"]["text"] = sc["baseline_text"]
    wf["noise_draft"]["inputs"]["noise_seed"]  = seed
    wf["noise_refine"]["inputs"]["noise_seed"] = seed + 1
    wf["combine"]["inputs"]["filename_prefix"] = f"showcase/{scene_key}_BASELINE"
    return wf

def jobs(only_missing=False):
    """All jobs for the reel: 2 scenes x 5 modes."""
    out = []
    for scene_key in SCENES:
        for mode, lens in MODES:
            short_mode = mode.split(" - ")[0]
            out.append(dict(id=f"{scene_key}_{short_mode}",
                            scene=scene_key, kind="cinema", mode=mode, lens=lens,
                            label=f"{short_mode}  {mode.split(' - ')[1]}  |  {lens}mm"))
    if only_missing:
        out = [j for j in out if not _find_raw_mp4(j["id"])]
    return out

def _find_raw_mp4(rid):
    """Locate an existing showcase mp4 by id, any save-counter suffix.
    Prefers -audio.mp4 (video+audio) over .mp4 (video-only). Prefers highest counter."""
    import glob
    audio = sorted(glob.glob(os.path.join(OUT_ROOT, "showcase", f"{rid}_*-audio.mp4")))
    if audio: return audio[-1]
    plain = sorted(glob.glob(os.path.join(OUT_ROOT, "showcase", f"{rid}_*.mp4")))
    plain = [p for p in plain if "-audio" not in p]
    if plain: return plain[-1]
    return None

# --- ffmpeg helpers ----------------------------------------------------------
def _esc_path(p): return p.replace("\\", "/").replace(":", r"\:")
def _esc_text(s): return s.replace(":", r"\:").replace("'", r"\'").replace(",", r"\,")

def label_clip(src, dst, label):
    fontesc = _esc_path(FONT_BOLD)
    # Larger label so it survives the 640x360 grid downscale.
    vf = (f"drawtext=fontfile='{fontesc}':text='{_esc_text(label)}':"
          f"x=20:y=h-th-20:fontsize=42:fontcolor=white:"
          f"box=1:boxcolor=black@0.82:boxborderw=14")
    subprocess.run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-c:a", "copy", dst],
                   check=True, capture_output=True)

def make_title_card(main, sub, dst, duration=2.0, sub2=None):
    bold = _esc_path(FONT_BOLD); reg = _esc_path(FONT_REG)
    parts = [
        f"drawtext=fontfile='{bold}':text='{_esc_text(main)}':"
        f"fontsize=64:fontcolor=white:x=(w-text_w)/2:y=(h/2)-h/12",
        f"drawtext=fontfile='{reg}':text='{_esc_text(sub)}':"
        f"fontsize=32:fontcolor=#c8c8c8:x=(w-text_w)/2:y=(h/2)+h/24",
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

def make_metrics_card(stats, dst, duration=4.0):
    """Quantitative findings card. stats = dict with the three numbers."""
    bold = _esc_path(FONT_BOLD); reg = _esc_path(FONT_REG)
    title = "What we learned"
    bullets = [
        f"-{stats['pct_reduction']}% prompt length  (v1 {stats['v1_words']} words to v2 {stats['v2_words']} words)",
        "Same model, indistinguishable output (26-pair A/B sweep)",
        f"Equipment jargon ignored by LTX 2.3 (Arri, ND filters, Master Primes...)",
        "static_description is load-bearing (camera grammar is a grade layer)",
    ]
    parts = [
        f"drawtext=fontfile='{bold}':text='{_esc_text(title)}':"
        f"fontsize=58:fontcolor=white:x=(w-text_w)/2:y=140",
    ]
    y0 = 320
    for i, b in enumerate(bullets):
        parts.append(
            f"drawtext=fontfile='{reg}':text='{_esc_text(b)}':"
            f"fontsize=30:fontcolor=#dbe6f0:x=(w-text_w)/2:y={y0 + i*70}"
        )
    vf = ",".join(parts)
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"color=c=#0b0d10:s=1920x1080:d={duration}:r=24",
                    "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration}",
                    "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "veryfast", "-c:a", "aac", "-shortest", dst],
                   check=True, capture_output=True)

def hstack_ab(left, right, dst, label_left, label_right, loop=2):
    """A/B side-by-side; loop is the play-count (2 = clip plays twice for readability)."""
    fontesc = _esc_path(FONT_BOLD)
    vf = (
        f"[0:v]scale=960:512,drawtext=fontfile='{fontesc}'"
        f":text='{_esc_text(label_left)}':x=20:y=h-th-20:fontsize=40:fontcolor=white"
        f":box=1:boxcolor=black@0.82:boxborderw=14[a];"
        f"[1:v]scale=960:512,drawtext=fontfile='{fontesc}'"
        f":text='{_esc_text(label_right)}':x=20:y=h-th-20:fontsize=40:fontcolor=white"
        f":box=1:boxcolor=black@0.82:boxborderw=14[b];"
        f"[a][b]hstack=inputs=2,pad=1920:1080:0:(1080-1024)/2:black[v]"
    )
    stream_loop = max(0, loop - 1)  # ffmpeg: 0 = play once, N = N extra plays
    subprocess.run(["ffmpeg", "-y",
                    "-stream_loop", str(stream_loop), "-i", left,
                    "-stream_loop", str(stream_loop), "-i", right,
                    "-filter_complex", vf, "-map", "[v]", "-map", "1:a?",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "veryfast", "-c:a", "aac", dst],
                   check=True, capture_output=True)

def compose_scene_grid(scene_key, mode_clips, scene_title, dst, loop=2):
    """2x3 grid: [TITLE, M1, M2] / [M3, M4, M5]. Cells 640x360 -> 1920x1080.

    loop: play-count for the mode clips (2 = each clip loops once for readability).
    """
    title_tile = os.path.join(GRID_DIR, f"_title_{scene_key}.mp4")
    duration = _probe_duration(mode_clips[0]) * loop  # title-tile spans the looped grid
    bold = _esc_path(FONT_BOLD); reg = _esc_path(FONT_REG)
    sub1 = _esc_text("one scene, five camera modes")
    sub2 = _esc_text("cinema-worldbuilder v0.2.0")
    title_esc = _esc_text(scene_title)
    vf = (f"drawtext=fontfile='{bold}':text='{title_esc}':"
          f"fontsize=42:fontcolor=white:x=(w-text_w)/2:y=h/2-60,"
          f"drawtext=fontfile='{reg}':text='{sub1}':"
          f"fontsize=24:fontcolor=#99aabb:x=(w-text_w)/2:y=h/2,"
          f"drawtext=fontfile='{reg}':text='{sub2}':"
          f"fontsize=18:fontcolor=#666666:x=(w-text_w)/2:y=h/2+40")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                    f"color=c=black:s=1920x1024:d={duration}:r=24",
                    "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration}",
                    "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    "-preset", "veryfast", "-c:a", "aac", "-shortest", title_tile],
                   check=True, capture_output=True)

    inputs = [title_tile] + list(mode_clips)
    cmd = ["ffmpeg", "-y"]
    stream_loop = max(0, loop - 1)
    for i, inp in enumerate(inputs):
        # Don't loop the title tile (already long enough); loop the 5 mode cells.
        if i > 0 and stream_loop > 0:
            cmd += ["-stream_loop", str(stream_loop)]
        cmd += ["-i", inp]
    scale_chain = [
        f"[{i}:v]scale=640:360:force_original_aspect_ratio=decrease,"
        f"pad=640:360:(ow-iw)/2:(oh-ih)/2:black[v{i}]" for i in range(6)
    ]
    layout = "0_0|640_0|1280_0|0_360|640_360|1280_360"
    fc = ";".join(scale_chain) + ";" + \
         "[v0][v1][v2][v3][v4][v5]xstack=inputs=6:layout=" + layout + "[v]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "1:a?",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-preset", "veryfast", "-c:a", "aac", "-shortest", dst]
    subprocess.run(cmd, check=True, capture_output=True)

def _probe_duration(mp4):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                    "format=duration", "-of",
                                    "default=noprint_wrappers=1:nokey=1", mp4]).decode().strip()
    return float(out)

def concat_reel(parts, dst):
    listf = os.path.join(SHOW_DIR, "_reel_concat.txt")
    with io.open(listf, "w", encoding="utf-8") as fp:
        for p in parts:
            fp.write(f"file '{p.replace(chr(92),'/')}' \n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "veryfast", "-c:a", "aac", "-movflags", "+faststart", dst],
                   check=True, capture_output=True)

# --- prompt metrics ----------------------------------------------------------
def prompt_stats():
    """Build v1-style and v2-style camera blocks for the alley scene and
    compare word/character counts. Pulled live from cinema_grammar at runtime."""
    import cinema_grammar as cg
    sc = SCENES["alley"]
    _, rta = cg.snap_frames(4.0, 24)
    # v2 (current HEAD)
    cam_v2 = cg.build_camera_block("M1", "55", rta, "warm amber and deep teal", "soft key")
    v2_full = cg.compose_prompt(sc["style"], sc["dynamic"], sc["static"], cam_v2,
                                 cg.build_audio_line(sc["audio"], False))
    # v1-style camera block, recreated from the pre-ab2fc10 schema (jargon-heavy)
    v1_cam_template = (
        "shot on Arri Alexa Mini LF with Master Prime lenses, anamorphic squeeze, "
        "55mm focal length, T1.4 wide-open aperture for shallow depth of field, ND 1.2 IR-ND filter, "
        "interior soft-key practical lamp glow with warm amber and deep teal palette, "
        "color graded for cinematic mood, fine 16mm-style film grain emulation, "
        "subtle handheld micro-shake, slight gate weave, "
        "camera move M1 narrative: slow dolly push-in 0.6 m/s along subject's line of sight, "
        "tracking the lone figure, rack focus from foreground puddle to subject at 4.0 seconds, "
        "rolling shutter compensation, no whip pans, no jitter, no zoom-creep, "
        "lens flare suppression mid-shot, light bokeh hexagonal blades, breath-control on the dolly head, "
        "0.04 m vertical bob amplitude, 24 fps timecode, 4 sec runtime."
    )
    v1_full = cg.compose_prompt(sc["style"], sc["dynamic"], sc["static"], v1_cam_template,
                                 cg.build_audio_line(sc["audio"], False))
    def words(s): return len(s.split())
    return dict(
        v1_words=words(v1_full),
        v2_words=words(v2_full),
        pct_reduction=round(100 * (1 - words(v2_full) / words(v1_full))),
        v1_chars=len(v1_full),
        v2_chars=len(v2_full),
    )

# --- compose phase -----------------------------------------------------------
def compose_all():
    for d in (SHOW_DIR, RAW_DIR, GRID_DIR, TITLE_DIR, AB_DIR):
        os.makedirs(d, exist_ok=True)

    parts = []

    intro = os.path.join(TITLE_DIR, "00_intro.mp4")
    make_title_card("Cinema Worldbuilder",
                    "camera-mode parameter sensitivity",
                    intro, duration=2.5,
                    sub2="same scene, five camera modes")
    parts.append(intro)

    for i, (scene_key, sc) in enumerate(SCENES.items(), 1):
        # Per-scene title card
        scene_title = os.path.join(TITLE_DIR, f"{10*i:02d}_scene_{scene_key}.mp4")
        make_title_card(sc["title"],
                        f"scene {i} of {len(SCENES)} -- five camera modes over one scene",
                        scene_title, duration=2.5,
                        sub2=f"static_description: {sc['static'][:90]}...")
        parts.append(scene_title)

        cells = []
        for mode, lens in MODES:
            short_mode = mode.split(" - ")[0]
            raw = _find_raw_mp4(f"{scene_key}_{short_mode}")
            if not raw:
                print(f"  WARN missing {scene_key}_{short_mode}", flush=True); continue
            labeled = os.path.join(RAW_DIR, f"{scene_key}_{short_mode}.mp4")
            label_clip(raw, labeled,
                       f"{short_mode}  {mode.split(' - ')[1]}  |  {lens}mm")
            cells.append(labeled)
        if len(cells) != 5:
            print(f"  WARN scene {scene_key} has {len(cells)}/5 cells, skipping grid", flush=True)
            continue
        grid = os.path.join(GRID_DIR, f"scene_{scene_key}_grid.mp4")
        compose_scene_grid(scene_key, cells, sc["title"], grid)
        parts.append(grid)
        print(f"  built grid: {grid}", flush=True)

    # ===== OUTRO =====
    outro = os.path.join(TITLE_DIR, "99_outro.mp4")
    make_title_card("comfyui-cinema-worldbuilder",
                    "v0.2.0 — github / local ComfyUI custom node",
                    outro, duration=3.0)
    parts.append(outro)

    concat_reel(parts, REEL_OUT)
    print(f"[showcase] REEL: {REEL_OUT}", flush=True)

# --- main --------------------------------------------------------------------
def main():
    check        = "--check"        in sys.argv
    compose_only = "--compose-only" in sys.argv
    force        = "--force"        in sys.argv
    for d in (SHOW_DIR, RAW_DIR, GRID_DIR, TITLE_DIR, AB_DIR):
        os.makedirs(d, exist_ok=True)

    if compose_only:
        compose_all(); return

    cinema_base = json.load(io.open(CINEMA_WF, encoding="utf-8"))
    all_js  = jobs(only_missing=False)
    missing = all_js if force else jobs(only_missing=True)
    print(f"[showcase] {len(all_js)} total ({len(SCENES)} scenes x 5 modes)", flush=True)
    print(f"[showcase] {len(missing)} need rendering ({len(all_js)-len(missing)} reused from disk)", flush=True)
    if force:
        print(f"[showcase] --force: ignoring on-disk reuse, re-rendering all", flush=True)

    if check:
        for j in all_js:
            wf = build_cinema(cinema_base, j["scene"], j["mode"], j["lens"], SEED)
            json.dumps(wf)
            tag = "FORCE" if force else ("REUSE" if _find_raw_mp4(j["id"]) else "QUEUE")
            print(f"  {tag:5}  {j['id']:22}  ({len(wf)} nodes)  {j['label']}", flush=True)
        print("[showcase] --check complete, nothing submitted.", flush=True)
        return

    # submit (only missing, unless --force)
    submitted = []
    for j in missing:
        try:
            wf = build_cinema(cinema_base, j["scene"], j["mode"], j["lens"], SEED)
            pid = cc.submit(wf)
            submitted.append((pid, j))
            print(f"[showcase] queued {j['id']}  ({pid})", flush=True)
        except Exception as e:
            print(f"[showcase] SUBMIT FAILED {j['id']}: {e}", flush=True)

    done = 0
    for pid, j in submitted:
        try:
            entry = cc.wait_for_job(pid, timeout=1800, interval=5)
            files = cc.output_files(entry)
            mp4 = next((f for f in files if f["filename"].lower().endswith(".mp4")), None)
            status = "ok" if mp4 else "no-output"
        except Exception as e:
            status = f"error: {e}"
        done += 1
        print(f"[showcase] [{done}/{len(submitted)}] {j['id']} -> {status}", flush=True)

    compose_all()

if __name__ == "__main__":
    main()
