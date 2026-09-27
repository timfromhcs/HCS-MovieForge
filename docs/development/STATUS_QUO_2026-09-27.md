# HCS MovieForge — Ehrliche Bestandsaufnahme (IST-Stand)

**Stichtag:** 2026-09-27
**Prüfer:** OpenCode-Agent (Lokalausführung, kein Web-Raten)
**Quellen:** `GEMINI.md` (4552 Zeilen, §§0–153), `README.md`, Git-Historie, `artifacts/verification/0.1.0/step*.json` (A–G), `models/locks/model-lock.json`, Live-Runs (`doctor`, `pytest`), Verzeichnis-Scans.
**Methode:** Jede Aussage unten ist auf eine Datei, einen Log-Eintrag oder einen ausgeführten Befehl zurückführbar. Wo kein Beleg existiert, steht explizit `UNVERIFIED` / `FEHLT`.

---

## 1. Kurzfazit (ehrlich, in einem Absatz)

Das Repo ist **kein leeres Skeleton mehr und kein fertiges Produkt**. Es ist ein **funktionsfähiger Headless-Kern mit echt verifizierten Backends** (Bonsai-Bild, TRELLIS-3D, Blender 5.1, Whisper, Piper-TTS, FFmpeg-1080p, Scheduler, Supervisor, API+WS, CLI) auf genau einer Maschine (Win11, Ryzen 7 7735HS, Radeon 680M, Vulkan 1.4.315). Der mini-filmartige Proof (`minifilm_spark7_final_1080p`, 3,56 s, 1920×1080, QA-passed) existiert, ist aber **kein §73-Vollfilm** (2 Charaktere, 6 Shots, 20–60 s). **Nicht existent** sind: Desktop-UI (Tauri-Skeleton leer), CosyVoice-/ACE-Step-Worker (nur STATUS.md, ehrlich `EXPERIMENTAL`), Humanoid-Rig (Gate blockt ehrlich), Phonem-Lipsync (nur RMS-Baseline), `docs/`-Inhalte (alle 5 Ordner leer), `scripts/{build,models,recovery,release}` (leer), `agent/{memory,planners,policies,prompts,subagents}` (leer), `tests/{fixtures,e2e,external}` (leer), Release-Artefakte (kein Tag, kein Portable-ZIP, kein SBOM, keine Clean-Room-Installation, kein HF-Space-Deploy). Der Arbeitsbaum ist **schmutzig** (4 modifizierte Dateien, +265 Zeilen, uncommittet) — `release verify` scheitert dadurch per Design. Korrekte Gesamt-Labels: **Core: VERIFIED LOCAL / Produkt: EXPERIMENTAL, NICHT STABLE, NICHT RELEASE, NICHT GREEN im Sinne von §127.**

---

## 2. Harte Fakten (gezählt, nicht geschätzt)

| Bereich | Befund |
|---|---|
| Git | Branch `master`, HEAD `7aabf1c`, **9 Commits, alle vom 2026-09-27**. Arbeitsbaum **dirty**: `M agent/director/master_agent.py` (+251), `M agent/tools/registry.py`, `M apps/cli/src/main.py` (`--full`-Flag), `M integrations/trellis_cpp/worker.py` (Seed-Param). `git diff --check`: sauber (keine Whitespace-Fehler). |
| Live-Run 27.09. | `python apps/cli/src/main.py doctor` → **LOCAL CORE: READY** (15/15: OS, Git 2.54, Python 3.14.6, Node 22, Rust 1.96, CMake, Ninja, FFmpeg, Blender 5.1.2, Vulkan AMD 1.4.315, sd.cpp master-920, trellis 0.8.1, llama b11205, whisper b5130, piper 1.8.0, 7 Modelle auf Platte). |
| Live-Run Tests | `pytest tests/unit tests/integration` → **46 passed** (8,14 s). Entspricht stepG-Aussage (39 Unit + 7 API). Golden/Stress/Soak-Suites wurden heute NICHT erneut live nachgelaufen (nur Evidenz-JSONs). |
| Python-Code | ~60 `.py`-Dateien mit echtem Inhalt (CLI 791 Zeilen, Registry 774 Zeilen, Director 438 Zeilen, Worker je 125–237 Zeilen, Validatoren, Scheduler 221 Zeilen, Supervisor 181 Zeilen). `ruff`/`mypy`-Binaries auf diesem Host **nicht im PATH** (Befehl nicht gefunden) — frühere PASS-Aussagen stammen aus Evidenz-JSONs, heute nicht reproduziert. |
| TS/Rust | **0 Zeilen**: `apps/desktop/src/` leer, `apps/desktop/src-tauri/src/` leer. Keine `.ts/.tsx/.rs`-Datei im ganzen Repo. `package.json`/`Cargo.toml`/`CMakeLists.txt` existieren, beschreiben aber leere Targets. |
| Modelle auf Platte | 7× `VERIFIED_ACTIVE` mit SHA256 im Lock: Bonsai Q2_K (1,36 GB), VAE flux2 (336 MB), Qwen3-TE 4B Q2_K (1,66 GB), TRELLIS.2 Q4 (7 GGUF-Files), Qwen3-VL-8B Q4_K_M + mmproj-F16 (zus. ~6,2 GB), Whisper-base (147 MB), Piper-lessac (ONNX+JSON). **Nicht** gelockt: CosyVoice, ACE-Step (`UNPINNED_EXPERIMENTAL`, `files=[]`). `models/staging/` leer. |
| Binaries | `bin/{llama-cpp,stable-diffusion-cpp,trellis-cpp,whisper-cpp}` mit echten `.exe`+`ggml-vulkan.dll`. `bin/{acestep-cpp,cosyvoice}` **FEHLT**. |
| Runtime-Belege | `runtime/` enthält echte Artefakte: `test_bonsai_robot.png` (190 KB), `test_trellis_output.glb` (5,2 MB), `test_shape.glb` (10 MB), `test_timeline_assembly.mp4`, `test_piper_dialogue.wav`, `test_render_turntable.png`, `hardware-profile.json` (20 GB RAM, UMA, HDD=true, Budget 14629 MB), `supervisor.log`, `logs/api.log`. `cache/` leer. `logs/` (Root) leer. |
| Verifikation | `artifacts/verification/0.1.0/step{A..G}.json` vorhanden (A 2002 B … G 1187 B). Inhalte siehe §4. **Kein** `artifacts/verification/<version>/`-Ordner im Sinne von §127 (mit unit.json/integration.json/e2e.json/stress.json/soak.json/visual/logs/release.json) — die step-Dateien sind Vorstufen, kein GREEN-Beleg. |
| Dist | Nur `dist/minifilm_spark7-export.zip` (890 KB). **Kein** `HCS-MovieForge-windows-x64-portable.zip`, kein Linux-Tarball, keine `checksums.txt`, kein SBOM. |

---

## 3. Phasen-Ampel (§121: Phase 0–15)

| Phase | SOLL (Kurz) | IST (Beleg) | Ampel |
|---|---|---|---|
| 0 Empty repo | Skeleton, GEMINI, README, LICENSE, Hooks, CI | Vorhanden (9 Commits). ABER: `docs/` leer, `scripts/{build,models,recovery,release}` leer. CI-Workflows nur 20–30-Zeilen-Skelette. | 🟡 PARTIAL |
| 1 Foundation | Projekt-DB, Artifact-Manager, Job-DB, Supervisor, CLI, Start/Stop | **Vorhanden + live PASS**: `doctor` READY, `pytest` 46 PASS, `server start/stop`, `project open/save/export`, `render preview/final`. | 🟢 PASS |
| 2 Hardware | Vulkan-Probe, Telemetrie, Profil, Benchmark | **Vorhanden**: `hardware-profile.json`, `benchmark --save/--hdd`. ABER Messung ehrlich eingeschränkt: Seq-Read 3107 MB/s = Page-Cache (kein Spindel-Wert), Cold/Warm 0,02 s = alles gecacht (echter Cold-Wert UNKNOWN). | 🟡 PASS mit Einschränkung |
| 3 Model-Manager | HF-Download, Locks, SHA256, Staging, Promotion | **Vorhanden für 7 Modelle** (Lock + Hashes + `doctor --offline`). CosyVoice/ACE-Step ehrlich ungelockt. | 🟢 PASS (Scope: 7/9) |
| 4 llama/Qwen-Agent | Qwen3-VL Vulkan, Server, Tool-Calling, Memory-Retrieval | **Teilweise**: Harness erst WEAK (Greeting-Leakage), nach Jinja-Fix PASS 8,98 s (stepD). Registry + Director vorhanden. **FEHLT**: Langkontext-Stress, Agent-Memory mit FTS5 (`agent/memory/` leer), `planners/prompts/policies/subagents` leer. | 🟡 PARTIAL |
| 5 Bonsai-Bild | Q2_K T2I/I2I, Validator, Vulkan-Zertifizierung | **Verifiziert**: 195,93 s Vulkan-Gen, `runtime/test_bonsai_robot.png` real. Validator + QA vorhanden. I2I/Edit-Pfad im Worker deklariert, Zertifizierungstiefe (Masken-Edit) nicht separat belegt. | 🟢 PASS (T2I; Edit: PARTIAL) |
| 6 3D-Worker | TRELLIS Q4, Bild→GLB, Mesh-Validator, Turntable | **Verifiziert**: 415,04 s, V=163744/F=272540, `test_trellis_output.glb` real + Validator + Turntable. AMD-Vulkan-Risiko per STATUS bekannt. 1024er-Profil nicht separat zertifiziert. | 🟢 PASS (512; 1024: UNVERIFIED) |
| 7 Blender | Import, Szene, Rigify, Render, VSE | **Verifiziert**: 5.1.2 headless, Import+Turntable+Rig-Gate+Pose-Sheet+VSE-Assemble. Rigify-`generate/bind` am Humanoiden **UNVERIFIED** (kein humanoides Fixture). | 🟡 PASS (ohne Humanoid-Rig) |
| 8 Motion/Cine | Action-Lib, Komposition, Mocap, Kamera/Licht/FX | **Teilweise**: 15 Kamera- + 11 Licht- + 12 FX-Presets + 18 Actions + 14-Pose-Matrix + Motion-Parser vorhanden, Camera/FX/Motion-Golden PASS. Mocap/Text-to-Motion ehrlich EXPERIMENTAL. Face-Rig fehlt. | 🟡 PARTIAL |
| 9 Audio | Whisper, CosyVoice, ACE-Step, Lipsync | **Gespalten**: Whisper PASS, Piper PASS (aktive TTS-Lane). CosyVoice: nur STATUS.md (CPU-Route, Vulkan NOT working upstream) — **kein Worker, kein Build, kein Staging**. ACE-Step: nur STATUS.md (`music.generate` ehrlich UNAVAILABLE) — **kein Worker, kein Build**. Lipsync: RMS-Baseline (SIL/CLOSED/MID/OPEN), **kein Phonem/Visem-exakt**. | 🔴 Audio-Kern (STT+Piper+Lipsync-Baseline): PASS; CosyVoice/ACE: NICHT IMPLEMENTIERT |
| 10 Timeline | Storyboard, Edit, VSE-Sync | **Vorhanden**: frame-exakte Math (split/trim/move/speed/fade), VSE-Assemble, `storyboard.reorder`. Timeline-UI-Handles fehlen (Phase-G-Arbeit). | 🟢 PASS (Headless) |
| 11 Visuelle QA | Sampler, Contact-Sheets, Regression, VLM | **Vorhanden (programmatisch)**: Sampling, Known-Bad-Detection, Sheets, Histogramm-Distanz, Movie-Gate, Continuity. VLM-Review optional (korrekt). Untertitel nur strukturell. | 🟢 PASS (ohne VLM-Pflicht) |
| 12 Self-Healing | OOM-Recovery, Restart, Crash-Recovery, Quarantäne | **Teilweise**: OOM-Leiter (Single-Pass), Supervisor-Backoff (max 30 s, 300-s-Fenster→DISABLED), Cancel-2-Step, Stress E/F/G/H/C/D + HDD-Benchmark + 60-s-Soak: PASS. **NICHT gelaufen**: Stress A (50 Zyklen, Tage GPU-Zeit), Stress B (absichtlicher Speicherdruck, Host-Risiko), Soak mehrstündig (§74-I). Turntable-Fallback (Bezier) mit Warnung. | 🟡 PARTIAL |
| 13 Full UI/UX | Desktop-App, Viewport, Editoren, Assistant, QA-Panel | **NICHT vorhanden**: Desktop = nur README + 2 leere `src/`-Ordner. API+WS vorhanden, Space-Demo nur import-verifiziert. Kein Playwright, keine Screenshots, kein i18n (DE/EN), kein A11y-Audit. | 🔴 NICHT IMPLEMENTIERT |
| 14 Mini-Film | Realer 20–60-s-1080p-Film (§73) | **Mini-Proof vorhanden, Vollfilm fehlt**: `minifilm_spark7_final_1080p.mp4` 3,56 s + QA-passed + Export-ZIP. §73 verlangt 2 Charaktere/1 Location/1 Prop/3 Szenen/6 Shots/20–60 s mit allen Backends — das ist **nicht belegt**. Uncommittete `run_full_minifilm` im Director deutet laufende Arbeit an. | 🟡 PROOF, kein §73-Film |
| 15 Soak/Release | Mehrstunden-Soak, Clean-Room, Pakete, Release, Space | **Nichts davon belegt**: kein Mehrstunden-Soak, kein Clean-Room-Test, keine Portable-Pakete, kein Tag, kein GitHub-Release, kein Space-Deploy-Test, kein SBOM. | 🔴 NICHT IMPLEMENTIERT |

---

## 4. Was die step-JSONs wirklich belegen (und was nicht)

- **A (Backends):** Alle 7 Harnesse PASS (Bonsai 195 s, Trellis 415 s, Qwen WEAK-aber-exit-0, Blender 3,2 s, FFmpeg 0,5 s, Whisper 1,6 s, Piper 6,6 s). Statik: ruff/mypy/pytest PASS (damals). Limit ehrlich notiert (Qwen-Template, fehlende Scanner, Full-mypy pending).
- **B (Foundation):** 20/20 pytest, `render preview` PASS, HDD-Zahlen ehrlich als cache-verfälscht markiert. `render final` damals nur via Produce-Pipeline, `release verify` scheitert bei dirty tree (by design).
- **C (Motion/Cine):** 28/28 pytest, Rig-Gate ehrlich `BLOCKED_NON_HUMANOID` (kein Fake-Rig), Kamera/FX/Pose-Sheet PASS. Humanoid-`generate` UNVERIFIED.
- **D (Audio):** Qwen-Fix (Jinja + Filter) 8,98 s PASS. Piper aktiv, Cosy/ACE als EXPERIMENTAL mit Upstream-Fakten dokumentiert. Lipsync-Baseline PASS.
- **E (Timeline/QA):** 42/42 pytest, `render final` 1080p + `qa.movie passed=true` (24 fps, Drift 0,02 s). Visual-QA-Sheet mit ehrlich korrigiertem Threshold.
- **F (Hardening):** 48/48 pytest (inkl. Stress + 60-s-Soak + echter Blender-Kill). A/B-SoBund Mehrstunden-Soak ehrlich als NICHT gelaufen markiert.
- **G (API/UI):** 46/46 pytest, Live-Zyklus `server start → /health → stop` PASS. Desktop/Space ehrlich als PENDING markiert.

**Gesamt:** Die JSONs sind glaubwürdige Teilbelege, aber **kein §127-GREEN** (dafür fehlen `unit/integration/e2e/stress/soak/visual/logs/release.json` + Checksums + Model-Lock-Snapshot im geforderten Ordnerformat).

---

## 5. DONE-Checkliste (§147) — Kästchen für Kästchen

- [x] repository builds (Python-Core; TS/Rust/C-Targets leer, nichts zu brechen)
- [x] local app starts (Supervisor + API via `start.ps1`/`server start`, live belegt in G)
- [x] start.bat works (Wrapper → ps1, strukturell ok)
- [x] stop.bat works (nur getrackte PIDs, strukturell ok)
- [~] Linux scripts work (inhaltlich korrekt, auf Win-Host nicht ausführbar → UNVERIFIED)
- [x] doctor works (15/15 READY, heute reproduziert)
- [x] model manager works (7 Modelle, Hash+Offline-Check)
- [x] SHA256 verification works (Lock + Validator + `models verify`-Pfad)
- [x] project create/save/load works (Manager + Snapshots)
- [x] autosave works (Snapshot-Scheduling im Manager; Crash-Test in F)
- [x] recovery works (OOM-Leiter + Startup-Recovery + Blender-Kill-Test)
- [x] scheduler works (WAL + Lokalität + Heavy-Limit; 50-Zyklen-Churn fehlt)
- [x] resource manager works (UMA-Budgets, Leases; Cold-Messung cache-verfälscht)
- [x] Bonsai real generation works (195-s-Vulkan-PNG)
- [x] image validation works
- [~] image editing works if backend certified (Worker deklariert, separate Masken-Zertifizierung fehlt)
- [x] 3D generation works (415-s-GLB; 1024-Profil unverified)
- [x] GLB validation works
- [x] Blender import works
- [ ] Rigify automation works (Gate blockt ehrlich; Humanoid-Generate UNVERIFIED)
- [~] motion library works (Lib + Parser + Golden; Face/Mocap fehlen)
- [x] camera system works (Presets + Applier + Golden)
- [x] lighting system works
- [x] FX system works (Smoke/Fire nur configured-preview)
- [x] STT works (Whisper-Harness)
- [~] TTS works or is clearly marked unsupported/experimental (Piper PASS als aktive Lane — Kriterium formal erfüllt; CosyVoice EXPERIMENTAL ohne Worker)
- [~] music works or is clearly marked unsupported/experimental (ehrlich UNAVAILABLE — formal erfüllt; kein Worker)
- [x] timeline works (headless; UI-Editor fehlt)
- [x] 1080p render works (3,56-s-Proof; 20–60-s-Film fehlt)
- [x] QA works (programmatisch; VLM optional)
- [~] self-healing tested (E/F/G/H/C/D ja; A/B-Mehrstunden nein)
- [ ] stress tests pass (vollständig im Sinne von §74: nein)
- [ ] soak test pass (60 s ja; mehrstündig nein)
- [ ] UI automation pass (kein Playwright, keine App)
- [ ] documentation accurate (README grundsätzlich ehrlich, aber §98-Inhalte fehlen: Screenshots, Troubleshooting, Limits, Lizenzen je Modell; `docs/` leer)
- [~] GitHub workflows green (Skelette vorhanden, Live-Status UNKNOWN — heute nicht geprüft)
- [ ] release package installs cleanly (kein Paket, kein Clean-Room-Test)
- [ ] SHA256 verified (für Release-Artefakte: keine Artefakte)
- [ ] Git tag/release created (kein Tag)
- [ ] HF Space works if published (nur import-verifiziert)

**Lesart:** 24× erfüllt, 6× teilweise/formal-erfüllt-aber-unvollständig, 9× offen. Das ist ein starker Kern, aber keine Release-Reife.

---

## 6. Vier Wahrheiten (§150) — pro Fähigkeit

| Fähigkeit | UPSTREAM_SUPPORTED | LOCAL_BUILT | LOCAL_RUNTIME_VERIFIED | RELEASE_CERTIFIED |
|---|---|---|---|---|
| Bonsai/Q2_K Vulkan | YES (sd.cpp FLUX.2-Pfad) | YES (master-920) | YES (195-s-PNG) | NO |
| TRELLIS.2 Q4 Vulkan | YES (trellis.cpp) | YES (0.8.1) | YES (415-s-GLB, 512) | NO |
| Qwen3-VL Vulkan | YES (llama.cpp) | YES (b11205) | WEAK→FIXED (8,98-s-Satz) | NO |
| Blender 5.1 headless | YES | YES (System-Blender) | YES | NO |
| Whisper CPU | YES | YES (b5130) | YES | NO |
| Piper TTS CPU | YES | YES (1.8.0) | YES | NO |
| CosyVoice | PARTIAL (CPU ja, Vulkan nein) | NO | NO | NO |
| ACE-Step | PARTIAL (Vulkan-Build existiert upstream, lokal nicht gebaut) | NO | NO | NO |
| Rigify-Humanoid | YES (Blender) | YES | NO (kein Fixture) | NO |
| Desktop-Tauri | YES (Tauri existiert) | NO | NO | NO |
| HF-Space | YES (Gradio/ZeroGPU) | NO (nur `app.py`) | NO (nur Import) | NO |

**Regel:** Solange eine Spalte NO ist, kein `production-ready` (§150). Aktuell ist keine einzige Zeile vollständig YES.

---

## 7. Ehrlich stark vs. ehrlich schwach

**Stark (bitte nicht kaputtmachen):** Keine Fake-Erfolge (Rig-Gate blockt, Music UNAVAILABLE, Qwen-Schwäche dokumentiert + gefixt, HDD-Zahlen als cache-verfälscht markiert). Echte Binaries + echte Gewichte + echte Hashes. Supervisor tötet nur eigene Kinder. Tests prüfen echte Artefakte (Pfad existiert, Größe, Metadaten). Commit-Historie kleinteilig mit Evidenz-JSONs.

**Schwach (Reihenfolge = Plan-Priorität):** (1) Dirty Tree — 4 Dateien uncommittet. (2) `docs/` total leer. (3) Desktop-UI nicht existent. (4) CosyVoice/ACE-Step ohne Worker. (5) Humanoid-Fixture fehlt → Rigify-Lücke. (6) Lipsync nur Baseline. (7) Stress-A/B + Mehrstunden-Soak fehlen. (8) §73-Vollfilm fehlt. (9) Kein Release (Paket/Tag/Clean-Room/SBOM). (10) Externe Scanner (PSScriptAnalyzer, shellcheck, actionlint, zizmor, gitleaks, lychee, eslint/tsc/cargo) auf diesem Host unverified/fehlend. (11) `scripts/{build,models,recovery,release}` + `agent/{memory,planners,prompts,policies,subagents}` + `tests/{fixtures,e2e,external}` leer. (12) README ohne Screenshots/Troubleshooting/Modell-Lizenzmatrix.

---

## 8. Reproduktionsbefehle (Stand 2026-09-27, Win11-PS)

```powershell
python apps/cli/src/main.py doctor
python -m pytest tests/unit tests/integration -q   # heute: 46 passed
git status --short; git log --oneline -9; git diff --check
Get-ChildItem docs -Recurse -Force
Get-ChildItem apps/desktop/src, apps/desktop/src-tauri/src -Force
Get-ChildItem models/locks; Get-Content models/locks/model-lock.json
Get-ChildItem artifacts/verification/0.1.0
Get-ChildItem bin; Get-ChildItem dist; Get-ChildItem runtime
```

---

*Ende der Bestandsaufnahme. Weiter mit `docs/development/MASTERPLAN_ZUM_ZIEL.md`.*
