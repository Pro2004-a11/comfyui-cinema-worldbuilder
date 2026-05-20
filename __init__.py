"""Cinema Worldbuilder — ComfyUI custom-node pack (V3 API).

Importable outside ComfyUI: if `comfy_api` is missing (pytest collection,
documentation tooling, standalone use of cinema_grammar), the V3 registration
is silently skipped. Inside ComfyUI the import succeeds and the pack registers
normally.
"""
try:
    from comfy_api.latest import ComfyExtension, io
except ModuleNotFoundError as _e:
    if _e.name != "comfy_api":
        raise
    # No ComfyUI in this interpreter — leave the V3 entry points unbound.
else:
    from typing_extensions import override
    from .nodes import (
        CinemaCameraBlock,
        CinemaAudioLine,
        CinemaPromptComposer,
    )

    class CinemaWorldbuilderExtension(ComfyExtension):
        @override
        async def get_node_list(self) -> list[type[io.ComfyNode]]:
            return [CinemaCameraBlock, CinemaAudioLine, CinemaPromptComposer]

    async def comfy_entrypoint() -> "CinemaWorldbuilderExtension":
        return CinemaWorldbuilderExtension()
