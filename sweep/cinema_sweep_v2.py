#!/usr/bin/env python3
"""Cinema Worldbuilder t2v overnight validation sweep.

Renders a param matrix through cinema_ltx23_t2v, burns the render params onto
every mp4 (ffmpeg drawtext) so clips are self-identifying when compared, and
builds a review index. Blocks:
  A - Mode coverage      : all 5 modes x 2 seeds (uses the real Cinema nodes)
  B - Grammar A/B        : full cinema prompt vs prose-only vs camera-only
  C - Scene robustness   : hard-geometry vs soft-organic vs crowd

Usage:
  python cinema_sweep.py --check   # build+validate matrix, test ffmpeg, no render
  python cinema_sweep.py           # submit the whole sweep and post-process
"""
import sys, os, io, json, time, subprocess, copy, datetime

PACK = r"D:\ComfyUI_windows_portable\ComfyUI\custom_nodes\comfyui-cinema-worldbuilder"
sys.path.insert(0, r"C:\Users\yosir\.claude\skills\comfy_local\scripts")
sys.path.insert(0, PACK)
import comfy_client as cc            # noqa: E402
import cinema_grammar as cg          # noqa: E402

OUT_ROOT  = r"D:\ComfyUI_windows_portable\ComfyUI\output"
SWEEP_DIR = os.path.join(PACK, "sweep")
RESULTS   = os.path.join(SWEEP_DIR, "results_v2")
FRAMES    = os.path.join(RESULTS, "frames")
CAPDIR    = os.path.join(SWEEP_DIR, "_captions_v2")
BASE_WF   = os.path.join(PACK, "example_workflows", "cinema_ltx23_t2v.json")
FONT      = "C:/Windows/Fonts/consola.ttf"
SEEDS     = [42, 7]

# --- scenes ------------------------------------------------------------------
SCENES = {
    "alley": dict(
        style="cinematic, moody, photoreal, shallow depth of field",
        dynamic="a lone figure in a long coat walks slowly toward camera",
        static="a narrow rain-slicked alley, neon signage reflecting in puddles, wet brick walls",
        audio="distant city hum, footsteps on wet pavement, light rain"),
    "studio": dict(
        style="editorial fashion film, glossy, high-key lighting",
        dynamic="a model turns their head slowly toward the lens",
        static="a seamless white cyclorama studio with a single soft key light",
        audio="fabric rustle, faint room tone"),
    "corridor": dict(
        style="gritty documentary action realism",
        dynamic="a figure sprints down a corridor as debris falls around them",
        static="a concrete service corridor with hanging dust and flickering lights",
        audio="pounding footsteps, falling debris, ragged breath",
        palette="cool desaturated concrete grey"),
    "arena": dict(
        style="concert documentary, energetic, photoreal",
        dynamic="a performer throws an arm up as the crowd surges forward",
        static="a large arena stage with volumetric haze and a sea of raised hands",
        audio="roaring crowd, low stage rumble, clapping",
        stage="magenta and cyan strobe wash"),
    "hall": dict(
        style="atmospheric environment plate, still and quiet",
        dynamic="the camera drifts slowly forward through the empty hall",
        static="a derelict grand interior, dust in shafts of light, broken glass, no people",
        audio="low wind, distant creaks, faint dripping water",
        palette="muted greys and pale amber"),
    "bridge": dict(
        style="high-contrast monochrome, sharp focus, cinematic",
        dynamic="the camera moves steadily forward along an old steel truss bridge",
        static="riveted iron lattice girders arching overhead, a long walkway receding to a vanishing point",
        audio="wind through steel, distant traffic hum"),
    "serum": dict(
        style="macro photography, soft translucent, cinematic",
        dynamic="translucent serum swirls and folds slowly",
        static="a macro view of glossy organic fluid with soft translucent membranes",
        audio="soft liquid movement, faint hum"),
    "market": dict(
        style="documentary realism, warm, photoreal",
        dynamic="people move through the frame in many directions",
        static="a dense crowded market square at dusk, stalls and hanging lanterns",
        audio="crowd chatter, footsteps, distant music box"),
}

# --- matrix ------------------------------------------------------------------
def _full(scene, mode, lens, rt=4.0):
    _, rta = cg.snap_frames(rt, 24)
    cam = cg.build_camera_block(mode, lens, rta, scene.get("palette", ""), scene.get("stage", ""))
    aud = cg.build_audio_line(scene["audio"], False)
    return cg.compose_prompt(scene["style"], scene["dynamic"], scene["static"], cam, aud)

def _prose(scene):
    return cg.compose_prompt(scene["style"], scene["dynamic"], scene["static"], "", "")

def _camera(scene, mode, lens, rt=4.0):
    _, rta = cg.snap_frames(rt, 24)
    cam = cg.build_camera_block(mode, lens, rta, scene.get("palette", ""), scene.get("stage", ""))
    return cg.compose_prompt("", scene["dynamic"], "", cam, "")

def build_jobs():
    jobs = []
    # Block A - mode coverage (real Cinema nodes)
    a_modes = [("M1 - Narrative", "alley", "55"), ("M2 - Studio", "studio", "75"),
               ("M3 - Action", "corridor", "40"), ("M4 - Performance", "arena", "55"),
               ("M5 - Atmospheric", "hall", "35")]
    for mode, scene_key, lens in a_modes:
        for seed in SEEDS:
            mk = mode.split(" - ")[0]
            jobs.append(dict(
                id=f"A_{mk}_s{seed}", block="A", kind="cinema", seed=seed,
                cam_mode=mode, lens=lens, scene=scene_key,
                caption=f"A mode-coverage | {mode} | lens {lens}mm | seed {seed} | scene={scene_key}"))
    # Block B - grammar A/B (direct text, Cinema nodes bypassed)
    for scene_key in ("alley", "bridge"):
        sc = SCENES[scene_key]
        for variant, text in (("FULL", _full(sc, "M1", "55")),
                              ("PROSE", _prose(sc)),
                              ("CAMERA", _camera(sc, "M1", "55"))):
            for seed in SEEDS:
                jobs.append(dict(
                    id=f"B_{scene_key}_{variant}_s{seed}", block="B", kind="text", seed=seed,
                    prompt_text=text,
                    caption=f"B grammar-AB | variant={variant} | scene={scene_key} | seed {seed}"))
    # Block C - scene robustness (real Cinema nodes, M1 fixed)
    for scene_key, tag in (("bridge", "hard-geometry"), ("serum", "soft-organic"),
                           ("market", "crowd")):
        for seed in SEEDS:
            jobs.append(dict(
                id=f"C_{scene_key}_s{seed}", block="C", kind="cinema", seed=seed,
                cam_mode="M1 - Narrative", lens="55", scene=scene_key,
                caption=f"C scene-robustness | type={tag} | scene={scene_key} | M1 55mm | seed {seed}"))
    return jobs

# --- workflow build ----------------------------------------------------------
def build_workflow(base, job):
    wf = copy.deepcopy(base)
    wf.pop("_comment", None)
    wf["noise"]["inputs"]["noise_seed"] = job["seed"]
    wf["combine"]["inputs"]["filename_prefix"] = "sweep_v2/" + job["id"]
    if job["kind"] == "cinema":
        sc = SCENES[job["scene"]]
        cam = wf["cinema_camera"]["inputs"]
        cam["mode"] = job["cam_mode"]
        cam["lens_mm"] = job["lens"]
        cam["runtime_seconds"] = 4.0
        cam["palette"] = sc.get("palette", "warm neutral grade")
        cam["stage_lighting"] = sc.get("stage", "soft neutral wash")
        p = wf["cinema_prompt"]["inputs"]
        p["style_and_mood"] = sc["style"]
        p["dynamic_description"] = sc["dynamic"]
        p["static_description"] = sc["static"]
        wf["cinema_audio"]["inputs"]["sounds"] = sc["audio"]
    else:  # text — drop the Cinema nodes, feed CLIPTextEncode directly
        for k in ("cinema_camera", "cinema_audio", "cinema_prompt"):
            wf.pop(k, None)
        wf["positive"]["inputs"]["text"] = job["prompt_text"]
        wf["empty_video_latent"]["inputs"]["length"] = 97
        wf["empty_audio_latent"]["inputs"]["frames_number"] = 97
    return wf

# --- ffmpeg: burn params onto the mp4 ---------------------------------------
def burn_params(src_mp4, job, dst_mp4):
    capfile = os.path.join(CAPDIR, job["id"] + ".txt")
    io.open(capfile, "w", encoding="utf-8").write(job["id"] + "\n" + job["caption"])
    esc = lambda p: p.replace("\\", "/").replace(":", r"\:")
    vf = (f"drawtext=fontfile='{esc(FONT)}':textfile='{esc(capfile)}':"
          f"x=12:y=12:fontsize=20:fontcolor=white:box=1:boxcolor=black@0.6:"
          f"boxborderw=8:line_spacing=5")
    subprocess.run(["ffmpeg", "-y", "-i", src_mp4, "-vf", vf, "-c:a", "copy", dst_mp4],
                   check=True, capture_output=True)

def extract_frame(mp4, png):
    subprocess.run(["ffmpeg", "-y", "-i", mp4, "-vf", "select=gte(n\\,20)",
                    "-vframes", "1", png], check=True, capture_output=True)

# --- review index ------------------------------------------------------------
def write_index(records):
    rows = []
    for blk in ("A", "B", "C"):
        recs = [r for r in records if r["block"] == blk]
        if not recs:
            continue
        rows.append(f"<h2>Block {blk}</h2><div class=grid>")
        for r in recs:
            status = r["status"]
            vid = f'<video src="{r["mp4"]}" controls width=384></video>' if r.get("mp4") else "<i>no output</i>"
            rows.append(f'<div class=cell><div class=cap>{r["id"]} — {status}</div>'
                         f'<div class=det>{r["caption"]}</div>{vid}</div>')
        rows.append("</div>")
    html = ("<!doctype html><meta charset=utf-8><title>Cinema sweep</title>"
            "<style>body{font:13px system-ui;background:#111;color:#eee;margin:20px}"
            ".grid{display:flex;flex-wrap:wrap;gap:14px}.cell{background:#1c1c1c;padding:8px;"
            "border-radius:6px}.cap{font-weight:700}.det{color:#9ab;margin:3px 0 6px;max-width:384px}"
            "h2{border-bottom:1px solid #333;padding-bottom:4px}</style>"
            f"<h1>Cinema Worldbuilder t2v sweep — {datetime.datetime.now():%Y-%m-%d %H:%M}</h1>"
            + "".join(rows))
    io.open(os.path.join(RESULTS, "index.html"), "w", encoding="utf-8").write(html)

# --- main --------------------------------------------------------------------
def main():
    check = "--check" in sys.argv
    only = None
    for a in sys.argv:
        if a.startswith("--only="):
            only = set(a.split("=", 1)[1].split(","))
    for d in (RESULTS, FRAMES, CAPDIR):
        os.makedirs(d, exist_ok=True)
    base = json.load(io.open(BASE_WF, encoding="utf-8"))
    jobs = build_jobs()
    if only:
        jobs = [j for j in jobs if j["id"] in only]
        print(f"[sweep] --only filter -> {len(jobs)} jobs: {[j['id'] for j in jobs]}", flush=True)
    print(f"[sweep] {len(jobs)} jobs across blocks A/B/C", flush=True)

    if check:
        for j in jobs:
            wf = build_workflow(base, j)
            json.dumps(wf)  # must be serializable
            print(f"  OK  {j['id']:22} ({len(wf)} nodes)  {j['caption']}", flush=True)
        # ffmpeg drawtext smoke test on any existing output mp4
        sample = next((f for f in os.listdir(OUT_ROOT) if f.lower().endswith(".mp4")), None)
        if sample:
            try:
                burn_params(os.path.join(OUT_ROOT, sample), jobs[0],
                            os.path.join(CAPDIR, "_ffmpeg_test.mp4"))
                print("[sweep] ffmpeg drawtext smoke test: OK", flush=True)
            except subprocess.CalledProcessError as e:
                print("[sweep] ffmpeg test FAILED:", e.stderr.decode("utf-8", "replace")[-400:], flush=True)
        print("[sweep] --check complete, nothing submitted.", flush=True)
        return

    # submit everything up front — the queue is sequential
    submitted = []
    for j in jobs:
        try:
            pid = cc.submit(build_workflow(base, j))
            submitted.append((pid, j))
            print(f"[sweep] queued {j['id']}  ({pid})", flush=True)
        except Exception as e:
            print(f"[sweep] SUBMIT FAILED {j['id']}: {e}", flush=True)
            submitted.append((None, j))

    records, done = [], 0
    for pid, j in submitted:
        rec = dict(id=j["id"], block=j["block"], caption=j["caption"], status="error", mp4=None)
        if pid:
            try:
                entry = cc.wait_for_job(pid, timeout=1800, interval=5)
                files = cc.output_files(entry)
                mp4 = next((f for f in files if f["filename"].lower().endswith(".mp4")), None)
                if mp4:
                    src = os.path.join(OUT_ROOT, mp4.get("subfolder", ""), mp4["filename"])
                    dst = os.path.join(RESULTS, j["id"] + ".mp4")
                    try:
                        burn_params(src, j, dst)
                        rec["mp4"] = j["id"] + ".mp4"
                        rec["status"] = "ok"
                        try:
                            extract_frame(dst, os.path.join(FRAMES, j["id"] + ".png"))
                        except subprocess.CalledProcessError:
                            pass
                    except subprocess.CalledProcessError as e:
                        # keep the raw render even if the caption burn fails
                        rec["status"] = "ok-nolabel"
                        rec["mp4"] = None
                        print(f"[sweep] {j['id']} ffmpeg burn failed: "
                              f"{e.stderr.decode('utf-8','replace')[-300:]}", flush=True)
                else:
                    rec["status"] = "no-output"
            except Exception as e:
                print(f"[sweep] {j['id']} render failed: {e}", flush=True)
        records.append(rec)
        done += 1
        print(f"[sweep] [{done}/{len(submitted)}] {j['id']} -> {rec['status']}", flush=True)
        write_index(records)  # refresh after each so a morning peek is always current

    json.dump(records, io.open(os.path.join(RESULTS, "manifest.json"), "w", encoding="utf-8"),
              indent=2)
    ok = sum(1 for r in records if r["status"].startswith("ok"))
    print(f"[sweep] DONE — {ok}/{len(records)} rendered. results/ has mp4s + index.html",
          flush=True)


if __name__ == "__main__":
    main()
