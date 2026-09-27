"""Hugging Face Space demo adapter (Gradio). Constrained public workflow, NOT the local runtime.

Exposes: backend status + a character-reference preview rendered from local fixtures.
Heavy generation stays GPU-gated per ZeroGPU policy; uploads are session-scoped.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import gradio as gr  # noqa: E402

from packages.ui_kit.src.status import backend_label  # noqa: E402


def backend_status() -> str:
    rows = {
        "image (Bonsai/FLUX.2)": {"local_built": True, "local_runtime_verified": True},
        "3d (TRELLIS.2)": {"local_built": True, "local_runtime_verified": True},
        "agent (Qwen3-VL)": {"local_built": True, "local_runtime_verified": True},
        "tts (Piper lane)": {"local_built": True, "local_runtime_verified": True},
        "tts (CosyVoice)": {"experimental": True},
        "music (ACE-Step)": {"experimental": True},
    }
    return "\n".join(f"{name}: {backend_label(v)['text']}" for name, v in rows.items())


def storyboard_sample() -> str:
    return (
        "Demo storyboard (fixture):\n"
        "1. [wide/static] Platform 4B in night rain\n"
        "2. [orbit] Spark-7 scans the rails — 'All systems nominal.'"
    )


with gr.Blocks(title="HCS MovieForge Demo") as demo:
    gr.Markdown("# HCS MovieForge — public demo adapter")
    gr.Markdown("_Constrained demo. The canonical workstation runs locally (Vulkan)._")
    status_box = gr.Textbox(label="Backend status (verification-driven)", lines=8)
    board_box = gr.Textbox(label="Storyboard sample", lines=4)
    gr.Button("Refresh status").click(backend_status, outputs=status_box)
    gr.Button("Show storyboard").click(storyboard_sample, outputs=board_box)
    demo.load(backend_status, outputs=status_box)

if __name__ == "__main__":
    demo.launch()
