# CosyVoice integration status — EXPERIMENTAL (CPU-only route)

Date: 2026-09-27. Verified against current upstream (not from memory).

- Official CosyVoice (FunAudioLLM/CosyVoice): Python inference, CUDA/docker/vLLM deployment.
  No official Windows/Vulkan/GGUF path.
- Community native runtime `cosyvoice.cpp` (Lourdle, MIT): Windows x64 / Linux / macOS builds,
  GGUF models (e.g. `Lourdle/Fun-CosyVoice3-0.5B-2512-GGUF`, Apache-2.0 weights).
  Backend test status per upstream README: CPU working, CUDA working, Metal working,
  SYCL working — **Vulkan currently NOT working**.
- Consequence for the AMD iGPU/Vulkan primary target: only a CPU-only CosyVoice route is
  realistic today. GEMINI.md §3.6 accepts CPU-only for voice, with centralized scheduling.
- Active verified TTS remains **Piper** (`voice_piper_en_lessac_medium`, harness PASS 6.56s),
  explicitly declared as the supported compatibility lane (no silent fallback, §113).
- Integration route (not yet executed): vendor `cosyvoice-cli` CPU build + GGUF set
  (llm-q4_k + flow-q8_0 + hift-f16 + voices ≈ 745MB), stage under
  `models/tts_cosyvoice3_05b/`, add `integrations/cosyvoice/worker.py` behind the worker
  protocol, certify with `scripts/test/test_cosyvoice.ps1`, then promote.
