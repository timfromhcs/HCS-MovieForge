# HCS MovieForge Model Registry

This directory contains versioned manifests and lock files for all AI models utilized by HCS MovieForge.

## Directory Layout

- `manifests/`: Machine-readable model manifests defining upstream repositories, revisions, expected files, SHA256 checksums, and resource estimates.
- `locks/`: Installed model lock files recording verified local file paths, calculated checksums, and promotion timestamps.
- `staging/`: Temporary directory for active downloads before verification and atomic promotion (gitignored).

## Model Download & Verification Policy

1. All models are downloaded via Hugging Face API / `hf` CLI using the headless model downloader (`movieforge models sync`).
2. Downloaded files are staged in `models/staging/`.
3. Checksums are computed locally. If an upstream hash is published, it is verified. If not, the locally computed hash is saved as the installation fingerprint.
4. Only after successful size, structure, and hash verification is the model atomically promoted to the active runtime path and added to `models/locks/model-lock.json`.
5. Model weights (`*.gguf`, `*.bin`, `*.safetensors`) MUST NOT be committed to Git.
