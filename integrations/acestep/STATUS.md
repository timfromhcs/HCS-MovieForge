# ACE-Step music integration status — EXPERIMENTAL (route verified, not staged)

Date: 2026-09-27. Verified against current upstream (not from memory).

- Model: ACE-Step 1.5 (ACE Studio / StepFun), open weights. Official Python path needs
  Python 3.11–3.12 + CUDA/ROCm/MPS/CPU; ≤6GB VRAM runs DiT-only turbo with LM disabled.
- Native runtime `acestep.cpp` (ServeurpersoCom, GGML, C++17): builds for CPU/CUDA/ROCm/Metal
  **and Vulkan** (`buildvulkan.cmd` / `buildvulkan.sh`), WebUI on :8085, GGUF weights.
  A Vulkan-capable native path therefore EXISTS upstream for the AMD target.
- Consequence: music is NOT fake-implemented. `music.generate` returns honest UNAVAILABLE
  until the runtime is staged. No placeholder WAVs, no silent success (§0.2).
- Integration route (not yet executed): build `acestep.cpp` Vulkan binaries into
  `bin/acestep-cpp/`, download GGUF set (DiT turbo Q8_0 + VAE BF16 + Qwen3-Embedding 0.6B
  + optional 0.6B LM ≈ several GB), add `integrations/acestep/worker.py` + manifest
  `music_acestep15_turbo_q8.json`, certify DiT-only CPU/Vulkan generation on this host,
  then promote. Multi-GB downloads + C++ build are the evidence-based blockers.
