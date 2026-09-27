"""Validates health and capabilities across all integrated workers."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
root = Path(__file__).resolve().parent.parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from integrations.blender.worker import BlenderWorker  # noqa: E402
from integrations.llama_cpp.worker import LlamaWorker  # noqa: E402
from integrations.stable_diffusion_cpp.worker import StableDiffusionWorker  # noqa: E402
from integrations.trellis_cpp.worker import TrellisWorker  # noqa: E402
from integrations.whisper_cpp.worker import WhisperWorker  # noqa: E402

workers = [
    BlenderWorker(),
    WhisperWorker(),
    TrellisWorker(),
    StableDiffusionWorker(),
    LlamaWorker(),
]

print("========================================")
print("     Worker Health & Capability Audit   ")
print("========================================")

all_ok = True
for w in workers:
    h = w.health()
    c = w.capabilities()
    status = h.get("status")
    icon = "[OK]  " if status == "ok" else "[FAIL]"
    print(f"{icon} {w.backend_name:<22}: status={status} | compute={c.compute_device} | tasks={c.supported_tasks}")
    if status != "ok":
        all_ok = False

if not all_ok:
    sys.exit(1)
print("All 5 workers report healthy and operational.")
