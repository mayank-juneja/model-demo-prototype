"""
Wrapper that patches a gradio-client 1.3.0 bug before launching the Gradio app.

Bug: json_schema_to_python_type() crashes when schema is a bool (e.g. additionalProperties: true).
Fix: wrap the top-level function to swallow parse errors and return "Any".
"""
import gradio_client.utils as _gc_utils

_orig = _gc_utils.json_schema_to_python_type


def _patched(schema, defs=None):
    try:
        return _orig(schema, defs)
    except Exception:
        return "Any"


_gc_utils.json_schema_to_python_type = _patched

# Also patch on gradio.blocks which imports it separately
try:
    import gradio.blocks as _gb
    import gradio_client.utils as _cu
    _cu.json_schema_to_python_type = _patched
except Exception:
    pass

from creditmemo_gradioapp import demo  # noqa: E402

if __name__ == "__main__":
    import sys
    share = "--share" in sys.argv
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False, share=share)
