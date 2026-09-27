# HCS MovieForge — Masterplan zum Ziel (GEMINI.md §§147/151)

**Basis:** `STATUS_QUO_2026-09-27.md` (IST), `GEMINI.md` (SOLL, §§0–153).
**Zielzustand:** Alle §147-Kästchen geschlossen, §126-STABLE-Kriterien erfüllt, §127-GREEN-Evidenzordner vollständig, Arbeitsbaum sauber, Tag + Release + Space verifiziert.
**Arbeitsprinzip pro Schritt (§122):** `READ → PLAN → EDIT → FORMAT → LINT → TYPECHECK → UNIT → BUILD → REAL SMOKE → VISUAL → REGRESSION → DOCS → COMMIT`. Kein Schritt gilt als fertig ohne seinen Akzeptanzbeleg. Keine Mocks für Real-Media (§0.2). Keine erfundenen Versionen/Hashs/Flags (§19).

**Konvention:** Jeder Schritt hat *Ziel – Dateien – Kommandos – Akzeptanz – Evidenz*. Evidenz landet in `artifacts/verification/<version>/` (neu: `0.2.0/` für die Ziel-Runde).

---

## Phase 0 — Baum säubern & Baseline sichern (Voraussetzung für alles)

### Schritt 0.1 — Dirty Tree auflösen
- **Ziel:** 4 modifizierte Dateien prüfen, testen, commiten oder reverten.
- **Dateien:** `agent/director/master_agent.py` (+251, `run_full_minifilm`), `agent/tools/registry.py`, `apps/cli/src/main.py` (`--full`), `integrations/trellis_cpp/worker.py` (Seed).
- **Kommandos:**
  ```powershell
  git diff HEAD -- agent/director/master_agent.py | Out-File $env:TEMP\diff_director.txt; code $env:TEMP\diff_director.txt
  python -m pytest tests/unit tests/integration -q
  python apps/cli/src/main.py doctor
  git diff --check; git status --short
  ```
- **Akzeptanz:** Diff gelesen; alle neuen Pfade getestet (`produce --full` Trockenlauf oder Unit); `pytest` grün; danach **ein** logischer Commit pro Thema (`feat(director): full-minifilm …`, `feat(trellis): seed …`), kein Riesen-Commit (§124).
- **Evidenz:** Commit-SHAs im Plan-Protokoll.

### Schritt 0.2 — Evidenzordner 0.2.0 anlegen
- **Ziel:** §127-Struktur vorbereiten, damit ab jetzt jeder Schritt Belege ablegt.
- **Kommandos:** `New-Item -ItemType Directory -Path artifacts/verification/0.2.0/visual, artifacts/verification/0.2.0/logs`
- **Akzeptanz:** Ordner + `README.md` (Schema: environment.json, model-lock.json, checksums.txt, unit.json, integration.json, e2e.json, stress.json, soak.json, visual/, logs/, release.json).
- **Evidenz:** Ordner existiert, leer, dokumentiert.

---

## Phase A — Doku & Skript-Skelette schließen (billig, entblockt §120/§98)

### Schritt A.1 — `docs/` befüllen (minimal, aber echt)
- **Ziel:** Keine leeren Ordner mehr; jede Datei beschreibt nur Belegtes.
- **Dateien:**
  - `docs/architecture/ÜBERSICHT.md` (Kontroll-Ebene-Diagramm aus §2 + Modul-Tabelle aus Bestandsaufnahme §2)
  - `docs/backend-matrices/MATRIX.md` (Tabelle aus Bestandsaufnahme §6, Stand 2026-09-27, Hardware-Profil)
  - `docs/user-guide/ERSTE_SCHRITTE.md` (doctor → benchmark → models list → Tests → start/stop, mit echten Outputs)
  - `docs/development/AGENT_LOOP.md` (§122-Ablauf + Beispiel-Session)
  - `docs/release-notes/0.1.0-UNRELEASED.md` (ehrlich: was geht, was nicht — aus §147-Tabelle)
- **Akzeptanz:** `markdownlint-cli2` (falls installierbar, sonst manuell) + `lychee`-Linkcheck über alle URLs; keine Behauptung ohne Quelle; Screenshots erst ab Phase G.
- **Evidenz:** 5 Dateien + Lint-Protokoll in `0.2.0/logs/docs-lint.txt`.

### Schritt A.2 — `scripts/{build,models,recovery,release}` füllen oder streichen
- **Ziel:** Keine toten Ordner.
- **Dateien:** Entweder echte Skripte (`build/windows.ps1`, `models/sync.ps1`, `recovery/restore.ps1`, `release/package.ps1` — jeweils als dünne Wrapper um vorhandene CLI-Befehle) oder Ordner löschen + GEMINI-Abweichung in CHANGELOG dokumentieren.
- **Akzeptanz:** `PSScriptAnalyzer` über jede `.ps1`; `shellcheck`/`shfmt` über jede `.sh`; jeder Wrapper hat `--help` und wird im Docs-Guide aufgerufen.
- **Evidenz:** Analyzer-Protokolle.

### Schritt A.3 — Leere Agent-/Test-Ordner entscheiden
- **Ziel:** `agent/{memory,planners,prompts,policies,subagents}` und `tests/{fixtures,e2e,external}` bekommen Inhalt (Schritte C/E/F) oder eine `README.md` mit ehrlichem `PLATZHALTER — geplant für Schritt X`.
- **Akzeptanz:** Kein Ordner ohne entweder Code oder datiertes Platzhalter-README.

---

## Phase B — Externe Checker auf diesem Host verfügbar machen (§63/§64)

### Schritt B.1 — Python-Checker pinnen & laufen lassen
- **Kommandos:**
  ```powershell
  python -m pip install ruff mypy pytest pytest-cov pip-audit  # Versionen in pyproject pinnen
  python -m ruff check .; python -m ruff format --check .
  python -m mypy  # Scope: erst 25 Kern-Dateien (Stand stepB), dann erweitern
  python -m pytest tests/unit tests/integration -q
  python -m pip-audit
  ```
- **Akzeptanz:** Alle vier grün; Versionen in `pyproject.toml` + `0.2.0/logs/python-checks.txt`.
- **Evidenz:** Log + `unit.json`.

### Schritt B.2 — PS/Shell/Workflow/Secrets-Scanner
- **Kommandos:** `PSScriptAnalyzer` (alle `.ps1/.psm1`), `shellcheck`+`shfmt` (alle `.sh`), `actionlint` + `zizmor` (alle `.github/workflows`), `gitleaks detect --source .`.
- **Akzeptanz:** Null Errors (Warnings dokumentiert); falls ein Tool auf Win-Host nicht installierbar → als `UNVERIFIED (Blocker: …)` in Matrix + Release-Notes, kein Fake-PASS.
- **Evidenz:** Je ein Protokoll in `0.2.0/logs/`.

### Schritt B.3 — TS/Rust/C-Checker vorbereiten (für Phase G)
- **Ziel:** Sobald erste `.ts/.rs`-Datei landet, gelten sofort `eslint`, `prettier --check`, `tsc --noEmit`, `cargo fmt/clippy/test/build`, `cmake configure/build`, `ctest`.
- **Akzeptanz:** Toolchain-Versionen aus Upstream-Docs gepinnt (`rust-toolchain.toml`, Node-LTS), nicht aus Erinnerung (§81).

---

## Phase C — Agent-Gedächtnis & Planer (Phase 4 schließen)

### Schritt C.1 — `agent/memory` (SQLite FTS5)
- **Ziel:** Story-/Asset-/Shot-Fakten, Continuity-Constraints, Präferenzen, genehmigte/abgelehnte Generationen + Metadaten; kompakte Snapshots + Retrieval (§22).
- **Dateien:** `agent/memory/schema.sql`, `agent/memory/store.py`, `agent/memory/retrieve.py`, Tests `tests/unit/test_memory.py`.
- **Akzeptanz:** Unit (Upsert/FTS-Suche/Rerank-Stub/Re snapshot-Limit) + Integration (Director schreibt/liet über echten Projekt-DB-Pfad); keine Embedding-Pflicht.
- **Evidenz:** `pytest` + Beispiel-Snapshot in `0.2.0/logs/`.

### Schritt C.2 — `agent/{planners,prompts,policies,subagents}` minimal
- **Ziel:** Typisierte Tool-Profile je Rolle (§23: DIRECTOR…RELEASE), ein Prompt-Template-Verzeichnis mit Versionierung, Policy-Datei (autonome vs. bestätigungspflichtige Aktionen, §135), Planer (OBSERVE→…→REPORT, §24).
- **Akzeptanz:** Jede Rolle hat erlaubte Tool-Liste; destruktive Tools verlangen Confirmation-Flag (Test: Ablehnung ohne Flag).
- **Evidenz:** Policy-Tests grün.

### Schritt C.3 — Langkontext-Kalibrierung Qwen3-VL
- **Ziel:** 24K-Start bestätigen oder anpassen (§21); KV-Quantisierung benchmarken; keine 128K/256K ohne Messung.
- **Kommandos:** `scripts/test/test_qwen3_vl.ps1` in Stufen (prompt-only, image-inspect, 24K-Kontext), Telemetrie (Dauer, RAM-Peak, OOM ja/nein).
- **Akzeptanz:** Gewählte `ngl/context/kv`-Werte in Hardware-Profil persistiert (§108); Ergebnis in `benchmark`-JSON.

---

## Phase D — Bild-Pipeline vervollständigen (Phase 5-Rest)

### Schritt D.1 — I2I/Masken-Edit-Zertifizierung
- **Ziel:** Klären, ob der gepinnte sd.cpp-Build (`master-920`) Masken-Edits + Single-Image-Edit über FLUX.2-Klein-Pfad unterstützt (§27).
- **Vorgehen:** Upstream-Docs des gepinnten Commits lesen → Flags ableiten → `test_bonsai.ps1` um Edit-Fall erweitern → echter Run → Validator + Visual-Sample.
- **Akzeptanz:** Entweder PASS (Feature freigeschaltet) oder `NOT AVAILABLE ON THIS BACKEND` in CLI-Hilfe + UI-Matrix (§27 letzter Absatz). Kein stilles No-Op.
- **Evidenz:** Vorher/Nachher-Bilder + `0.2.0/visual/bonsai-edit/`.

### Schritt D.2 — Referenz-Packs & Storyboard-Frames
- **Ziel:** Multi-View (front/3-4/side/back/ganz/Gesicht), Charakter-/Prop-Packs, Storyboard-Frames (§27/§29) als Registry-Tools mit Konsistenz-QA.
- **Akzeptanz:** Golden-Test mit echter Generierung (kleine Auflösung für540p-Preview ok, Config dokumentiert) + Identitäts-Threshold statt Pixel-Gleichheit (§66).

---

## Phase E — 3D & Rig schließen (Phasen 6–7-Rest)

### Schritt E.1 — TRELLIS-1024-Entscheidung
- **Ziel:** 1024er-Profil entweder zertifizieren oder als `UNSUPPORTED_ON_THIS_HOST` markieren (OOM-/Zeit-Beleg).
- **Kommandos:** `scripts/test/test_trellis.ps1` mit 1024-Flag, Telemetrie, Validator, Turntable.
- **Akzeptanz:** Messwerte (Dauer/RAM/V/F) oder ehrlicher Block-Bericht (§141-Format) in `STATUS` + Matrix.

### Schritt E.2 — Humanoid-Fixture + Rigify-Generate
- **Ziel:** Größte offene 3D-Lücke schließen. Fixture beschaffen (lizenzsauber, z. B. CC0-Humanoid oder synthetischer Blender-Humanoid, Quelle + Lizenz dokumentiert) → `rig_character.py` über Gate hinaus (Metarig → Generate → Weights → Pose-Tests → Face-Rig-Ansatz).
- **Dateien:** `tests/fixtures/humanoid_basic.glb` (+ Herkunft/Lizenz-README), Erweiterung `integrations/blender/scripts/rig_character.py`, `pose_sheet.py`-Asserts.
- **Akzeptanz:** §35-Matrix (14 Posen) rendert + Evidence-JSON (Bones, Controls, Gewichte, Deformations-Check) + visuelle Prüfung. Bei Scheitern: Blocker-Bericht statt Fake-Rig.
- **Evidenz:** `0.2.0/visual/rig/` (Pose-Sheet + Turntable).

### Schritt E.3 — Retopo-Job trennen (§33)
- **Ziel:** `raw.glb` vs. `retopo.glb` als eigene Jobs mit Poly/Non-Manifold/Normal/UV-Checks.
- **Akzeptanz:** Unit (Job-Übergang) + Integration (echter Retopo-Lauf oder ehrlich `EXPERIMENTAL`).

---

## Phase F — Audio schließen (Phase 9-Rest)

### Schritt F.1 — CosyVoice-CPU-Route (falls gewollt) oder ehrlich parken
- **Route (aus STATUS.md):** `cosyvoice-cli`-CPU-Build vendoren → GGUF-Set (~745 MB) nach `models/tts_cosyvoice3_05b/` → `integrations/cosyvoice/worker.py` (Worker-Protokoll) → `scripts/test/test_cosyvoice.ps1` → Harness (echtes WAV + `ffprobe` + Amplituden-Check).
- **Akzeptanz:** Entweder Piper bleibt aktive Lane + CosyVoice als zweite Lane PASS, oder STATUS bleibt `EXPERIMENTAL (nicht staged)` mit datiertem Blocker (Download-/Build-Größe). Keine stillen Fallbacks (§113): CLI meldet explizit, welches Backend gesprochen hat.
- **Evidenz:** WAV + Validierungs-JSON oder Blocker-Bericht.

### Schritt F.2 — ACE-Step-Route (analog)
- **Route:** `acestep.cpp`-Vulkan-Build nach `bin/acestep-cpp/` → GGUF-Set (DiT-Turbo Q8_0 + VAE + Embedding, mehrere GB) → `integrations/acestep/worker.py` → `scripts/test/test_acestep.ps1` → Stems-Test (§47).
- **Akzeptanz:** Echte Musik-Stems oder weiterhin ehrlich `UNAVAILABLE`. Entscheidung dokumentieren (Aufwand vs. Nutzen auf 12-GB-UMA).

### Schritt F.3 — Lipsync aufwerten
- **Ziel:** Von RMS-Baseline zu Phonem→Visem-Timing (§46). Erst prüfen, ob Whisper-Alignment oder CosyVoice-Durations real liefern; sonst Baseline als `BASELINE` labeln + Face-Rig-Anbindung (E.2) fertigstellen.
- **Akzeptanz:** Golden-Test mit mehr als 10 Frames + Blender-Jaw-Keys + Proof-Render (bestehenden Test erweitern, nicht ersetzen).

---

## Phase G — Desktop-UI bauen (Phase 13; größter Brocken)

### Schritt G.1 — Toolchain pinnen (aus Upstream-Docs, nicht aus Erinnerung)
- **Ziel:** `rust-toolchain.toml`, Tauri-CLI-Version, Node-LTS, System-Deps (WebView2 auf Win).
- **Akzeptanz:** `cargo --version`, `node --version`, Tauri-Init läuft; Versionen in `apps/desktop/README.md` + `package.json` aktualisiert.

### Schritt G.2 — Shell über Control-Plane (dünn, keine Logik-Duplikate)
- **Ziel:** Layout aus §52 (Projekt-Rail, Canvas, Inspector, Assistant-Dock) als reine API/WS-Ansicht (`GET /health /models /projects`, `WS /ws/jobs`).
- **Dateien:** Erste echte `.tsx` (Views) + erstes `.rs` (Tauri-Commands: start/stop/health).
- **Akzeptanz:** `eslint`, `prettier --check`, `tsc --noEmit`, `cargo clippy/test/build` grün; App startet, zeigt Backend-Matrix aus `ui_kit` (keine Hardcoded-Labels, §128).
- **Evidenz:** Echte Screenshots (kein Konzept-Art, §99) → `docs/` + README.

### Schritt G.3 — Editoren (Bild/3D/Motion/Kamera/Licht/FX) als Parameter-Flächen
- **Ziel:** Jede AI-Empfehlung wird editierbarer Parameter (§56); 2D-Canvas + Three.js-Vorschau (Blender bleibt autoritativ, §54).
- **Akzeptanz:** Playwright-Szenario (§137: launch → create → generate → job → cancel → inspect → save → reopen) grün + manueller Review-Durchgang (§77-Checkliste).

### Schritt G.4 — i18n + A11y
- **Ziel:** DE/EN-Architektur ab Start (§139), Tastatur-Navigation, Fokus, Kontrast, Status-Texte (§138).
- **Akzeptanz:** Sprach-Umschalter funktioniert; A11y-Checkliste im PR.

---

## Phase H — E2E-Vollfilm §73 + visuelle Pipeline (Phase 14)

### Schritt H.1 — `produce --full` stabilisieren
- **Ziel:** Uncommittete `run_full_minifilm`-Arbeit (Schritt 0.1) zu einem reproduzierbaren §73-Film machen: 1 Projekt, 2 Charaktere, 1 Location, 1 Prop, 3 Szenen, 6 Shots, 20–60 s, 1080p.
- **Kommandos:** `python apps/cli/src/main.py produce --full -p "..." --project-name E2E_073` (mehrere Stunden GPU-Zeit einplanen; Bonsai ~3 min/Bild, Trellis ~7 min/Asset).
- **Akzeptanz:** `qa.movie passed=true` + Shot-Vollständigkeit + Continuity-Checks + Hashes; alle Artefakte in `0.2.0/visual/e2e/` (Contact-Sheets, Turntables, Pose-Sheets, Audio-Samples).
- **Evidenz:** `e2e.json` + Final-MP4 + Export-ZIP.

### Schritt H.2 — Release-Visual-Review vorbereiten (§77)
- **Ziel:** Review-Seiten automatisch erzeugen (Character-Sheet, Bild-Sample, Turntable, Pose-Sheet, Motion-, Kamera-, FX-, Voice-, Musik-Sample, kompletter Mini-Film, UI-Screenshots).
- **Akzeptanz:** Menschlicher Review-Durchgang dokumentiert (wer/wann/was abgenommen).

---

## Phase I — Stress/Soak-Vervollständigung (Phase 12-Rest, §74)

### Schritt I.1 — Stress A (50-Zyklen-Churn)
- **Ziel:** Bonsai↔Trellis↔Qwen↔Piper↔Blender im Wechsel; Abbruch-Kriterium bei Hardware-Gefahr (Temperatur/OOM) mit ehrlichem Zählstand statt erzwungener 50.
- **Akzeptanz:** `stress.json` (Peak-RAM/GPU, Load/Unload-Zähler, HDD-Bytes, Restarts, Fehler) oder datierter Teilstand + Blocker.

### Schritt I.2 — Stress B (kontrollierter Speicherdruck)
- **Ziel:** In separatem Testprozess über Normalbedarf gehen; erwartetes Verhalten: OOM erkannt → Cleanup → Fallback → Job-Retry/Block, kein Projekt-Schaden.
- **Akzeptanz:** Nachweis, dass kein Partial-Artefakt als gültig gilt.

### Schritt I.3 — Mehrstunden-Soak (§74-I)
- **Ziel:** Gemischte Workload über Stunden (über Nacht), Speicher-Trends + Restart-Zähler.
- **Akzeptanz:** `soak.json` mit Trend-Diagramm (oder CSV); Wachstums-Gate definiert.

---

## Phase J — Release-Reife (§§92/93/96/97/126/127)

### Schritt J.1 — Paketierung (§105)
- **Ziel:** `HCS-MovieForge-windows-x64-portable.zip` (+ Linux-Tarball, falls Linux-Host verfügbar, sonst als UNVERIFIED markiert) mit App, Start/Stop, Doctor, Config-Templates, Manifesten, README, Lizenzen. Modelle separat (nur Manifeste + Downloader).
- **Akzeptanz:** `checksums.txt` (SHA256 je Datei) + unabhängiges Re-Read-Verify (§93).

### Schritt J.2 — SBOM + Lizenzen (§103)
- **Ziel:** Modell-Registry (URL/Revision/Lizenz/Commercial-Note/Runtime/HW/Datum) vollständig; SBOM für App-Deps.
- **Akzeptanz:** README-Lizenzmatrix stimmt mit Manifesten überein; kommerzielle Einschränkungen benannt.

### Schritt J.3 — Clean-Room-Test (§97)
- **Ziel:** Frisches Temp-Verzeichnis → nur Doku-Pfad → doctor → Model-Sync → Bild-Smoke → 3D-Smoke → Projekt create/save/reopen → Mini-Film → 1080p-Verify → Hashes.
- **Akzeptanz:** Protokoll in `0.2.0/logs/cleanroom.txt`; jeder Fehlschlag = Release-Blocker.

### Schritt J.4 — README auf §98-Niveau
- **Ziel:** Was es ist/kann, OS/HW, was-lokal-geht vs. optional, Modellquellen+Lizenzen, Installation, Start/Stop, echte Screenshots + Diagramm, Limits, Troubleshooting, Verifikations-/Release-Status mit Datum+Profil.
- **Akzeptanz:** `README matches actual CLI/OS/backend status` (§120) + `lychee`-Check.

### Schritt J.5 — Tag + GitHub-Release (§§96/125/126)
- **Ziel:** Erst wenn J.1–J.4 + H + I grün: SemVer-Tag → GitHub-Release (Source, Pakete, Checksums, Verification-Report, Limits, Model-Lock-Snapshot).
- **Akzeptanz:** §126-Liste vollständig abgehakt; sonst kein `STABLE`-Label.

### Schritt J.6 — HF-Space (§§100–102)
- **Ziel:** `space-sync.yml` prüfen (Upstream-ZeroGPU-Docs!), `app.py` erweitern (nur erlaubte Demo-Flows), Space-CI (Import, UI-Render, 1 echte Gen, Validierung, Error-Handling, Cleanup).
- **Akzeptanz:** Space läuft + `space.json`-Beleg; kein unbegrenzter Film-Loop im Public-Demo.

---

## Reihenfolge-Empfehlung (kritischer Pfad)

```
0.1 Baum säubern (30 min)
→ B.1 Python-Checker (1 h)          parallel: A.1 Docs-Grundgerüst (2 h)
→ C.1 Memory (3 h) → D.1 Edit-Zert (2 h GPU) → E.2 Humanoid-Rig (4–8 h, größtes Risiko)
→ F.1/F.2 Entscheidung Cosy/ACE (je 2–6 h oder Parken in 30 min)
→ G.1–G.2 Desktop-Shell (1–3 Tage)
→ H.1 Vollfilm (1 Nacht GPU) → I.1/I.3 (1 Nacht) → J.1–J.6 (1 Tag)
```

**Realistische Größenordnung:** Kern-Lücken (ohne Desktop, ohne Cosy/ACE-Builds) ≈ 2–4 Arbeitstage + 2 GPU-Nächte. Mit Desktop-Shell + Space ≈ 1–2 Wochen. Mit CosyVoice-/ACE-Step-Vollintegration (Downloads + C++-Builds + Tuning) + X.

## Stop-Regeln (wann ehrlich pausieren statt schönreden)

- Humanoid-Rig scheitert an TRELLIS-Topologie → als `BLOCKED (Fixtur X, Fehlermaße Y)` in Matrix + Release-Notes, Rest bleibt nutzbar (§0.3).
- 1024-TRELLIS OOM auf 12-GB-UMA → als `UNSUPPORTED_ON_THIS_HOST` markieren, 512 bleibt supported.
- CosyVoice-Vulkan bleibt upstream NOT working → CPU-Lane oder Parken; Piper bleibt deklarierte Lane.
- Stress-A/B gefährden Host → abbrechen, Teilstand protokollieren (§74 erlaubt das explizit).

---

*Nach jedem Schritt: Evidenz in `artifacts/verification/0.2.0/` ablegen, Doku aktualisieren, klein committen. Erst wenn alle §147-Kästchen mit Beleg geschlossen sind, `STABLE`/`GREEN` verwenden.*
