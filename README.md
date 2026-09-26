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
  ├── 3D Scene Assembly & Rigging (Blender 5.1 / Rigify headless)
  │
  ├── Speech, Voiceover & Music (Whisper.cpp, CosyVoice, ACE-Step)
  │
  └── Assembly, VSE Timeline & Master Encode (Blender VSE + FFmpeg 1080p)
```

---

## 2. Hardware Targets & Status

| Target Profile | Environment | Status | Tested Hardware / Profile |
| :--- | :--- | :--- | :--- |
| **Primary Local** | Windows 11 x64 + AMD iGPU (Vulkan) | **VERIFIED LOCAL CORE** | AMD Ryzen 7 7735HS, Radeon 680M (Vulkan 1.4.315), 20GB RAM (2026-09-27) |
| **Secondary Local** | Linux x86_64 + Vulkan | **PLANNED / SKELETON** | Ubuntu 22.04+ with Vulkan runtime |
| **Public Demo** | Hugging Face Space (Gradio) | **DEMO ADAPTER** | ZeroGPU / Web Demo |

---

## 3. Backend Capability Matrix

All statuses represent genuine local verification records, not assumptions:

| Backend | Component | Role | Local Verification Status |
| :--- | :--- | :--- | :--- |
| **CLI & Doctor** | `apps/cli` | Diagnostics & Management | **VERIFIED LOCAL** (10/10 checks PASS) |
| **Process Supervisor** | `engine/supervisor` | Process tree & PID tracker | **VERIFIED LOCAL** |
| **Job Scheduler** | `engine/scheduler` | WAL queue, Locality-aware | **VERIFIED LOCAL** |
| **Blender Engine** | Blender 5.1.2 Headless | 3D authoring, Rigify, VSE | **VERIFIED LOCAL** (headless script PASS) |
| **FFmpegFinalizer** | FFmpeg 9.0 + ffprobe | 1080p Encoding & stream QA | **VERIFIED LOCAL** (1080p stream QA PASS) |
| **Bonsai Image** | `stable-diffusion.cpp` | FLUX.2 Klein Q2_K GGUF | **UPSTREAM PINNED** (Sha: `8a0fb8cc`) |
| **TRELLIS 3D** | `trellis.cpp` | TRELLIS.2 Q4 GGUF to GLB | **UPSTREAM PINNED** (ilintar/trellis2-gguf) |
| **Multimodal Agent**| `llama.cpp` | Qwen3-VL 8B Instruct Q4_K_M | **UPSTREAM PINNED** (Sha: `f982a075`) |
| **Speech-to-Text** | `whisper.cpp` | Voice commands & dialogue STT | **UPSTREAM PINNED** (ggml-base) |

---

## 4. Installation & First Run

### Prerequisites
- Windows 11 64-bit or Linux x86_64
- Python 3.12+ (or 3.14 on tested machines)
- Git, CMake, Ninja
- Blender 5.1+ or 4.5+ LTS
- FFmpeg 6.0+ / 9.0+

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
   pwsh -File scripts/test/run_all_tests.ps1
   ```

5. **Start the workstation supervisor:**
   - On Windows: Run `start.bat` or `pwsh -File start.ps1`
   - On Linux: Run `./start.sh`

6. **Stop the workstation gracefully:**
   - On Windows: Run `stop.bat` or `pwsh -File stop.ps1`
   - On Linux: Run `./stop.sh`

---

## 5. Security & Privacy

- **Local-First**: All projects, assets, renders, and databases remain strictly local in the `projects/` directory.
- **Zero Secret Commits**: Sensitive credentials (GitHub tokens, Hugging Face tokens) are isolated in `.env` (gitignored) or OS keyrings and are strictly forbidden from version control.
- **Cryptographic Provenance**: Every output file is registered as an immutable artifact with SHA256 checksums in SQLite WAL databases.

---

## 6. License

This project is licensed under the MIT License - see the [LICENSE](file:///E:/AiMovieMaker/LICENSE) file for details.
