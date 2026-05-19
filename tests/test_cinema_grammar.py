import pytest

import cinema_grammar as cg


def test_mode_data_integrity():
    assert len(cg.MODE_CHOICES) == 5
    for label in cg.MODE_CHOICES:
        assert label in cg.MODE_LABEL_TO_KEY
        key = cg.MODE_LABEL_TO_KEY[label]
        assert key in cg.MODES
    for key, mode in cg.MODES.items():
        for field in ("label", "body", "lens_family", "camera_block", "requires"):
            assert field in mode, f"{key} missing {field}"


def test_frame_bounds():
    assert cg.MIN_FRAMES == 9
    assert cg.MAX_FRAMES == 97
    assert (cg.MAX_FRAMES - 1) % 8 == 0


def test_snap_frames_typical():
    frames, runtime = cg.snap_frames(4.0, 24)
    assert frames == 97
    assert abs(runtime - 97 / 24) < 1e-6


def test_snap_frames_clamps_high():
    frames, _ = cg.snap_frames(15.0, 24)
    assert frames == 97  # clamped to MAX_FRAMES


def test_snap_frames_clamps_low():
    frames, _ = cg.snap_frames(0.5, 24)
    assert frames == 9  # clamped to MIN_FRAMES


def test_snap_frames_is_always_8k_plus_1():
    for sec in (0.5, 1.0, 2.5, 3.0, 4.0):
        frames, _ = cg.snap_frames(sec, 24)
        assert (frames - 1) % 8 == 0


def test_parse_mode_label_valid():
    assert cg.parse_mode_label("M3 - Action") == "M3"
    assert cg.parse_mode_label("M1 - Narrative") == "M1"


def test_parse_mode_label_bad():
    with pytest.raises(ValueError, match="unknown mode label"):
        cg.parse_mode_label("M9 - Nonsense")


def test_build_camera_block_m1():
    block = cg.build_camera_block("M1", "55", 4.04, "", "")
    assert "55mm" in block
    assert "roughly 4.0 seconds" in block
    assert "ARRI Alexa 35" in block


def test_build_camera_block_m3_uses_palette():
    block = cg.build_camera_block("M3", "40", 3.0, "stormy desaturated palette", "")
    assert "stormy desaturated palette" in block


def test_build_camera_block_m3_default_palette(capsys):
    block = cg.build_camera_block("M3", "40", 3.0, "", "")
    assert cg.PALETTE_DEFAULT in block
    assert "[WARN]" in capsys.readouterr().out


def test_build_camera_block_m4_default_stage(capsys):
    block = cg.build_camera_block("M4", "55", 3.0, "", "")
    assert cg.STAGE_LIGHTING_DEFAULT in block
    assert "[WARN]" in capsys.readouterr().out


def test_build_camera_block_bad_mode():
    with pytest.raises(ValueError, match="unknown mode"):
        cg.build_camera_block("M9", "55", 3.0, "", "")


def test_build_audio_line_clean():
    line = cg.build_audio_line("boots on gravel\nrain hiss, distant thunder", False)
    assert line.startswith("Audio: diegetic only - ")
    assert "boots on gravel" in line
    assert "rain hiss" in line
    assert "no music" in line
    assert "no dialogue except what is physically spoken in frame" in line


def test_build_audio_line_spoken_dialogue():
    line = cg.build_audio_line("footsteps", True)
    assert "dialogue limited to what is physically spoken in frame" in line


def test_build_audio_line_rejects_music():
    with pytest.raises(ValueError, match="orchestral"):
        cg.build_audio_line("footsteps, orchestral swell, wind", False)


def test_build_audio_line_rejects_padded_banned_token():
    with pytest.raises(ValueError, match="music"):
        cg.build_audio_line("footsteps\n   music   \nwind", False)


def test_compose_prompt_full():
    out = cg.compose_prompt(
        "tense, observational",
        "she steps off the curb",
        "rose-pink haired woman in a white tank",
        "Shot on ARRI Alexa 35 ...",
        "Audio: diegetic only - rain, no music, no dialogue ...",
    )
    assert out.index("Style & Mood:") < out.index("Dynamic Description:")
    assert out.index("Dynamic Description:") < out.index("Static Description:")
    assert "\n" not in out
    assert "**" not in out


def test_compose_prompt_drops_blank_label():
    out = cg.compose_prompt("", "action here", "static here", "CAM", "")
    assert "Style & Mood:" not in out
    assert "Dynamic Description: action here" in out


def test_compose_prompt_omits_blank_audio():
    out = cg.compose_prompt("mood", "dyn", "stat", "CAM", "")
    assert out.rstrip().endswith("CAM")
