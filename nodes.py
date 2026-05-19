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
