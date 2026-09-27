# HCS MovieForge

**Local-First AI Filmmaking Workstation**

HCS MovieForge is an autonomous, local-first filmmaking workstation designed to transform ideas into complete, editable film productions. It unifies modern open-weights generative models with deterministic 3D authoring in Blender, centralized memory scheduling, durable job queues, and immutable cryptographic artifact tracking.

---

## 1. Product Capabilities & Workflow

MovieForge automates the complete cinematic production pipeline while ensuring that every asset and scene remains directly editable by humans:

```text
Idea / Script
  │
  ├── Story & Dialogue (Qwen3-VL-8B via llama.cpp)
  │
  ├── Character & Prop Visuals (Bonsai FLUX.2 Klein Q2_K via stable-diffusion.cpp)
  │
  ├── Background Removal & Image-to-3D (TRELLIS.2 Q4 via trellis.cpp)
  │
  ├── 3D Scene Assembly & Rigging (Blender headless, Rigify gate)
  │
  ├── Speech & Voiceover (Whisper.cpp STT, Piper TTS lane)
  │   └── CosyVoice / ACE-Step: EXPERIMENTAL, unstaged (see integrations/*/STATUS.md)
  │
  └── Assembly, VSE Timeline & Master Encode (Blender VSE + FFmpeg 1080p)
```

---

## 2. Hardware Targets & Status

| Target Profile | Environment | Status | Tested Hardware / Profile |
| :--- | :--- | :--- | :--- |
| **Primary Local** | Windows 11 x64 + AMD iGPU (Vulkan) | **VERIFIED LOCAL CORE** | AMD Ryzen 7 7735HS, Radeon 680M (Vulkan 1.4.315), 20GB RAM, `doctor` 16/16 READY, `pytest` 51 passed (2026-09-27) |
| **Secondary Local** | WSL2 Ubuntu + Vulkan | **VERIFIED LOCAL CORE** | Ubuntu (kernel WSL2), Vulkan API 1.3, Blender 5.0.1, `doctor` 16/16 READY, `pytest` 46 unit + 5 integration passed (2026-09-27) |
| **Public Demo** | Hugging Face Space (Gradio) | **LIVE DEMO ADAPTER** | https://huggingface.co/spaces/timfromhcs/HCS-MovieForge (status + storyboard sample, synced from `apps/space-demo` via CI) |

---

## 3. Backend Capability Matrix

All statuses represent genuine local verification records, not assumptions:

| Backend | Component | Role | Local Verification Status |
| :--- | :--- | :--- | :--- |
| **CLI & Doctor** | `apps/cli` | Diagnostics & Management | **VERIFIED LOCAL** (Win 16/16 + WSL 16/16 checks READY) |
| **Process Supervisor** | `engine/supervisor` | Process tree & PID tracker | **VERIFIED LOCAL** (`start.ps1 -Daemon` → tracked PID → `stop.ps1` clean kill, live-tested) |
| **Job Scheduler** | `engine/scheduler` | WAL queue, Locality-aware | **VERIFIED LOCAL** |
| **Model Registry** | `engine/model_manager` | Portable lock paths (Win/Linux) | **VERIFIED LOCAL** (relative POSIX lock paths, cross-OS unit tests) |
| **Blender Engine** | Blender 5.1.2 (Win) / 5.0.1 (WSL) Headless | 3D authoring, Rigify, VSE | **VERIFIED LOCAL** (headless script PASS) |
| **FFmpegFinalizer** | FFmpeg + ffprobe | 1080p Encoding & stream QA | **VERIFIED LOCAL** (1080p stream QA PASS) |
| **Bonsai Image** | `stable-diffusion.cpp` | FLUX.2 Klein Q2_K GGUF | **UPSTREAM PINNED** (Sha: `8a0fb8cc`, real 195s Vulkan PNG) |
| **TRELLIS 3D** | `trellis.cpp` | TRELLIS.2 Q4 GGUF to GLB | **UPSTREAM PINNED** (ilintar/trellis2-gguf, real 415s GLB) |
| **Multimodal Agent**| `llama.cpp` | Qwen3-VL 8B Instruct Q4_K_M | **UPSTREAM PINNED** (Sha: `f982a075`) |
| **Speech-to-Text** | `whisper.cpp` | Voice commands & dialogue STT | **UPSTREAM PINNED** (ggml-base, real transcript PASS) |
| **TTS Lane** | `piper` 1.8.0 | Dialogue voiceover (CPU) | **VERIFIED LOCAL** (real WAV PASS, Win + WSL) |
| **Space Demo** | `apps/space-demo` | Public Gradio adapter | **LIVE** (import-verified locally, deployed via `space-sync.yml` + `HF_TOKEN` secret) |

---

## 4. Installation & First Run

### Prerequisites
- Windows 11 64-bit or Linux x86_64 (or WSL2 Ubuntu)
- Python 3.12+ (3.14 on tested machines)
- Git, CMake, Ninja
- Blender 5.x (5.1.2 Win / 5.0.1 WSL tested) or 4.5+ LTS
- FFmpeg 6.0+ (9.x Win / 8.x WSL tested)

### Step-by-Step Setup

1. **Verify your local toolchains:**
   ```powershell
   python apps/cli/src/main.py doctor
   ```

2. **Benchmark your hardware and safe UMA memory allocation:**
   ```powershell
   python apps/cli/src/main.py benchmark
   ```

3. **Inspect the registered AI model manifests:**
   ```powershell
   python apps/cli/src/main.py models list
   ```

4. **Run the full test suite:**
   ```powershell
   python -m pytest tests/unit tests/integration -q
   ```

5. **Start the workstation supervisor:**
   - On Windows: Run `start.bat` or `pwsh -File start.ps1` (`-Daemon` for background)
   - On Linux: Run `./start.sh`

6. **Stop the workstation gracefully:**
   - On Windows: Run `stop.bat` or `pwsh -File stop.ps1`
   - On Linux: Run `./stop.sh`

### WSL2 Quick Path (tested 2026-09-27)

```bash
sudo apt-get install -y ffmpeg blender cmake ninja-build nodejs
pip3 install --user --break-system-packages pydantic click huggingface_hub pillow psutil rich python-dotenv httpx fastapi uvicorn websockets pytest piper-tts
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
sudo ln -sf $HOME/.cargo/bin/{cargo,rustc,rustup} /usr/local/bin/
cd /mnt/e/AiMovieMaker && python3 apps/cli/src/main.py doctor
```

---

## 5. Security & Privacy

- **Local-First**: All projects, assets, renders, and databases remain strictly local in the `projects/` directory.
- **Zero Secret Commits**: Sensitive credentials (GitHub tokens, Hugging Face tokens) are isolated in `.env` (gitignored) or OS keyrings and are strictly forbidden from version control. CI uses the `HF_TOKEN` repository secret; it never appears in code or logs.
- **Cryptographic Provenance**: Every output file is registered as an immutable artifact with SHA256 checksums in SQLite WAL databases.

---

## 6. Known Limitations (honest, 2026-09-27)

- **Desktop UI**: Tauri skeleton only (`apps/desktop/src/` empty) — the workstation is headless-first (CLI + API + WS). No screenshots yet because there is no app window to screenshot.
- **TTS/Music**: Piper is the verified voice lane. CosyVoice (CPU-only route, Vulkan NOT working upstream) and ACE-Step (build + multi-GB staging pending) are `EXPERIMENTAL` — see `integrations/cosyvoice/STATUS.md` and `integrations/acestep/STATUS.md`. `music.generate` honestly returns `UNAVAILABLE`.
- **Rigging**: The Blender Rigify gate honestly blocks non-humanoid TRELLIS blobs (`BLOCKED_NON_HUMANOID`, no fake rigs). Full humanoid generate/bind awaits a licensed humanoid fixture.
- **Stress/Soak**: Suites E/F/G/H/C/D + 60s soak pass. 50-cycle churn (A), intentional memory pressure (B), and multi-hour soak are pending real GPU-time runs.
- **Mini-film**: A 3.5s 1080p proof (`qa.movie passed=true`) exists; the full §73 film (2 chars, 6 shots, 20–60s) is implemented as `produce --full` and awaits its overnight GPU run.

---

## 7. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
