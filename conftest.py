# Keeps pytest from trying to import the project's V3 entry point (`__init__.py`
# does `from comfy_api.latest import …` which only resolves inside ComfyUI).
collect_ignore = ["__init__.py", "nodes.py"]
