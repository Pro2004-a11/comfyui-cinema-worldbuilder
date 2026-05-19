"""Cinema Worldbuilder — ComfyUI custom-node pack (V3 API)."""
from typing_extensions import override
from comfy_api.latest import ComfyExtension, io

from nodes import CinemaCameraBlock, CinemaAudioLine, CinemaPromptComposer


class CinemaWorldbuilderExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [CinemaCameraBlock, CinemaAudioLine, CinemaPromptComposer]


async def comfy_entrypoint() -> CinemaWorldbuilderExtension:
    return CinemaWorldbuilderExtension()
