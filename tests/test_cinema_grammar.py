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
