# Desktop shell (Tauri) — skeleton status: PENDING BUILD

The desktop UI is a thin shell over the control-plane API (`apps/api/src/main.py`).
No Tauri/Rust/TS build has been certified yet; versions will be pinned from current
upstream Tauri docs at build time (never from memory).

## Contract the shell will consume

- `GET /health` — backend/model readiness
- `GET /models` — manifests + installed flags
- `GET /projects`, `POST /projects`, `GET /projects/{id}/shots` — project state
- `WS /ws/jobs?project=` — job snapshots at 1Hz (no polling loops in UI thread)

## Layout target (GEMINI.md §52)

Project rail | Canvas (2D/3D/shot) | Inspector | AI assistant dock.
Status labels come from `packages/ui_kit` (verification-driven, non-color text markers).

## Pending

1. Pin `rust-toolchain.toml` + Tauri CLI + Node LTS from upstream requirements.
2. `cargo clippy/test/build`, `eslint`, `tsc --noEmit`, Playwright desktop-critical paths.
3. Screenshots in README only from the real app (§99).
