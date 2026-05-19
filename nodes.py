"""ComfyUI V3 node adapters for the Cinema Worldbuilder grammar."""
from comfy_api.latest import io

import cinema_grammar as cg


class CinemaCameraBlock(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CinemaWorldbuilder_CameraBlock",
            display_name="Cinema Camera Block",
            category="Cinema Worldbuilder",
            description="Mode + lens + runtime -> canonical camera block + LTX frame count.",
            inputs=[
                io.Combo.Input("mode", options=cg.MODE_CHOICES,
                               default=cg.MODE_CHOICES[0]),
                io.Combo.Input("lens_mm", options=cg.LENS_CHOICES, default="50"),
                io.Float.Input("runtime_seconds", default=4.0, min=0.5, max=4.0,
                               step=0.5),
                io.Combo.Input("fps", options=cg.FPS_CHOICES, default="24"),
                io.String.Input("palette", multiline=True, optional=True,
                                default=""),
                io.String.Input("stage_lighting", multiline=True, optional=True,
                                default=""),
            ],
            outputs=[
                io.String.Output("camera_block"),
                io.Int.Output("frame_count"),
                io.Int.Output("fps"),
                io.Float.Output("runtime_actual"),
            ],
        )

    @classmethod
    def execute(cls, mode, lens_mm, runtime_seconds, fps, palette="",
                stage_lighting=""):
        key = cg.parse_mode_label(mode)
        fps_int = int(fps)
        frame_count, runtime_actual = cg.snap_frames(runtime_seconds, fps_int)
        camera_block = cg.build_camera_block(
            key, lens_mm, runtime_actual, palette or "", stage_lighting or "")
        return io.NodeOutput(camera_block, frame_count, fps_int, runtime_actual)


class CinemaAudioLine(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CinemaWorldbuilder_AudioLine",
            display_name="Cinema Audio Line",
            category="Cinema Worldbuilder",
            description="Diegetic-only audio line. Rejects music/score/lyrics.",
            inputs=[
                io.String.Input("sounds", multiline=True, default=""),
                io.Boolean.Input("spoken_dialogue", default=False),
            ],
            outputs=[
                io.String.Output("audio_line"),
            ],
        )

    @classmethod
    def validate_inputs(cls, sounds, spoken_dialogue):
        """Pre-execution guard: fail the graph cleanly if music is referenced."""
        haystack = sounds.lower()
        for banned in cg.AUDIO_BANNED:
            if banned in haystack:
                return (f"Cinema Audio Line: banned token '{banned}' - the audio "
                        f"line is diegetic only, no music/score/lyrics.")
        return True

    @classmethod
    def execute(cls, sounds, spoken_dialogue):
        return io.NodeOutput(cg.build_audio_line(sounds, spoken_dialogue))


class CinemaPromptComposer(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="CinemaWorldbuilder_PromptComposer",
            display_name="Cinema Prompt Composer",
            category="Cinema Worldbuilder",
            description="Assembles the single-paragraph Seedance-style prompt.",
            inputs=[
                io.String.Input("style_and_mood", multiline=True, default=""),
                io.String.Input("dynamic_description", multiline=True, default=""),
                io.String.Input("static_description", multiline=True, default=""),
                io.String.Input("camera_block", force_input=True),
                io.String.Input("audio_line", force_input=True, optional=True),
            ],
            outputs=[
                io.String.Output("prompt"),
            ],
        )

    @classmethod
    def execute(cls, style_and_mood, dynamic_description, static_description,
                camera_block, audio_line=""):
        return io.NodeOutput(cg.compose_prompt(
            style_and_mood, dynamic_description, static_description,
            camera_block, audio_line or ""))
