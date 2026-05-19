"""Cinema Worldbuilder grammar — pure data and pure functions. No ComfyUI import."""

MAX_FRAMES = 97   # 8*12+1 — LTX 2.3 single-latent ceiling on a 12 GB RTX 4070 Ti
MIN_FRAMES = 9    # 8*1+1

FPS_CHOICES = ["24", "25", "30"]

LENS_CHOICES = ["32", "35", "40", "50", "55", "75", "85", "100"]

PALETTE_DEFAULT = "neutral desaturated grade (default - no palette specified)"
STAGE_LIGHTING_DEFAULT = "neutral white stage wash (default - no stage lighting specified)"

AUDIO_BANNED = [
    "music", "song", "lyric", "soundtrack", "score", "melody",
    "beat drop", "orchestral", "synth pad", "vocals",
]
AUDIO_TEMPLATE = "Audio: diegetic only - {sounds}, no music, {dialogue_clause}."

# Canonical camera blocks transcribed verbatim from cinema-worldbuilder/SKILL.md,
# with [XX]->{lens}/{runtime}, [palette descriptor]->{palette},
# [stage-lighting...]->{stage_lighting}.
MODES = {
    "M1": {
        "label": "M1 - Narrative",
        "body": "ARRI Alexa 35",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": [],
        "camera_block": (
            "Shot on ARRI Alexa 35 in ProRes 4444 LogC4, Panavision Ultra Vintage "
            "2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 filter, "
            "handheld with natural breath and slight shake, photoreal cinematic grit "
            "with oval bokeh and horizontal streak flares, warm anamorphic falloff "
            "toward frame edges, Kodak Vision3 250D film emulation grade with slight "
            "halation on highlights and 800 ASA grain structure, teal-amber color "
            "split with cool teal-blue shadows and warm amber highlights, organic "
            "lens breathing on focus racks, shallow depth of field, 24fps base "
            "shutter 180 degrees, total runtime roughly {runtime} seconds."
        ),
    },
    "M2": {
        "label": "M2 - Studio",
        "body": "ARRI Alexa Mini LF",
        "lens_family": "Cooke S4/i spherical",
        "requires": [],
        "camera_block": (
            "Shot on ARRI Alexa Mini LF in ProRes 4444 LogC4, Cooke S4/i spherical "
            "prime {lens}mm at T2 with Tiffen Black Pro-Mist 1/2 filter, locked-off "
            "tripod with optional 4-to-6 inch slow push-in, photoreal editorial "
            "fashion film aesthetic with gentle halation bloom on highlights and "
            "soft warm falloff in the Cooke signature, fine 400 ASA film grain "
            "structure retaining warmth in the shadows, highlights allowed to bloom "
            "slightly around fabric and chrome surfaces, saturated editorial grade "
            "with warm-retained blacks not crushed to pure black, slight skin tone "
            "warmth from the Cooke color rendition, 24fps base shutter 180 degrees, "
            "total runtime roughly {runtime} seconds. Not CGI, not plastic, "
            "shot-on-film analog aesthetic with real-world lens character."
        ),
    },
    "M3": {
        "label": "M3 - Action",
        "body": "ARRI Alexa 35",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": ["palette"],
        "camera_block": (
            "Shot on ARRI Alexa 35 in ProRes 4444 LogC4, Panavision Ultra Vintage "
            "2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 filter, "
            "all camera work is handheld and shaky throughout with constant operator "
            "micro-jitter, reactive movement, and chaotic shake, no stabilized or "
            "locked-off or dolly-smooth shots anywhere, gritty "
            "documentary-meets-sci-fi war film aesthetic with no stylization and "
            "everything grounded in physical realism, Kodak Vision3 250D film "
            "emulation with 800 ASA grain structure, {palette} with dusty "
            "atmospheric haze, slight halation on highlights, 24fps base shutter "
            "180 degrees, total runtime roughly {runtime} seconds."
        ),
    },
    "M4": {
        "label": "M4 - Performance",
        "body": "ARRI Alexa 35",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": ["stage_lighting"],
        "camera_block": (
            "Shot on ARRI Alexa 35 in ProRes 4444 LogC4, Panavision Ultra Vintage "
            "2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 filter, "
            "mixed handheld pit-photographer energy with rapid handhelds and shaky "
            "low-angle operator work and orbital handheld passes around the "
            "performers, hard cuts between angles, no stabilized or locked-off "
            "shots, photoreal concert documentary aesthetic, Kodak Vision3 250D "
            "film emulation with fine grain structure overlaid throughout, slightly "
            "desaturated cool tones with warm highlight bloom and deep blacks "
            "holding shadow detail, {stage_lighting}, heavy volumetric haze with "
            "dust suspended in every beam, real sweat sheen on skin and real fabric "
            "darkening from exertion, gentle halation on light sources, 24fps base "
            "shutter 180 degrees, total runtime roughly {runtime} seconds."
        ),
    },
    "M5": {
        "label": "M5 - Atmospheric",
        "body": "ARRI Alexa Mini LF",
        "lens_family": "Panavision Ultra Vintage anamorphic",
        "requires": ["palette"],
        "camera_block": (
            "Shot on ARRI Alexa Mini LF in ProRes 4444 LogC4, Panavision Ultra "
            "Vintage 2x anamorphic {lens}mm at T2.3 with Tiffen Black Pro-Mist 1/4 "
            "filter, locked-off or extremely slow push-in motion only, no handheld "
            "energy, photoreal atmospheric environment plate aesthetic, Kodak "
            "Vision3 250D film emulation with fine 400 ASA grain structure, "
            "palette-driven grade with {palette}, strong negative space, deep depth "
            "of field, light atmospheric haze with dust particles suspended in air, "
            "weathered material detail with oxidized metal and dust-covered glass "
            "and cracked paint and moisture stains, slight anamorphic flares on any "
            "directional light sources, 24fps base shutter 180 degrees, total "
            "runtime roughly {runtime} seconds. No humans, no silhouettes, no "
            "living beings - the environment is the subject."
        ),
    },
}

MODE_CHOICES = [MODES[k]["label"] for k in ("M1", "M2", "M3", "M4", "M5")]
MODE_LABEL_TO_KEY = {MODES[k]["label"]: k for k in MODES}


def snap_frames(runtime_seconds, fps):
    """Snap a requested runtime to a valid LTX 2.3 latent length (8k+1).

    EmptyLTXVLatentVideo.length has the live constraint min=1, step=8.
    Rounds to the NEAREST valid value, so runtime_actual may differ from the
    request by up to ~0.33 s at 24 fps. Returns (frame_count, runtime_actual).
    """
    raw = runtime_seconds * fps
    k = round((raw - 1) / 8)
    frames = max(MIN_FRAMES, min(8 * k + 1, MAX_FRAMES))
    runtime_actual = frames / fps
    return frames, runtime_actual


def parse_mode_label(label):
    """Map a MODE_CHOICES display label to its M1..M5 key."""
    try:
        return MODE_LABEL_TO_KEY[label]
    except KeyError:
        raise ValueError(f"unknown mode label: {label}") from None


def build_camera_block(mode_key, lens_mm, runtime_actual, palette, stage_lighting):
    """Fill the chosen mode's canonical camera block.

    Required fields per mode are listed in MODES[key]["requires"]. A blank
    required field falls back to a named default and prints a [WARN] line so the
    degraded behavior is visible. Placeholders not present in a block are ignored
    by str.format.
    """
    mode = MODES.get(mode_key)
    if mode is None:
        raise ValueError(f"unknown mode: {mode_key}")

    palette = palette.strip()
    stage_lighting = stage_lighting.strip()

    if "palette" in mode["requires"] and not palette:
        print(f"[WARN] cinema-worldbuilder: mode {mode_key} has no palette; "
              f"using default")
        palette = PALETTE_DEFAULT
    if "stage_lighting" in mode["requires"] and not stage_lighting:
        print(f"[WARN] cinema-worldbuilder: mode {mode_key} has no stage_lighting; "
              f"using default")
        stage_lighting = STAGE_LIGHTING_DEFAULT

    return mode["camera_block"].format(
        lens=lens_mm,
        runtime=f"{runtime_actual:.1f}",
        palette=palette,
        stage_lighting=stage_lighting,
    )


def build_audio_line(sounds, spoken_dialogue):
    """Assemble the diegetic audio line. Raises ValueError if a banned (music)
    token appears in any cleaned sound entry."""
    items = [s.strip() for part in sounds.splitlines()
             for s in part.split(",")]
    items = [s for s in items if s]
    joined = ", ".join(items)
    haystack = joined.lower()
    for banned in AUDIO_BANNED:
        if banned in haystack:
            raise ValueError(
                f"banned audio token '{banned}' - the audio line is diegetic "
                f"only, no music/score/lyrics"
            )
    dialogue_clause = (
        "dialogue limited to what is physically spoken in frame"
        if spoken_dialogue
        else "no dialogue except what is physically spoken in frame"
    )
    return AUDIO_TEMPLATE.format(sounds=joined, dialogue_clause=dialogue_clause)


def _collapse(text):
    """Collapse whitespace/newlines in a free-text field to single spaces."""
    return " ".join(text.split())


def compose_prompt(style_and_mood, dynamic_description, static_description,
                   camera_block, audio_line=""):
    """Assemble the single continuous-paragraph prompt. Blank labelled prose
    sections are dropped entirely; a blank audio_line is omitted."""
    parts = []
    for label, value in (
        ("Style & Mood", style_and_mood),
        ("Dynamic Description", dynamic_description),
        ("Static Description", static_description),
    ):
        value = _collapse(value)
        if value:
            parts.append(f"{label}: {value}")
    camera_block = _collapse(camera_block)
    if camera_block:
        parts.append(camera_block)
    audio_line = _collapse(audio_line)
    if audio_line:
        parts.append(audio_line)
    return " ".join(parts)
