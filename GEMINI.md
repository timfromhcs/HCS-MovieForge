# HCS MovieForge — Autonomous Build & Verification Contract

**Purpose:** Build a real, local-first, full-fledged AI filmmaking workstation from an empty directory. This file is the operating specification for a Gemini coding agent working autonomously inside the repository.

**Primary local target:** Windows 11 Pro x64, AMD iGPU/Vulkan, approximately 12 GB system RAM and approximately 12 GB shared graphics memory (UMA), no CUDA, primary storage on HDD.

**Secondary target:** Linux x86_64 with Vulkan where the same architecture is supported.

**Public demo target:** Hugging Face Space using Gradio/ZeroGPU as a demo/deployment adapter, not as the canonical local runtime.

**Core image model:** `Aatricks/bonsai-image-ternary-4B-FLUX2-klein-GGUF` Q2_K GGUF through the FLUX.2 Klein path of `stable-diffusion.cpp` + Vulkan.

**Core 3D model/runtime:** `trellis.cpp` / TRELLIS.2 Q4 GGUF with Vulkan on the local target.

**Core multimodal agent:** Qwen3-VL 8B GGUF through `llama.cpp` + Vulkan, with dynamic context/KV/cache policies.

**Core DCC:** Blender 4.5 LTS or another explicitly verified compatible LTS build selected by the implementation after checking the current upstream release/build requirements.

**Important:** This document is a build contract, not permission to invent compatibility. All mutable upstream details MUST be re-checked at implementation time against primary upstream documentation/releases/model cards. Never fabricate a download filename, release version, checksum, CLI option, or claimed backend capability.

---

# 0. NON-NEGOTIABLE AGENT RULES

## 0.1 Never hallucinate

Never state or imply that something is supported until it has been verified by one of:

1. current upstream documentation,
2. current upstream source/release artifact,
3. a real local build/test,
4. an external static/structural checker,
5. a reproducible runtime smoke test.

When evidence is missing, write `UNKNOWN` or `UNVERIFIED`, do not guess.

## 0.2 Never use fake success

The following are prohibited as production implementations:

- mock inference when the feature claims to generate real media,
- fake progress bars,
- dummy output filenames,
- placeholder GLBs pretending to be generated assets,
- fabricated benchmark numbers,
- hard-coded `success=true` responses,
- fake model metadata,
- fake GPU telemetry,
- simulated backend success in E2E tests.

Mocks are allowed only for isolated unit tests of pure orchestration logic and MUST be clearly scoped to the unit-test layer. Every important real backend requires a real integration test.

## 0.3 No skip without an explicit, evidence-based block

Never silently skip a requested implementation phase.

If a dependency is unavailable on the target hardware:

1. record the limitation,
2. identify a real compatible fallback where one exists,
3. implement the fallback or mark the capability as explicitly unsupported,
4. keep the rest of the system operational,
5. include a reproducible verification report.

The agent must never rewrite a failed task as if it succeeded.

## 0.4 Code completion is not feature completion

A feature is COMPLETE only after:

```text
source code
→ static analysis
→ unit tests
→ build
→ real backend smoke/integration test
→ artifact validation
→ UI/API verification
→ failure-path verification
→ documentation update
→ regression suite
```

## 0.5 Human edits are authoritative

Never silently overwrite user-authored assets or project state.

Use versioned artifacts and reversible mutations.

## 0.6 The project must remain useful without AI autonomy

Every major production object must be manually editable:

- story,
- characters,
- references,
- images,
- masks,
- 3D assets,
- rigs,
- motion,
- camera,
- lights,
- effects,
- dialogue,
- audio,
- timeline,
- rendering settings.

The master agent automates the production stack; it does not replace the underlying editable production state.

## 0.7 Never claim perfect/green without evidence

The terms `GREEN`, `STABLE`, `RELEASE`, `PRODUCTION`, `VERIFIED`, and `COMPATIBLE` have strict meanings in this project and may be used only when the corresponding acceptance gates are satisfied.

---

# 1. PRODUCT DEFINITION

HCS MovieForge is a local-first AI film-production workstation.

It must support this complete workflow:

```text
idea
→ story
→ screenplay
→ storyboard
→ character design
→ prop design
→ location design
→ image generation/editing
→ background removal
→ image-to-3D
→ mesh validation
→ retopology
→ materials/UV
→ Blender import
→ character rigging
→ facial rig
→ AI-assisted motion
→ mocap/pose retargeting
→ camera design
→ lighting design
→ FX
→ dialogue writing
→ STT
→ TTS/voiceover
→ lip sync
→ music
→ SFX/ambience
→ shot assembly
→ edit/cut
→ compositing
→ QA
→ repair
→ 1920×1080 final render
→ encoded master
```

Video-generation models are optional extensions. The canonical movie path MUST remain functional as a 3D/Blender-driven production pipeline.

---

# 2. ARCHITECTURE PRINCIPLE

Use one product with multiple specialized backends and one authoritative project state.

```text
                    HCS MOVIEFORGE
                           │
         ┌─────────────────┼───────────────────┐
         │                 │                   │
        UI              MASTER AGENT      PROJECT STATE
   React/TypeScript      Qwen3-VL           SQLite
   Tauri desktop        tool-calling        WAL + events
         │                 │                   │
         └─────────────────┼───────────────────┘
                           │
                     CONTROL PLANE
                  API + WebSocket + CLI
                           │
              ┌────────────┴────────────┐
              │                         │
           SCHEDULER               RESOURCE MANAGER
              │                         │
      ┌───────┼────────┬───────┐        │
      │       │        │       │        │
    IMAGE     3D    BLENDER   AUDIO   RENDER/QA
      │       │        │       │        │
   Bonsai   TRELLIS  Blender  Whisper  FFmpeg
   FLUX2      Q4     Rigify   CosyVoice VLM
   Vulkan   Vulkan    EEVEE   ACE-Step
```

---

# 3. CANONICAL BACKEND STACK

## 3.1 Image

Primary:

```text
Aatricks/bonsai-image-ternary-4B-FLUX2-klein-GGUF
Q2_K GGUF
```

Runtime:

```text
stable-diffusion.cpp
GGML Vulkan
FLUX.2 Klein execution path
```

Required companion components are pinned by model-manifest revision, not by assumptions. The agent must inspect the current upstream FLUX.2 Klein integration and download only the components actually required by the selected stable-diffusion.cpp commit/build.

Current upstream stable-diffusion.cpp documentation describes a FLUX.2 Klein path with a diffusion model, VAE, and Qwen3 text encoder, and documents CPU offloading and diffusion flash attention for low-memory operation. Re-check the exact filenames and flags at build time. [Upstream: https://github.com/leejet/stable-diffusion.cpp/tree/master/docs]

## 3.2 3D

Primary:

```text
trellis.cpp
TRELLIS.2 Q4 GGUF
Vulkan
```

The current upstream trellis.cpp project provides native C++/GGML TRELLIS.2, Windows/Linux Vulkan builds, GGUF weights, image→textured GLB, background-removal support, retopology, and a resident HTTP server. Re-check exact release assets and command-line flags before use. [Upstream: https://github.com/pwilkin/trellis.cpp]

The agent must treat the current known AMD Vulkan issues in trellis.cpp as an explicit compatibility risk and must certify the target device through real smoke and stress tests before declaring the 3D backend production-ready. [Example upstream issue: https://github.com/pwilkin/trellis.cpp/issues]

## 3.3 Agent/VLM

Primary:

```text
Qwen3-VL-8B GGUF
llama.cpp
Vulkan
```

Use Q4_K_M initially unless a benchmark proves another format is better.

The exact context size, GPU layers, KV cache types, and multimodal projector format MUST be benchmark-calibrated on the target machine.

Current llama.cpp supports mmap/lazy model loading, KV-cache quantization, Flash Attention, and Vulkan. Re-check current CLI flags against the checked-out revision. [Upstream: https://github.com/ggml-org/llama.cpp]

## 3.4 3D authoring

```text
Blender LTS
EEVEE
Rigify
Python API
Video Sequencer
Compositor
```

The implementation must detect and pin the exact Blender LTS version used for a release. Do not silently switch versions during a release.

## 3.5 Speech-to-text

```text
whisper.cpp
Vulkan where supported by the checked-out build
```

## 3.6 TTS / voice

Primary small local candidate:

```text
CosyVoice 3 0.5B
```

Use a GGUF/native runtime where a real supported path exists. If the available local runtime is CPU-only, that is acceptable; resource scheduling remains centralized.

## 3.7 Music

Primary candidate:

```text
ACE-Step 1.5
acestep.cpp or the current verified native local runtime
```

The agent must verify current Windows/Vulkan/quantized support before enabling it as a release worker.

## 3.8 Editing and delivery

```text
Blender VSE
FFmpeg
```

Final target:

```text
1920×1080
progressive
exact project FPS
stereo or project-defined multichannel audio
```

---

# 4. REPOSITORY LAYOUT

Build this structure from the empty directory. Adapt names only if necessary; do not collapse the architecture into one monolithic script.

```text
HCS-MovieForge/
├── GEMINI.md
├── LICENSE
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── pyproject.toml
├── package.json
├── Cargo.toml
├── CMakeLists.txt
├── .gitignore
├── .gitattributes
├── .editorconfig
│
├── apps/
│   ├── desktop/
│   │   ├── src/
│   │   ├── src-tauri/
│   │   └── package.json
│   ├── api/
│   ├── cli/
│   └── space-demo/
│
├── packages/
│   ├── contracts/
│   ├── project-format/
│   ├── validators/
│   ├── ui-kit/
│   └── telemetry/
│
├── engine/
│   ├── supervisor/
│   ├── scheduler/
│   ├── resource_manager/
│   ├── model_manager/
│   ├── artifact_manager/
│   ├── project_manager/
│   ├── cache_manager/
│   ├── recovery/
│   └── workers/
│
├── agent/
│   ├── director/
│   ├── planners/
│   ├── subagents/
│   ├── tools/
│   ├── memory/
│   ├── prompts/
│   └── policies/
│
├── integrations/
│   ├── stable-diffusion-cpp/
│   ├── trellis-cpp/
│   ├── llama-cpp/
│   ├── blender/
│   ├── whisper-cpp/
│   ├── cosyvoice/
│   └── acestep/
│
├── models/
│   ├── manifests/
│   ├── locks/
│   └── README.md
│
├── projects/
│   └── .gitkeep
│
├── scripts/
│   ├── bootstrap/
│   ├── models/
│   ├── build/
│   ├── test/
│   ├── release/
│   └── recovery/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── golden/
│   ├── stress/
│   ├── soak/
│   ├── fixtures/
│   └── external/
│
├── docs/
│   ├── architecture/
│   ├── user-guide/
│   ├── development/
│   ├── backend-matrices/
│   └── release-notes/
│
├── runtime/
├── cache/
├── logs/
└── dist/
```

`models/`, `cache/`, `projects/`, `runtime/`, `logs/`, and generated media are local runtime data and MUST NOT be committed unless a tiny explicit fixture is required.

---

# 5. BOOTSTRAP FROM AN EMPTY FOLDER

The agent starts in an empty directory.

First actions:

1. inspect OS, architecture, shell, Git, Python, Node, Rust, CMake/Ninja, Vulkan, Blender availability, FFmpeg availability;
2. create repository skeleton;
3. initialize Git;
4. create Python virtual environment;
5. create Node workspace;
6. create Rust/Tauri skeleton;
7. create backend integration directories;
8. create model manifests;
9. create test harness;
10. create developer scripts;
11. write the first README before implementing large features;
12. commit baseline.

Do not download large models before the model manifest and verification system exist.

---

# 6. HEADLESS-FIRST POLICY

Every backend must have:

```text
CLI or headless entrypoint
structured JSON result
structured logs
exit code semantics
artifact path
artifact SHA256
resource telemetry
```

The UI is built on top of headless interfaces. Never make the UI the only way to exercise a backend.

Required examples:

```text
movieforge doctor
movieforge models sync
movieforge models verify
movieforge models list
movieforge benchmark
movieforge test smoke
movieforge test integration
movieforge test stress
movieforge test soak
movieforge project create
movieforge project open
movieforge project save
movieforge project export
movieforge render preview
movieforge render final
movieforge server start
movieforge server stop
movieforge release verify
```

---

# 7. START / STOP CONTRACT

Provide:

```text
start.bat
stop.bat
start.ps1
stop.ps1
start.sh
stop.sh
```

Windows `start.bat` must launch the supervisor, API, UI and enabled local workers through one controlled process tree.

Windows `stop.bat` must request graceful shutdown, wait for children, then force-kill only remaining MovieForge child processes if necessary.

Linux scripts must provide the same semantics through PID/state files.

Never blindly kill unrelated processes by generic names such as every `python.exe` or every `blender.exe` on the system.

The supervisor must write:

```text
runtime/supervisor.pid
runtime/service-state.json
```

and track child process IDs it actually launched.

---

# 8. PROCESS SUPERVISOR

Implement a supervisor with:

- service manifest,
- health checks,
- heartbeats,
- restart policies,
- exponential backoff,
- max restart rate,
- graceful shutdown,
- orphan detection,
- log routing,
- state persistence.

Service states:

```text
STARTING
READY
BUSY
DEGRADED
STOPPING
STOPPED
CRASHED
RECOVERING
DISABLED
```

A crashed worker must not automatically crash the control plane.

---

# 9. DURABLE JOB SYSTEM

Use SQLite WAL for durable job state.

Job states:

```text
CREATED
QUEUED
WAITING_RESOURCE
PREPARING
PRELOADING
RUNNING
VALIDATING
COMMITTING
SUCCEEDED
FAILED_RETRYABLE
FAILED_FINAL
CANCEL_REQUESTED
CANCELLED
ORPHANED
RECOVERING
```

Every job stores:

- job ID,
- project ID,
- type,
- model ID,
- model revision,
- input artifact IDs,
- input hashes,
- recipe fingerprint,
- priority,
- retry count,
- resource estimate,
- timestamps,
- parent job,
- child jobs,
- worker ID,
- output artifact IDs,
- final status,
- structured error.

---

# 10. ARTIFACT SYSTEM

Every real output is an artifact.

Artifact record:

```text
artifact_id
project_id
kind
path
relative_path
size
sha256
mime
created_at
producer
producer_version
model_id
model_revision
source_artifacts
recipe_fingerprint
qa_status
canonical
```

Artifacts are immutable.

Changes create new versions.

The filesystem is the payload store; SQLite stores metadata and relationships.

---

# 11. PROJECT FORMAT

A project must be portable.

Minimum project root:

```text
project.toml
manifest.json
movieforge.db
story/
characters/
locations/
props/
scenes/
shots/
storyboards/
motion/
camera/
lighting/
fx/
audio/
renders/
exports/
logs/
.movieforge/
```

`.movieforge/` contains:

```text
events/
snapshots/
recovery/
locks/
trash/
```

The project database must use WAL mode, transactional migrations, integrity checks, and recovery metadata.

---

# 12. AUTOSAVE AND RECOVERY

Save project state on every durable mutation.

Also create periodic snapshots after activity, before high-risk operations, and after large completed jobs.

Recommended pattern:

```text
user mutation
→ transaction
→ event
→ commit
→ autosave snapshot scheduling
```

On startup:

```text
load project
→ integrity_check
→ discover incomplete jobs
→ discover stale leases
→ quarantine partial artifacts
→ replay events if required
→ restore UI state
→ resume queue
```

Never treat a partially written file as a valid artifact.

---

# 13. MODEL REGISTRY

Create machine-readable manifests for every model.

Example fields:

```json
{
  "id": "image.bonsai.flux2-klein.q2k",
  "source": {
    "type": "huggingface",
    "repo": "Aatricks/bonsai-image-ternary-4B-FLUX2-klein-GGUF",
    "revision": "PINNED_AT_INSTALL"
  },
  "files": [],
  "sha256": {},
  "size_bytes": {},
  "role": "image",
  "backend": "stable-diffusion.cpp",
  "compute": "vulkan",
  "memory": {},
  "capabilities": ["text-to-image", "image-editing"],
  "verification": {}
}
```

Do not invent `files` until discovered from the actual source repository/model card/API.

---

# 14. HEADLESS MODEL DOWNLOADER

Use Hugging Face CLI/API instead of Git for large model blobs.

The downloader must:

1. resolve the repository/revision;
2. enumerate the actual required files;
3. download to the configured model store;
4. resume interrupted transfers;
5. record revision;
6. calculate SHA256;
7. compare against a trusted expected hash if one is published;
8. otherwise record locally computed hash as an installation fingerprint and mark upstream hash as `NOT_PUBLISHED`;
9. validate expected file sizes and file structure;
10. atomically promote files from temporary to final location;
11. update the model lock only after successful validation.

Never claim a SHA256 is upstream-authored when it is only locally calculated.

Never place a partially downloaded file in the active model path.

---

# 15. MODEL UPDATE POLICY

Model updates require a new immutable revision entry.

Do not silently replace production model files.

Workflow:

```text
new revision discovered
→ download into staging
→ hash
→ backend load test
→ functional smoke test
→ visual quality test
→ memory benchmark
→ compare against current
→ explicit promotion
```

If the new model regresses compatibility or memory, keep the old production revision.

---

# 16. RESOURCE MANAGER

Treat the AMD iGPU system as a constrained UMA machine.

Never assume:

```text
12 GB RAM + 12 GB VRAM = 24 GB dedicated usable GPU memory
```

At startup, probe:

- Vulkan device,
- Vulkan heap/budget,
- current allocation,
- free system RAM,
- total system RAM,
- CPU features,
- driver version,
- Vulkan version,
- storage throughput,
- filesystem type,
- available disk space.

Derive a dynamic safe budget.

Keep an OS safety reserve.

Keep a Blender reserve.

Keep a model reserve.

---

# 17. MEMORY TIERS

Use these conceptual states:

```text
COLD   = on storage only
WARM   = likely in OS page cache / RAM
HOT    = loaded by worker
BUSY   = actively computing
EVICT  = being unloaded
```

Do not pin the entire model in RAM unless benchmarking demonstrates that it is beneficial and safe.

Use mmap/lazy loading when supported.

For llama.cpp, the current CLI supports load modes including mmap and lazy mode; re-check exact options in the checked-out revision. [Upstream: https://github.com/ggml-org/llama.cpp]

---

# 18. MODEL LOCALITY SCHEDULING

The scheduler must minimize repeated model loads on HDD.

Given a queue:

```text
Bonsai
Bonsai
Trellis
Bonsai
Bonsai
TTS
```

it may reorder independent jobs to reduce churn:

```text
Bonsai
Bonsai
Bonsai
Bonsai
Trellis
TTS
```

Dependency order always wins over locality optimization.

Never reorder jobs in a way that changes the meaning of a user-approved dependency.

---

# 19. PREDICTIVE PREFETCH

Use the dependency graph and queue to predict likely next models.

During current computation:

```text
current GPU job
+
background HDD prefetch of likely next model data
```

is allowed only if it does not cause memory pressure or interfere with the current compute job.

Prefetch must be cancelable.

Do not prefetch entire multi-gigabyte models indiscriminately.

Use file access priority and stage only likely-required model components.

---

# 20. HEAVY WORKER POLICY

Default:

```text
MAX_HEAVY_GPU_JOBS = 1
```

Heavy:

- Bonsai/FLUX image generation,
- TRELLIS 3D generation,
- other large diffusion workers,
- GPU-heavy Blender jobs,
- large music synthesis.

The scheduler may relax this only when a hardware benchmark proves a safe concurrent configuration.

---

# 21. LLAMA/QWEN AGENT MEMORY POLICY

Initial production candidate:

```text
Qwen3-VL-8B GGUF Q4_K_M
context target: 24K initially
parallel sequences: 1
mmap: enabled when supported
lazy loading: enabled where useful
KV quantization: benchmark-driven
```

Do not begin with 128K/256K context merely because the model supports it.

The Story Bible is external memory, not a giant repeated prompt.

---

# 22. AGENT MEMORY

Store:

- story entities,
- asset facts,
- scene facts,
- shot facts,
- continuity constraints,
- user preferences relevant to the project,
- prior approved/rejected generations,
- generation metadata.

Use SQLite FTS5 for exact text retrieval.

Use embeddings only when needed.

Use reranking to reduce irrelevant context.

The agent receives a compact state snapshot plus retrieved evidence.

---

# 23. MASTER AGENT ROLES

Logical subagents share the same model runtime where possible.

Roles:

```text
DIRECTOR
STORY
CHARACTER
WORLD
STORYBOARD
IMAGE
ASSET
THREE_D
RIG
MOTION
CAMERA
LIGHTING
FX
AUDIO
EDITOR
QA
ARCHIVIST
RELEASE
```

Do not load one separate full LLM per logical subagent.

Use typed tool permissions and system-role profiles.

---

# 24. MASTER AGENT OPERATING LOOP

Every non-trivial action follows:

```text
OBSERVE
→ RETRIEVE
→ PLAN
→ VALIDATE PLAN
→ EXECUTE
→ INSPECT
→ VERIFY
→ REPAIR IF NEEDED
→ VERIFY AGAIN
→ COMMIT
→ UPDATE MEMORY
→ REPORT
```

Never skip `INSPECT` or `VERIFY` for artifact-producing operations.

---

# 25. TOOL CONTRACTS

All agent tools use typed schemas.

Examples:

```text
story.create
story.edit
character.create
character.generate_references
image.generate
image.edit
image.remove_background
asset.image_to_3d
asset.retopology
asset.validate
blender.import_asset
blender.create_scene
blender.rig_character
motion.create
motion.retarget
camera.configure
lighting.configure
fx.configure
dialogue.write
speech.transcribe
voice.generate
lipsync.create
music.generate
timeline.edit
render.preview
render.final
qa.image
qa.mesh
qa.rig
qa.motion
qa.timeline
qa.movie
project.save
project.load
project.export
```

Tools must return structured results containing actual artifact references and verification status.

---

# 26. BONSai IMAGE PIPELINE

Primary path:

```text
prompt/reference
→ request validation
→ model-manager admission
→ Bonsai Q2_K loaded
→ Qwen text encoder loaded
→ FLUX VAE loaded
→ Vulkan generation
→ output file
→ image decoder validation
→ metadata write
→ optional visual QA
→ artifact commit
```

The agent must verify whether the current stable-diffusion.cpp build accepts the Bonsai Q2_K GGUF directly through the FLUX.2 Klein path.

Do not write a custom Bonsai ternary kernel in the first milestone unless real compatibility testing proves the existing path cannot run the selected GGUF.

---

# 27. IMAGE FEATURES

Implement in this order:

1. Text-to-image.
2. Single-image edit/reference.
3. Mask-based edit if supported by the verified backend path.
4. Multi-view reference generation.
5. Character reference pack creation.
6. Prop reference pack creation.
7. Storyboard frame generation.
8. Optional LoRA support only after a real backend test proves the adapter format/path.
9. Control lane using a genuinely supported control backend/path.

Never expose a UI option that silently does nothing.

If a feature is unsupported, show `NOT AVAILABLE ON THIS BACKEND` and keep the fallback path usable.

---

# 28. CONTROL SYSTEM

Control should be an abstraction:

```text
ControlSignal
```

with implementations such as:

```text
pose
openpose
-depth
depth
canny
edge
segmentation
mask
reference
```

The agent must distinguish:

```text
SUPPORTED_NATIVE
SUPPORTED_VIA_COMPATIBILITY_LANE
EXPERIMENTAL
UNSUPPORTED
```

Do not claim native FLUX.2 ControlNet support without real current evidence.

Where appropriate, use a verified SD1.5/SDXL ControlNet lane to derive pose/depth/layout conditioning and then feed validated structure/reference data into the image workflow.

---

# 29. CHARACTER CREATION

Create a canonical character entity before downstream generation.

Required:

```text
id
name
body description
face description
hair
wardrobe
palette
proportions
voice
personality
reference images
canonical version
```

Generate reference pack:

```text
front
3/4
side
back
full body
face close-up
neutral expression
expression sheet
costume sheet
```

Run consistency QA before sending the asset to 3D.

---

# 30. BACKGROUND REMOVAL

Background removal must preserve the original input.

Output:

```text
source.png
mask.png
cutout.png
```

Every mask and cutout is independently validated.

Prefer a real backend available in the current TRELLIS/3D stack where it is genuinely supported on the target. Otherwise use a tested standalone local segmentation/removal backend.

---

# 31. IMAGE → 3D PIPELINE

Canonical path:

```text
approved reference
→ cutout/mask
→ TRELLIS.2 Q4 Vulkan
→ raw 3D result
→ structural validation
→ topology checks
→ optional retopology
→ UV/material validation
→ GLB export
→ Blender import
→ turntable render
→ visual QA
```

TRELLIS.2 may produce a textured GLB; do not assume the result is rig-ready.

The current trellis.cpp project documents Q4 GGUF workflows and Vulkan binaries on Windows/Linux. Re-check the exact release and tested flags at implementation time. [Upstream: https://github.com/pwilkin/trellis.cpp]

---

# 32. 3D VALIDATION

For every generated mesh test:

```text
GLB parse
vertices > 0
faces > 0
no NaN coordinates
no Inf coordinates
finite bounding box
no obviously degenerate mesh
material references valid
texture references valid
UVs present when expected
scene graph valid
```

For characters additionally:

```text
T/A-pose suitability
scale sanity
orientation sanity
body-part coverage
```

Then create a scripted Blender turntable render.

---

# 33. RETOPOLOGY

Retopology is its own job.

Store:

```text
raw.glb
retopo.glb
```

Never replace the raw output.

Run:

```text
polycount check
quad ratio where applicable
non-manifold check
normal check
UV check
turntable render
```

---

# 34. CHARACTER RIGGING

Primary:

```text
Blender Rigify
```

Optional AI rigging backends must remain adapters and must be verified separately.

Pipeline:

```text
glb
→ normalize orientation/scale
→ identify humanoid landmarks
→ build Rigify metarig
→ place bones
→ generate rig
→ bind/weights
→ pose tests
→ face rig
→ visemes
```

---

# 35. RIG TEST MATRIX

Every rigged character must be tested with:

```text
neutral
T-pose
A-pose
arms up
arms forward
squat
kneel
walk pose
run pose
left bend
right bend
head turn
look up
look down
```

Produce a pose-sheet render and inspect programmatically and visually.

A rig is invalid if severe deformation artifacts are visible or if bones/constraints fail to evaluate.

---

# 36. MOTION ARCHITECTURE

The canonical motion stack is layered:

```text
Action Library
        ↓
Motion composition
        ↓
Mocap / pose retargeting
        ↓
Optional text-to-motion AI
```

Do not make a CUDA-only text-to-motion research repository a hard dependency of the local Vulkan release.

---

# 37. ACTION LIBRARY

Create reusable Blender actions:

```text
idle
walk
run
sprint
sit
stand
turn
look
wave
point
pick_up
drop
reach
push
pull
jump
fall
fight
```

Each action has metadata:

```text
id
duration
loopable
root_motion
compatible_rig_type
source
license
```

---

# 38. MOTION PLANNING

Text instructions are translated into structured motion plans.

Example:

```text
"Anna walks four meters, slows down, stops, and looks left."
```

becomes:

```text
walk(distance=4m)
decelerate
stop
head_turn(left)
```

The agent then creates editable Blender actions/keyframes.

---

# 39. CAMERA SYSTEM

Create a real camera subsystem.

Presets:

```text
static
push_in
pull_out
dolly
truck
orbit
arc
crane
pan
tilt
rack_focus
tracking
POV
handheld
over_shoulder
```

Expose real parameters:

```text
position
rotation
lens
sensor
focus
dof
path
speed
look_at
```

AI suggestions modify these deterministic values rather than replacing a shot with an uncontrollable generated video frame.

---

# 40. LIGHTING SYSTEM

Use structured Blender lights and world settings.

Presets:

```text
day
night
sunset
moon
neon
interior
rain
warm
cold
dramatic
sci-fi
```

Persist every parameter.

---

# 41. FX SYSTEM

Use deterministic Blender systems where practical:

```text
fog
rain
snow
dust
smoke
fire
sparks
debris
lightning
hologram
energy
wind
```

The agent sets real scene parameters.

Avoid making an AI video model responsible for persistent physics or scene truth.

---

# 42. STORYBOARD

Storyboard entities contain:

```text
shot_id
scene_id
frame
camera
action
characters
location
dialogue
duration
lighting
fx
motion
references
status
qa
```

User can reorder storyboard cards manually.

---

# 43. DIALOGUE WRITING

The story/agent layer creates structured screenplay dialogue.

Store:

```text
speaker
line
emotion
subtext
pace
pause
direction
shot_id
```

Never store only raw generated text without scene/shot links.

---

# 44. STT

Use whisper.cpp for:

```text
voice command
transcription
mocap annotation
rough dialogue transcription
```

The voice command pipeline is:

```text
microphone
→ STT
→ agent intent parser
→ typed tool call
→ verification
```

The agent must show the interpreted action for potentially destructive changes.

---

# 45. TTS / VOICEOVER

Voice assets are canonical project entities.

Store:

```text
voice_id
speaker
reference
language
style
pitch
speed
license/consent metadata
```

Every generated voice line stores source text and generation metadata.

---

# 46. LIP SYNC

For persistent 3D characters:

```text
audio
→ phoneme timing
→ viseme timing
→ Blender facial rig
```

Do not make video-based lip sync the only path for 3D characters.

---

# 47. MUSIC

Music is structured media.

Store:

```text
track_id
scene_id
mood
tempo
instrumentation
length
seed where supported
source model
stems
```

Generate music as separate stems where the backend supports it.

---

# 48. TIMELINE / EDITOR

The timeline must support:

```text
video clips
audio clips
transitions
cuts
trim
split
move
speed
fade
markers
subtitles
```

Blender VSE is the canonical local timeline for v1 unless a custom timeline is needed for UI responsiveness.

The UI may expose a richer editor while keeping Blender/VSE as the render-authoritative timeline format.

---

# 49. FINAL RENDER

Default master:

```text
1920 × 1080
```

The exact FPS is project-level state and must not be guessed.

Final render gate requires:

```text
story valid
characters locked
locations valid
assets valid
rigs valid
motions valid
shots complete
no missing media
audio sync valid
timeline valid
fps consistent
resolution valid
encoder available
QA pass
```

---

# 50. FFmpeg FINALIZATION

Use FFmpeg for robust final mux/encode.

Before encoding:

```text
ffprobe input video
ffprobe audio
validate durations
validate frame rate
validate resolution
validate audio channels
```

After encoding:

```text
ffprobe final
SHA256 final
visual sample
audio sample
```

---

# 51. UI/UX PRINCIPLES

The desktop UI must be a full production tool, not a chatbot wrapper.

Top-level areas:

```text
Project
Story
Characters
Locations
Props
Storyboard
Scenes
Shots
3D
Motion
Camera
Lighting
FX
Audio
Timeline
Render
QA
Settings
```

Global assistant dock:

```text
What do you want to create or change?
```

---

# 52. UI LAYOUT

Target layout:

```text
┌──────────────────────────────────────────────────────────────┐
│ HCS MOVIEFORGE  Save ●  Undo  Redo  Render  ● LOCAL READY   │
├──────────────┬───────────────────────────────┬───────────────┤
│ PROJECT      │                               │ INSPECTOR     │
│ Story        │                               │ Properties    │
│ Characters   │           CANVAS              │ Versions      │
│ Locations    │        2D / 3D / Shot         │ References    │
│ Props        │                               │ QA            │
│ Storyboard   │                               │               │
│ Scenes       │                               │               │
│ Shots        │                               │               │
│ Motion       │                               │               │
│ Camera       │                               │               │
│ Lighting     │                               │               │
│ FX           │                               │               │
│ Audio        │                               │               │
│ Timeline     │                               │               │
├──────────────┴───────────────────────────────┴───────────────┤
│ AI ASSISTANT                                                   │
│ > What should we change?                         [Send]       │
└──────────────────────────────────────────────────────────────┘
```

The UI must remain responsive while workers execute.

Use WebSockets/event streams for job state, not polling every few milliseconds.

---

# 53. MANUAL IMAGE EDITOR

Provide:

```text
upload
crop
mask
brush
erase
inpaint/edit
reference images
before/after
version compare
accept/reject
```

The underlying source and derived artifacts remain separate.

---

# 54. MANUAL 3D EDITOR

Expose:

```text
move
rotate
scale
materials
object visibility
camera
lights
bones
weights
```

Browser preview may use Three.js/React Three Fiber.

Blender remains authoritative for final scene state.

---

# 55. MANUAL MOTION EDITOR

Expose:

```text
trim
split
blend
speed
loop
mirror
move
keyframe
```

---

# 56. MANUAL CAMERA/LIGHT/FX EDITORS

Every AI-produced recommendation must become editable parameters.

AI action:

```text
"make this shot more tense"
```

may produce an editable plan such as:

```text
lens 50 → 85
camera distance ↓
dolly speed ↓
key light intensity ↓
rain density ↑
```

Never hide the real changes.

---

# 57. MASTER AGENT UX

Simple requests should be simple.

Example:

```text
"Make the robot blue."
```

The agent:

```text
find canonical robot
→ create version
→ edit material/reference as appropriate
→ validate
→ preview
```

Complex actions get a readable plan first.

Example:

```text
PLAN
1. Update canonical wardrobe.
2. Rebuild affected reference pack.
3. Mark dependent 3D asset stale.
4. Rebuild character asset.
5. Revalidate affected shots.
```

---

# 58. PROJECT VERSIONING

Every destructive-looking action is implemented as a versioned mutation.

Store parent/child relationships.

Use dependency invalidation:

```text
character v4
→ old rig stale
→ affected shots stale
→ dependent renders stale
```

Do not regenerate unrelated scenes.

---

# 59. SELF-HEALING

Self-healing means diagnosis + bounded recovery, not infinite blind retry.

Error classes:

```text
OOM
MODEL_INIT
BACKEND_CRASH
DRIVER
INVALID_INPUT
CORRUPT_OUTPUT
MISSING_DEPENDENCY
BLENDER_SCRIPT
FFMPEG
DISK_IO
QUALITY_FAILURE
CONTINUITY_FAILURE
TIMEOUT
CANCELLED
```

Recovery example:

```text
OOM
→ collect telemetry
→ unload unrelated model
→ reduce worker concurrency
→ reduce resolution/context/offload placement
→ retry once
→ validate
```

No more than the configured retry budget.

---

# 60. OOM RECOVERY LADDER

For image/3D/agent jobs:

```text
1. stop unrelated heavy jobs
2. free stale cache
3. evict idle models
4. reduce GPU placement
5. increase CPU offload
6. enable lower-memory model path if available
7. lower preview resolution
8. reduce context/KV size for LLM jobs
9. reduce batch/concurrency
10. retry
11. if still failing: mark blocked with actual evidence
```

Never loop forever.

---

# 61. CANCELLATION SEMANTICS

Cancellation is cooperative first:

```text
user cancel
→ job CANCEL_REQUESTED
→ worker receives cancellation
→ backend stops safely where supported
→ partial files quarantined
→ resources released
→ job CANCELLED
```

If a subprocess cannot cancel safely, terminate the known child process owned by the supervisor.

Never kill unrelated processes.

---

# 62. OBSERVABILITY

Every worker emits structured JSON logs.

Required telemetry:

```text
timestamp
job_id
worker_id
model_id
backend
state
duration
cpu_percent
ram_used
ram_peak
gpu_used
gpu_peak
disk_read
disk_write
artifact_id
error_class
```

Logs must be searchable by job/project.

---

# 63. EXTERNAL CODE-QUALITY TOOLING

The project MUST use tools outside the LLM-generated reasoning itself.

## Python

Use:

```text
ruff check
ruff format --check
pytest
coverage
pyright or mypy
pip-audit
```

Ruff is an external linter/formatter. [Upstream: https://github.com/astral-sh/ruff]

The exact type checker should be chosen once and pinned.

## PowerShell

Use:

```text
PSScriptAnalyzer
```

for `.ps1` and `.psm1` sources. [Upstream: https://github.com/PowerShell/PSScriptAnalyzer]

## Shell

Use:

```text
shellcheck
shfmt
```

for Bash scripts where installed.

## TypeScript / React

Use:

```text
eslint
prettier --check
 tsc --noEmit
npm test
npm run build
```

The final repository must not depend on editor-only type checking.

## Rust/Tauri

Use:

```text
cargo fmt -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features
cargo build --release
```

## C/C++ integrations

Use, as supported by the checked-out project/toolchain:

```text
cmake configure
cmake build
ctest
clang-tidy
cppcheck
compiler warnings as errors for project-owned code where practical
```

Do not attempt to lint vendored third-party source with an incompatible house rule set unless necessary.

## GitHub Actions

Validate workflows with an external workflow linter such as `actionlint` and a security scanner such as `zizmor` where available. [Upstream: https://github.com/rhysd/actionlint] [Upstream: https://github.com/woodruffw/zizmor]

## Secrets/security

Use `gitleaks` in CI and locally if available.

Use dependency/security scanners appropriate to each language.

## Documentation

Use `markdownlint-cli2` and a URL/link checker such as `lychee` where appropriate.

---

# 64. GIT INTEGRITY CHECKS

Before every commit:

```text
git diff --check
git status
```

Before release:

```text
no unintended generated files
no credentials
no tokens
no local absolute paths
no machine-specific secrets
```

Run gitleaks.

---

# 65. UNIT TEST ARCHITECTURE

Three levels are mandatory.

## Level 1 — Pure unit

Examples:

```text
memory_budget_calculation
job_state_transition
job_deduplication
artifact_manifest
hashing
path_normalization
model_manifest_validation
project_schema
camera_parameter_validation
timeline math
```

These may use mocks.

## Level 2 — Real integration

Examples:

```text
Bonsai → real PNG
TRELLIS → real GLB
Blender → real render
Whisper → real transcript
CosyVoice → real WAV
FFmpeg → real output
```

## Level 3 — E2E

At least one miniature end-to-end film is generated with real backends.

---

# 66. IMAGE GOLDEN TEST

Use a deterministic/sufficiently controlled fixture.

Test:

```text
input
→ Bonsai
→ PNG
→ validator
→ visual sample
```

Persist:

```text
prompt
seed where supported
model revision
parameters
output hash
metrics
```

AI outputs are not pixel-exact by default; use structural/semantic thresholds rather than brittle exact-image equality.

---

# 67. 3D GOLDEN TEST

Fixture:

```text
tests/golden/3d/character.png
```

Run:

```text
TRELLIS
→ GLB
→ parser
→ Blender import
→ turntable render
```

Validate mesh and render existence.

---

# 68. RIG GOLDEN TEST

```text
GLB
→ Rigify
→ pose sheet
→ render
```

Review:

```text
bone count
required controls
pose evaluation
weight integrity
visual deformation
```

---

# 69. MOTION GOLDEN TEST

```text
rig
→ walk
→ turn
→ stop
→ render
```

Programmatic metrics may include:

```text
keyframe continuity
frame count
root displacement
unexpected NaN
```

Visual review checks obvious deformation and motion discontinuity.

---

# 70. CAMERA GOLDEN TEST

Given a canonical scene:

```text
camera preset
→ scene render
```

Verify:

```text
camera exists
lens matches recipe
focus target valid
render composition within expected bounds
```

---

# 71. FX GOLDEN TEST

For each effect:

```text
base scene
→ FX enabled
→ preview render
```

Check no crash, no missing nodes, no invalid references, and expected visual presence.

---

# 72. AUDIO GOLDEN TEST

For TTS/music:

```text
input
→ real backend
→ WAV
→ ffprobe
→ amplitude/silence checks
→ artifact commit
```

Check clipping and duration.

---

# 73. FINAL MINI-FILM E2E TEST

Create a tiny fixture film:

```text
1 project
2 characters
1 location
1 prop
3 scenes
6 shots
20–60 seconds final duration
```

Pipeline:

```text
story
→ character references
→ image generation
→ image→3D
→ rig
→ motion
→ camera
→ lighting
→ FX
→ dialogue
→ TTS
→ music
→ timeline
→ render
→ QA
→ final 1080p
```

This E2E must use real model execution, not mocks.

---

# 74. STRESS TESTS

## Stress A — model churn

Repeatedly alternate:

```text
Bonsai
TRELLIS
Qwen
CosyVoice
ACE-Step
Blender
```

At least 50 cycles in a standard stress profile unless the hardware cannot complete it safely; if the target cannot complete the full count, report the exact completed count and failure evidence.

Measure:

```text
peak RAM
peak GPU
load count
unload count
HDD bytes
worker restarts
errors
```

## Stress B — memory pressure

Intentionally push above normal memory demand within a controlled test process.

Expected:

```text
OOM detected
→ cleanup
→ fallback
→ job fails/retries safely
→ no project corruption
```

## Stress C — worker kill

Kill a worker during:

```text
model load
generation
validation
commit
```

Verify supervisor recovery and project consistency.

## Stress D — Blender crash

Terminate only the known Blender child process during a render.

Verify:

```text
partial artifact quarantined
project intact
job recoverable
```

## Stress E — corrupt output

Corrupt an output file before validation.

Expected:

```text
validator failure
artifact rejected
no false success
```

## Stress F — corrupt model

Corrupt a staged model file.

Expected:

```text
hash/structure failure
model never promoted to active
```

## Stress G — disk pressure

Simulate low free space in a controlled test location.

Expected:

```text
large artifact blocked safely
metadata/project state preserved
clear error
```

## Stress H — cancellation storm

Queue many jobs and cancel a mix of queued/loading/running jobs.

Verify no resource leaks.

## Stress I — long soak

Run mixed workloads for several hours when feasible.

Record memory trends and restart counts.

---

# 75. HDD BENCHMARK

Compare:

```text
FIFO scheduler
vs
model-locality-aware scheduler
```

on the same deterministic workload.

Record:

```text
total runtime
model load count
cold start count
bytes read
average queue wait
```

Do not claim the scheduler is faster until measurements prove it.

---

# 76. VISUAL VERIFICATION PIPELINE

Every important media feature gets a two-part test:

```text
programmatic validation
+
visual validation
```

Programmatic validators:

```text
Pillow / image metadata
ffprobe
GLTF/GLB parser
Blender headless validation
custom mesh checks
JSON schema
```

Visual validation:

```text
render representative outputs
→ generate contact sheets
→ compare to golden/reference
→ optional local VLM review
→ human review during release certification
```

The LLM must not be the only judge.

---

# 77. MANUAL RELEASE VISUAL REVIEW

For every release candidate, a human operator must be able to inspect:

```text
character sheet
image generation sample
3D turntable
rig pose sheet
motion sample
camera sample
FX sample
voice sample
music sample
complete mini-film
UI screenshots
```

The agent must prepare these review pages/artifacts automatically.

---

# 78. NO MOCK PROTECTION IN CI

CI must reject fake implementations where practical.

Examples of safeguards:

```text
artifact path must exist
file size > minimal threshold
real encoder metadata present
backend process must have executed
model file hash must match lock
command exit code must be checked
real integration environment marker required
```

Tests that return `passed` without touching the real backend must not count as integration tests.

---

# 79. EXTERNAL BACKEND CHECKERS

Create dedicated test harnesses around the real binaries.

Each harness:

```text
locates binary
locates model
runs command
captures stdout/stderr
records exit code
records duration
records resource telemetry
validates output
writes JSON evidence
```

Examples:

```text
scripts/test/test_bonsai.ps1
scripts/test/test_trellis.ps1
scripts/test/test_blender.ps1
scripts/test/test_whisper.ps1
scripts/test/test_cosyvoice.ps1
scripts/test/test_ffmpeg.ps1
```

The same semantic harness contract should exist on Linux with `.sh` wrappers where appropriate.

---

# 80. BUILD VERIFICATION

For every implementation phase:

```text
format
→ lint
→ type-check
→ compile/build
→ unit tests
→ backend smoke
→ integration
```

No phase is considered complete because the source compiles alone.

---

# 81. WINDOWS BUILD

Use a reproducible build environment.

Prefer:

```text
MSVC
Ninja
CMake
Vulkan SDK
Python 3.x pinned by pyproject
Node LTS pinned by package manager metadata
Rust stable pinned by rust-toolchain.toml when Tauri is used
```

The exact versions must be discovered from upstream requirements and pinned in the repository once selected.

Do not hard-code versions solely from memory.

---

# 82. LINUX BUILD

Support:

```text
Ubuntu/Debian-style Vulkan environment
```

using the same core source and configuration system.

Provide:

```text
start.sh
stop.sh
build.sh
install.sh
```

where practical.

Linux must run a CPU-only fallback for project management even when AI GPU backends are unavailable.

---

# 83. DOCKER POLICY

Do not make Docker a local prerequisite for the core workstation.

Containers may be used in CI for isolated verification where beneficial, but the desktop product must run natively on Windows and Linux.

---

# 84. CONFIGURATION

Use a validated configuration hierarchy:

```text
built-in defaults
→ hardware profile
→ global config
→ project config
→ session overrides
```

Never store secrets in the repository.

---

# 85. CLI UX

The CLI must be readable and scripting-friendly.

Human mode:

```text
✓ Vulkan device detected
✓ Bonsai model verified
⚠ TRELLIS 1024 benchmark not yet certified
```

Machine mode:

```text
--json
```

returns stable JSON schema.

---

# 86. DEBUGGING WORKFLOW FOR THE AGENT

When a test fails:

1. capture exact command,
2. capture exit code,
3. capture stdout/stderr,
4. capture environment,
5. capture model revision,
6. capture resource state,
7. reproduce once in isolation,
8. identify root cause,
9. patch the smallest correct layer,
10. rerun the failing test,
11. rerun the relevant integration suite,
12. rerun regression.

Do not change unrelated architecture just to make a test green.

---

# 87. VISUAL BUG DEBUGGING

When a rendered artifact is wrong:

```text
render fixture
→ inspect image properties
→ compare reference
→ inspect Blender scene graph
→ inspect model/generation metadata
→ inspect VLM description if available
→ isolate layer
→ patch
→ rerender
```

Never change prompts blindly without first determining whether the failure is in:

```text
model
conditioning
scene state
camera
lighting
postprocess
export
```

---

# 88. IMAGE QUALITY ACCEPTANCE

An image is accepted only when:

```text
valid file
correct dimensions
non-empty
no decoder errors
expected semantic content
identity/reference constraints within accepted threshold
no severe visible artifact
```

For character references, check identity/appearance consistency across the set.

---

# 89. 3D QUALITY ACCEPTANCE

An asset is accepted only when:

```text
valid GLB
valid scene graph
finite geometry
usable topology
expected materials/textures
reasonable dimensions
Blender import succeeds
turntable render succeeds
```

---

# 90. FILM CONTINUITY SYSTEM

Track continuity for:

```text
wardrobe
hair
props
injuries
character positions
weather
time of day
lighting
location geometry
camera state where required
```

Each shot can declare:

```text
inherits_from_shot
continuity_constraints
```

QA checks the relevant constraints only; do not compare every frame of every shot unnecessarily.

---

# 91. FINAL MOVIE QA

Programmatic:

```text
missing media = 0
fps consistent
resolution consistent
audio exists
video exists
audio duration valid
video duration valid
subtitle references valid
final file decodes
```

Visual sample:

```text
beginning
middle
end
key dialogue shots
key VFX shots
key character continuity shots
```

Audio sample:

```text
dialogue
music
SFX
master level
```

---

# 92. RELEASE ARTIFACTS

A release must contain, as applicable:

```text
Windows portable package
Linux package
checksums
SBOM
versioned model manifest
release notes
README
upgrade notes
```

Do not bundle huge model weights into GitHub releases unless licensing, size, and bandwidth explicitly permit it.

Prefer model manifests + headless downloader.

---

# 93. SHA256 RELEASE RULE

For every release artifact:

```text
file
→ SHA256
→ checksums file
→ independent re-read
→ verify checksum
```

For model weights:

```text
download
→ local SHA256
→ compare upstream published hash where available
```

If no upstream hash exists:

```text
local fingerprint
```

must be clearly labelled as local, not as an upstream signature.

---

# 94. GITHUB REPOSITORY

The GitHub repository is source-of-truth for code, manifests, docs, tests, workflows, and tiny fixtures.

Do not commit:

```text
GGUF
safetensors
large Blender projects
renders
user projects
credentials
cache
```

unless an explicit repository policy says otherwise.

---

# 95. GITHUB WORKFLOWS

Required workflows:

```text
ci.yml
windows-build.yml
linux-build.yml
security.yml
docs.yml
release.yml
space-sync.yml
```

CI should run:

```text
lint
format
type-check
unit
schema tests
build
workflow lint
security scan
```

Hardware-dependent Vulkan/AI integration tests run on self-hosted hardware or dedicated manual certification jobs.

Do not fake hardware capability in generic CI.

---

# 96. RELEASE PROCESS

Never publish directly from an unverified working tree.

Process:

```text
feature complete
→ full CI
→ local Vulkan certification
→ golden suite
→ stress suite
→ soak suite
→ package
→ SHA256
→ clean-room install test
→ clean-room run test
→ docs verification
→ git tag
→ GitHub release
→ deployment
```

Tags should follow a documented semantic versioning policy.

---

# 97. CLEAN-ROOM INSTALL TEST

Before calling a release stable:

1. create a fresh temporary directory,
2. install only using the documented release path,
3. run `movieforge doctor`,
4. synchronize the pinned models,
5. run image smoke,
6. run 3D smoke where certified,
7. create a new project,
8. save/reopen it,
9. run the mini-film,
10. verify final 1080p output,
11. verify hashes.

This catches missing dependencies that a developer's environment can hide.

---

# 98. README REQUIREMENTS

README must be understandable without reading source code.

Include:

```text
what MovieForge is
what it can do
supported OS
hardware expectations
what works locally
what is optional
model sources
licenses
installation
first run
start/stop
UI screenshots
workflow diagram
known limitations
troubleshooting
verification status
release status
```

Never market an unverified backend as production-ready.

Use status labels such as:

```text
VERIFIED LOCAL
EXPERIMENTAL
OPTIONAL
UNAVAILABLE
```

with a date and tested hardware/software profile.

---

# 99. GRAPHICAL README

The README should include simple architecture diagrams and at least these screenshots when the UI exists:

```text
Project dashboard
Character editor
3D scene
Storyboard
Timeline
Agent assistant
QA panel
```

Images should come from the actual application, not generated concept art pretending to be screenshots.

---

# 100. HUGGING FACE SPACE

The Space is a demo adapter, not the canonical local workstation.

Use Gradio for the demo UI.

Expose a constrained public workflow:

```text
image generation
image editing/reference
character reference pack sample
image → 3D demo where feasible
storyboard sample
voice sample where licensing permits
```

Do not expose an unbounded autonomous movie-production loop in a public demo.

Do not store user uploads longer than required by the demo policy.

---

# 101. ZEROGPU DEPLOYMENT POLICY

At implementation time, verify the current Hugging Face ZeroGPU/Gradio requirements from official documentation.

Use GPU allocation only around expensive functions.

Keep model loading explicit and compatible with the Space hardware/runtime.

The public Space may use a CUDA adapter even though the desktop product uses Vulkan; the product API and semantic contracts remain shared, while runtime adapters differ.

The Space must never claim:

```text
"this is exactly the same runtime as local Vulkan"
```

unless it actually is.

---

# 102. SPACE CI

The Space deployment must be tested independently.

Required checks:

```text
app import
UI render
one real generation
artifact validation
error handling
session cleanup
```

Do not push a broken Space just because GitHub CI passed.

---

# 103. LICENSE / MODEL REGISTRY

Create a registry:

```text
model
source URL
revision
license
commercial-use note
runtime
hardware
verification date
```

The README must state when a model has a usage restriction.

Never assume a model is commercially unrestricted because it is hosted on Hugging Face.

---

# 104. CLOUD BUILDING

Use GitHub Actions for:

```text
Windows build
Linux build
unit/integration tests that do not require GPU
release packaging
artifact hashing
security scans
docs checks
```

Use hardware-specific self-hosted runners or manual certification for AMD Vulkan tests.

Cloud builds must publish build logs and artifacts.

---

# 105. INSTALLER / PORTABLE PACKAGE

First release should prefer portable deployment.

Windows:

```text
HCS-MovieForge-windows-x64-portable.zip
```

Linux:

```text
HCS-MovieForge-linux-x86_64.tar.gz
```

Each contains:

```text
app
start/stop scripts
doctor
config templates
model manifests
README
licenses
```

Models are downloaded separately.

---

# 106. DOCTOR COMMAND ACCEPTANCE

`movieforge doctor` must return non-zero if any REQUIRED local component is broken.

Example:

```text
✓ OS
✓ Vulkan
✓ Git
✓ Python
✓ Node
✓ Rust
✓ CMake
✓ Blender
✓ FFmpeg
✓ llama.cpp
✓ stable-diffusion.cpp
✓ trellis.cpp
✓ Bonsai model hash
✓ Qwen model hash
✓ VAE model hash
⚠ optional TTS backend

LOCAL CORE: READY
```

Do not mark `READY` if a required component is absent.

---

# 107. BENCHMARK COMMAND ACCEPTANCE

`movieforge benchmark` must produce machine-readable JSON plus a readable report.

At minimum:

```text
Bonsai image first-run
Bonsai image warm-run
TRELLIS 512
TRELLIS 1024 if supported
Qwen-VL prompt-only
Qwen-VL image inspection
Whisper transcription
TTS generation
Blender preview
FFmpeg encode
HDD cold/warm model load
```

Each line includes:

```text
duration
peak RAM
peak GPU if measurable
result status
model revision
backend
```

---

# 108. HARDWARE AUTO-CALIBRATION

At first launch:

```text
probe
→ test Vulkan
→ run microbenchmarks
→ estimate safe memory budget
→ determine GPU offload configuration per worker
→ persist hardware profile
```

Never permanently hard-code a single GPU-layer count.

Per-worker profiles are allowed:

```text
agent.ngl
image.gpu_budget
3d.gpu_budget
blender.gpu_policy
```

---

# 109. MODEL LOADING IMPLEMENTATION RULES

Use:

```text
staging directory
atomic rename
lock file
lease
```

When loading:

```text
check hash
check file size
check model manifest
check free resources
acquire GPU lease
start worker
health check
mark HOT
```

When unloading:

```text
stop request
flush pending work
release resources
close handles
verify memory decreases
mark COLD
```

If resource release cannot be verified, mark the worker `DEGRADED` and restart it safely.

---

# 110. WORKER API

Every worker follows the same protocol:

```text
health()
capabilities()
estimate(request)
prepare(request)
run(request)
cancel(job_id)
cleanup()
shutdown()
```

Responses include:

```text
status
job_id
artifacts
telemetry
warnings
error
```

---

# 111. BACKEND CAPABILITY MATRIX

Create a generated matrix in the application and README.

Example columns:

```text
backend
OS
CPU
Vulkan
CUDA
RAM
GPU memory
T2I
I2I
references
LoRA
control
3D
TTS
STT
music
status
```

Status must come from actual verification records, not manual optimism.

---

# 112. EXPERIMENTAL FEATURES

Any feature not fully verified is isolated under an `experimental` capability namespace.

Experimental workers may never block stable workflows.

Example:

```text
motion.text.experimental
```

instead of exposing it as production `motion.text` until certification.

---

# 113. NO SILENT FALLBACKS

If the user asks for Bonsai and Bonsai is unavailable, do not silently switch to another model while claiming Bonsai was used.

The system may offer:

```text
Bonsai unavailable.
Use verified fallback Z-Image instead?
```

For autonomous batch operations, the policy must be explicit in the project settings.

---

# 114. REAL ARTIFACT PATHS ONLY

The agent must never invent:

```text
C:\something\result.png
```

Use path objects returned by the actual worker.

Then:

```text
exists
→ file type
→ size
→ hash
```

before presenting the path to the user.

---

# 115. LOGICAL VS REAL AGENTS

Logical subagents are prompts/tools over a shared runtime.

Real concurrent model processes are used only when resource telemetry proves they are safe.

Default:

```text
one heavy VLM/LLM inference
one heavy generative GPU job
```

at a time on the target hardware.

---

# 116. INFINITE / ENDLESS RUN MODE

`movieforge run --until-complete` and controlled batch modes may execute long workflows.

Requirements:

```text
checkpointing
heartbeat
lease renewal
periodic save
bounded retries
memory cleanup
worker restart
artifact deduplication
```

Never implement an endless loop without a persisted stop condition.

Allow:

```text
stop after job
stop after scene
stop after render
stop now
pause
resume
```

---

# 117. ENDLESS BATCH SAFETY

If the system has been running for an unexpectedly long time without progress:

```text
detect stalled job
→ capture diagnostics
→ attempt one controlled recovery
→ if still stalled, mark blocked
```

Do not let a frozen backend consume a machine indefinitely.

---

# 118. PROJECT SAVE / LOAD TEST

Test:

```text
create project
→ create assets
→ save
→ close app
→ reopen
→ load
→ verify state
```

Then test after simulated crash.

Project must retain:

```text
story
assets
versions
jobs
timeline
model revisions
```

---

# 119. EXPORT / IMPORT TEST

Export a sample project.

Import into a clean directory.

Verify:

```text
database
assets
references
Blender scene links
artifact hashes
```

No absolute user-specific paths may be required after relocation unless documented and repaired automatically.

---

# 120. RELEASE DOCUMENTATION CHECK

Before release:

```text
README matches actual CLI
README matches actual supported OS
README matches actual backend status
model URLs resolve
model revisions match lock
SHA256 files verify
screenshots are real
known limitations are current
```

Use automated link checking and manual review.

---

# 121. DEVELOPMENT PHASES

## Phase 0 — Empty repository

Deliver:

```text
repo skeleton
GEMINI.md
README
LICENSE
Git hooks
CI skeleton
```

Tests: Git integrity, lint config, CI syntax.

## Phase 1 — Foundation

Deliver:

```text
project DB
artifact manager
job DB
supervisor
CLI
start/stop
```

Tests: pure unit + crash recovery.

## Phase 2 — Hardware

Deliver:

```text
Vulkan probe
RAM/GPU telemetry
hardware profile
benchmark framework
```

Tests: real local device.

## Phase 3 — Model Manager

Deliver:

```text
HF download
lock files
SHA256
staging
promotion
verify
```

Tests: download resume/corruption/hash.

## Phase 4 — llama.cpp Agent

Deliver:

```text
Qwen3-VL
Vulkan
server
tool calling
memory retrieval
```

Tests: real prompt + image inspection + long-context stress.

## Phase 5 — Bonsai Image Worker

Deliver:

```text
Bonsai Q2_K
T2I
I2I/edit
image validator
Vulkan certification
```

Tests: cold/warm/memory/visual.

## Phase 6 — 3D Worker

Deliver:

```text
TRELLIS Q4
image→GLB
mesh validator
turntable render
```

Tests: 512, 1024 if certified, crash recovery.

## Phase 7 — Blender

Deliver:

```text
import
scene creation
Rigify
render
VSE
```

Tests: headless scene test.

## Phase 8 — Motion/Cinematography

Deliver:

```text
action library
motion composition
mocap route
camera
lighting
FX
```

Tests: pose/motion/camera/FX golden tests.

## Phase 9 — Audio

Deliver:

```text
Whisper
CosyVoice
ACE-Step
lipsync
```

Tests: real WAV generation/transcription/mix.

## Phase 10 — Timeline

Deliver:

```text
storyboard
edit
VSE sync
```

Tests: deterministic timeline transformations.

## Phase 11 — Visual QA

Deliver:

```text
frame sampler
contact sheets
visual regression
VLM inspection
```

Tests: known-bad fixture detection.

## Phase 12 — Self-healing

Deliver:

```text
OOM recovery
worker restart
crash recovery
artifact quarantine
```

Tests: deliberate failure injection.

## Phase 13 — Full UI/UX

Deliver:

```text
desktop app
3D viewport
image editor
storyboard
timeline
assistant
QA panel
```

Tests: Playwright or equivalent UI automation + manual review.

## Phase 14 — Full mini-film

Deliver a real 20–60 second 1080p mini-film through the complete pipeline.

## Phase 15 — Soak/release

Deliver:

```text
multi-hour soak
clean-room install
Windows package
Linux package
GitHub release
HF Space
```

---

# 122. AGENTIC DEVELOPMENT LOOP

The coding agent must work in small validated increments.

For each task:

```text
READ
→ INSPECT
→ PLAN
→ EDIT
→ FORMAT
→ STATIC CHECK
→ UNIT TEST
→ BUILD
→ REAL SMOKE
→ VISUAL CHECK
→ REGRESSION
→ UPDATE DOCS
→ COMMIT
```

The agent may batch mechanical tasks, but must not batch away verification.

---

# 123. CHANGE IMPACT ANALYSIS

Before modifying a core contract, identify:

```text
callers
workers
UI consumers
CLI consumers
tests
README
schemas
```

After modification, run targeted and regression tests.

---

# 124. BRANCH/COMMIT STRATEGY

Prefer small, logical commits:

```text
feat(core): project schema
feat(engine): durable job queue
feat(image): Bonsai worker
fix(trellis): Vulkan resource cleanup
```

Never use a giant final commit hiding untested subsystems.

---

# 125. TAGS / RELEASES

Use signed tags if signing infrastructure is available; otherwise use immutable GitHub tag/release plus SHA256 checksums.

Each stable release includes:

```text
source tag
build artifacts
checksums
verification report
known limitations
model lock snapshot
```

---

# 126. STABLE RELEASE DEFINITION

A release is STABLE only if:

```text
CI GREEN
Windows build PASS
Linux build PASS
hardware certification PASS for claimed Vulkan targets
Bonsai real smoke PASS
TRELLIS real smoke PASS if listed as supported
Blender headless PASS
project save/load PASS
recovery tests PASS
golden suite PASS
stress suite PASS
clean-room install PASS
SHA256 verification PASS
README verification PASS
HF Space PASS if published
```

Anything else is not stable.

---

# 127. GREEN DEFINITION

`GREEN` means every mandatory check has a machine-readable evidence record.

Required evidence folder:

```text
artifacts/verification/<version>/
├── environment.json
├── model-lock.json
├── checksums.txt
├── unit.json
├── integration.json
├── e2e.json
├── stress.json
├── soak.json
├── visual/
├── logs/
└── release.json
```

Never claim green based on a terminal screenshot or memory.

---

# 128. VISUAL BUILD STATUS

The UI must expose:

```text
Backend status
Model status
GPU/RAM status
Queue status
Active job
Artifact status
QA status
```

Example:

```text
IMAGE ENGINE   READY
TRELLIS        VERIFIED
BLENDER        READY
AGENT          READY
AUDIO          EXPERIMENTAL
```

These labels come from verification state, not hard-coded UI text.

---

# 129. MODEL CACHE HOUSEKEEPING

Implement:

```text
cache size limit
LRU-ish eviction
model pinning
project-active model protection
orphan cache cleanup
```

Never evict a model currently required by a running job.

---

# 130. HDD SAFETY

Never write thousands of tiny temporary files to the project directory during generation.

Use:

```text
runtime/tmp
cache/tmp
staging
```

and atomically promote completed artifacts.

Periodically compact logs and cache indexes.

---

# 131. NETWORK SAFETY

Model downloader must support:

```text
resume
retry
backoff
checksum
rate-limiting
```

Network failures must not corrupt active model files.

After a network error, verify the partial file before resuming or restarting.

---

# 132. OFFLINE-FIRST MODE

After models are downloaded, the local product should run without Internet for all features that do not inherently require external services.

`movieforge doctor --offline` must verify local readiness.

---

# 133. NO CLOUD DEPENDENCY IN CORE

The core application must not require:

```text
OpenAI API
Google API
Anthropic API
remote rendering
cloud storage
```

for the local workflow.

Cloud adapters may be optional plugins.

---

# 134. USER DATA PRIVACY

Projects and generated media remain local by default.

Do not upload project media automatically.

The HF Space demo is separate and follows its own runtime storage policy.

---

# 135. SECURITY

Agent tools must be allow-listed.

Do not expose unrestricted shell execution to the master agent.

Use typed operations for destructive actions.

Potentially destructive operations require either:

```text
explicit user confirmation
```

or an explicitly configured autonomous policy that permits the action.

---

# 136. SAFE SHELL EXECUTION

The agent may invoke predefined commands through command adapters.

Avoid direct arbitrary command concatenation.

Validate paths against allowed project/runtime roots.

Never accept a model-generated absolute path for deletion without validation.

---

# 137. UI AUTOMATION TESTS

Use an external UI automation stack such as Playwright for web surfaces and appropriate Tauri automation for desktop-critical paths.

Test:

```text
launch
create project
open project
generate request
show job
cancel job
inspect artifact
save
close
reopen
```

---

# 138. ACCESSIBILITY

The production UI should provide:

```text
keyboard navigation
visible focus
usable contrast
status text
non-color-only status indicators
```

---

# 139. INTERNATIONALIZATION

The UI architecture should allow:

```text
DE
EN
```

from the start.

The model/agent language follows the project/user language setting.

---

# 140. PERFORMANCE BUDGETS

UI:

```text
no blocking model calls on UI thread
```

Backend:

```text
one event stream
bounded queues
bounded worker concurrency
```

Disk:

```text
prefer sequential reads where possible
```

Memory:

```text
always leave OS reserve
```

---

# 141. FAILURE EVIDENCE

Every final failure report contains:

```text
what failed
where it failed
exact command/tool
exit code
relevant log excerpt
model revision
resource snapshot
what was attempted
what was changed
why it remains blocked
```

Never output only `something went wrong`.

---

# 142. AGENT FINAL REPORT FORMAT

At the end of a major build phase:

```text
PHASE: <name>
STATUS: PASS | PARTIAL | BLOCKED

IMPLEMENTED:
- ...

VERIFIED:
- ...

REAL BACKENDS TESTED:
- ...

EXTERNAL CHECKERS:
- ...

STRESS TESTS:
- ...

KNOWN LIMITATIONS:
- ...

ARTIFACTS:
- ...

NEXT PHASE:
- ...
```

No invented metrics.

---

# 143. FIRST BOOT ORDER

After the code exists, `start.bat` should approximately do:

```text
validate environment
→ load config
→ start supervisor
→ start API
→ start scheduler
→ probe resources
→ verify local model registry
→ start agent if available
→ start UI
→ report READY
```

Do not start every heavy model eagerly.

---

# 144. DEFAULT MODEL WARMING

Warm only:

```text
agent model
```

if the hardware benchmark says it is safe.

Heavy generators:

```text
Bonsai
TRELLIS
```

remain on-demand.

---

# 145. FINAL PRODUCT EXPERIENCE

A normal user should be able to:

1. run `start.bat`,
2. open the local UI,
3. create a project,
4. describe a film idea,
5. collaborate with the agent,
6. generate characters and references,
7. convert approved references to 3D,
8. rig and animate them,
9. arrange cameras/lights/FX,
10. create dialogue/music,
11. edit the timeline,
12. inspect QA,
13. render 1080p,
14. reopen the project later and continue.

The same project remains accessible through the CLI for automation.

---

# 146. COMPLETE PRODUCT DEMO SCENARIO

A final demo should show:

```text
"Create a 30 second sci-fi scene about a small maintenance robot searching a rainy station."
```

Agent creates:

```text
story
→ robot character
→ station location
→ storyboard
```

Then:

```text
Bonsai
→ robot reference
→ station references
```

Then:

```text
background removal
→ TRELLIS
→ GLB
```

Then:

```text
Blender
→ Rigify
→ motion
→ camera
→ rain
→ lighting
```

Then:

```text
CosyVoice
→ dialogue
ACE-Step
→ music
```

Then:

```text
VSE
→ edit
→ QA
→ 1080p
```

The demo must use real artifacts and be reproducible from a clean installation.

---

# 147. WHAT COUNTS AS "DONE"

For the full product:

```text
[ ] repository builds
[ ] local app starts
[ ] start.bat works
[ ] stop.bat works
[ ] Linux scripts work
[ ] doctor works
[ ] model manager works
[ ] SHA256 verification works
[ ] project create/save/load works
[ ] autosave works
[ ] recovery works
[ ] scheduler works
[ ] resource manager works
[ ] Bonsai real generation works on claimed local targets
[ ] image validation works
[ ] image editing works if backend certified
[ ] 3D generation works on claimed targets
[ ] GLB validation works
[ ] Blender import works
[ ] Rigify automation works
[ ] motion library works
[ ] camera system works
[ ] lighting system works
[ ] FX system works
[ ] STT works
[ ] TTS works or is clearly marked unsupported/experimental
[ ] music works or is clearly marked unsupported/experimental
[ ] timeline works
[ ] 1080p render works
[ ] QA works
[ ] self-healing tested
[ ] stress tests pass
[ ] soak test pass
[ ] UI automation pass
[ ] documentation accurate
[ ] GitHub workflows green
[ ] release package installs cleanly
[ ] SHA256 verified
[ ] Git tag/release created
[ ] HF Space works if published
```

---

# 148. THE AGENT MUST NOT STOP AFTER WRITING CODE

After implementing a component, the agent MUST actually run the available validators and tests.

If a test fails, it must diagnose and repair the code before moving on, within a bounded retry strategy.

It must not leave obvious red tests while continuing to implement unrelated layers.

---

# 149. THE AGENT MUST NOT CLAIM A BACKEND IS VERIFIED BY README TEXT

A README/model card is evidence of intended support, not proof that the exact pinned build works on this exact machine.

For local release status, the decisive evidence is:

```text
actual build
+
actual model
+
actual Vulkan device
+
actual output
+
actual validation
```

---

# 150. THE AGENT MUST DISTINGUISH FOUR TRUTHS

Every capability has four independent statuses:

```text
UPSTREAM_SUPPORTED
LOCAL_BUILT
LOCAL_RUNTIME_VERIFIED
RELEASE_CERTIFIED
```

Example:

```text
TRELLIS Vulkan
UPSTREAM_SUPPORTED = YES
LOCAL_BUILT = YES
LOCAL_RUNTIME_VERIFIED = NO
RELEASE_CERTIFIED = NO
```

Until all required states are true, do not label it `production-ready`.

---

# 151. FINAL AUTONOMOUS EXECUTION CONTRACT

From an empty directory, the agent must:

```text
1. inspect environment
2. create repository
3. create architecture
4. create tests before high-risk backend integration
5. pull/compile real dependencies
6. discover and pin model revisions
7. verify model files with SHA256
8. build headless backends
9. build project state system
10. build scheduler/resource manager
11. certify Bonsai Vulkan path
12. certify TRELLIS Vulkan path
13. certify Blender bridge
14. build image→3D→rig pipeline
15. build motion/camera/light/FX
16. build audio
17. build timeline
18. build VLM visual QA
19. build self-healing
20. build desktop UI
21. run E2E mini-film
22. run stress/failure/soak tests
23. fix all failures that are within scope
24. run full external checker suite
25. update README and docs from actual evidence
26. build clean Windows and Linux packages
27. hash release artifacts
28. run clean-room installation tests
29. create GitHub tags/releases
30. deploy/verify HF Space
31. produce final verification report
```

The agent must never replace real implementation with a mock to satisfy a checklist.

The final report must tell the truth about every capability.

---

# 152. CURRENT UPSTREAM REFERENCE INDEX

Use primary sources first and re-check at execution time:

- Aatricks Bonsai FLUX.2 Klein GGUF: https://huggingface.co/Aatricks/bonsai-image-ternary-4B-FLUX2-klein-GGUF
- stable-diffusion.cpp FLUX.2 docs: https://github.com/leejet/stable-diffusion.cpp/tree/master/docs
- stable-diffusion.cpp repository: https://github.com/leejet/stable-diffusion.cpp
- trellis.cpp: https://github.com/pwilkin/trellis.cpp
- llama.cpp: https://github.com/ggml-org/llama.cpp
- whisper.cpp: https://github.com/ggml-org/whisper.cpp
- Blender: https://www.blender.org/
- Hugging Face Hub CLI/API: https://huggingface.co/docs/huggingface_hub/
- Hugging Face Spaces/ZeroGPU: https://huggingface.co/docs/hub/spaces-zerogpu
- Gradio: https://www.gradio.app/
- GitHub Actions: https://docs.github.com/en/actions
- Ruff: https://github.com/astral-sh/ruff
- PSScriptAnalyzer: https://github.com/PowerShell/PSScriptAnalyzer
- actionlint: https://github.com/rhysd/actionlint
- zizmor: https://github.com/woodruffw/zizmor
- gitleaks: https://github.com/gitleaks/gitleaks
- Playwright: https://playwright.dev/

When these sources change, the implementation must follow the new verified interface instead of blindly using old examples in this file.

---

# 153. FINAL PRINCIPLE

**Build the real thing. Measure it. Inspect it. Test it. Break it. Repair it. Repeat.**

Never let a green-looking UI, a successful subprocess exit code, a model card, a mock, or an LLM assertion substitute for actual evidence.

The finished product is not a collection of demos.

It is one persistent, editable, recoverable local film-production environment whose models are interchangeable behind typed contracts, whose resources are scheduled intelligently, whose outputs are cryptographically identifiable, whose failures are recoverable, whose UI is usable by hand, and whose public demo is clearly separated from the local canonical runtime.

