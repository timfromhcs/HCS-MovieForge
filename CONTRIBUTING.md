# Contributing to HCS MovieForge

Thank you for your interest in contributing to HCS MovieForge!

## Autonomous & Local-First Philosophy

HCS MovieForge operates strictly under the principles outlined in `GEMINI.md`:
1. **Never hallucinate**: Documented capabilities must be verified against real hardware and upstream artifacts.
2. **Never use fake success**: No mock inference in production code, no dummy GLBs pretending to be generated assets.
3. **Code completion != Feature completion**: Every feature requires linting, unit tests, build, integration smoke test, and documentation.
4. **Editable production state**: The project remains fully functional and editable even without AI autonomy.

## Development Workflow

1. Fork and clone the repository.
2. Ensure you have the required prerequisites:
   - Python 3.12+ (or 3.14 on tested systems)
   - Node.js 20+ / 22+
   - Rust 1.80+ / stable
   - CMake 3.28+ and Ninja
   - Vulkan 1.3+ compatible GPU and runtime
   - Blender 4.5+ or 5.1+
   - FFmpeg 6.0+
3. Run `movieforge doctor` to verify environment health.
4. Run tests:
   ```bash
   pytest
   npm test
   cargo test
   ```
5. Follow formatting and linting:
   - Python: `ruff check`, `ruff format`
   - TypeScript: `eslint`, `prettier`
   - Rust: `cargo clippy`, `cargo fmt`
6. Submit a pull request with clear verification evidence.
