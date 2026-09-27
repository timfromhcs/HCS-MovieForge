"""Main CLI entrypoint for HCS MovieForge implementing headless-first commands."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import click  # noqa: E402

from engine.model_manager.manager import ModelManager  # noqa: E402
from engine.project_manager.manager import ProjectManager  # noqa: E402
from packages.telemetry.src.probe import probe_hardware, probe_vulkan  # noqa: E402


@click.group()
@click.option("--json-output", is_flag=True, help="Emit output as structured JSON")
@click.pass_context
def cli(ctx: click.Context, json_output: bool) -> None:
    """HCS MovieForge - Autonomous Local-First AI Filmmaking Workstation."""
    ctx.ensure_object(dict)
    ctx.obj["JSON"] = json_output


@cli.command()
@click.option("--offline", is_flag=True, help="Verify local-only readiness without checking network")
@click.pass_context
def doctor(ctx: click.Context, offline: bool) -> None:
    """Checks the health and readiness of all local dependencies and toolchains."""
    as_json = ctx.obj.get("JSON", False)
    checks: dict[str, dict[str, Any]] = {}
    all_ok = True

    # Check OS
    checks["os"] = {"status": "ok", "message": f"{sys.platform} (64-bit)"}

    # Check Git
    git_path = shutil.which("git")
    if git_path:
        res = subprocess.run(["git", "--version"], capture_output=True, text=True)
        checks["git"] = {"status": "ok", "message": res.stdout.strip()}
    else:
        checks["git"] = {"status": "error", "message": "git not found"}
        all_ok = False

    # Check Python
    checks["python"] = {"status": "ok", "message": f"Python {sys.version.split()[0]}"}

    # Check Node
    node_path = shutil.which("node")
    if node_path:
        res = subprocess.run(["node", "--version"], capture_output=True, text=True)
        checks["node"] = {"status": "ok", "message": res.stdout.strip()}
    else:
        checks["node"] = {"status": "warning", "message": "node not found (needed for desktop UI build)"}

    # Check Rust
    cargo_path = shutil.which("cargo")
    if cargo_path:
        res = subprocess.run(["cargo", "--version"], capture_output=True, text=True)
        checks["rust"] = {"status": "ok", "message": res.stdout.strip()}
    else:
        checks["rust"] = {"status": "warning", "message": "cargo not found (needed for Tauri desktop)"}

    # Check CMake & Ninja
    cmake_path = shutil.which("cmake")
    checks["cmake"] = {
        "status": "ok" if cmake_path else "warning",
        "message": "cmake found" if cmake_path else "cmake missing",
    }

    ninja_path = shutil.which("ninja")
    checks["ninja"] = {
        "status": "ok" if ninja_path else "warning",
        "message": "ninja found" if ninja_path else "ninja missing",
    }

    # Check FFmpeg & ffprobe
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if ffmpeg_path and ffprobe_path:
        checks["ffmpeg"] = {"status": "ok", "message": "FFmpeg and ffprobe available"}
    else:
        checks["ffmpeg"] = {"status": "error", "message": "FFmpeg or ffprobe missing from PATH"}
        all_ok = False

    # Check Blender
    blender_path = shutil.which("blender")
    if not blender_path:
        # Check standard install path discovered during probe
        std_blender = Path("C:/Program Files/Blender Foundation/Blender 5.1/blender.exe")
        if std_blender.exists():
            blender_path = str(std_blender)

    if blender_path:
        checks["blender"] = {"status": "ok", "message": f"Blender found at {blender_path}"}
    else:
        checks["blender"] = {"status": "error", "message": "Blender not found"}
        all_ok = False

    # Check Vulkan
    vulkan = probe_vulkan()
    if vulkan.device_name and vulkan.device_name != "Unknown":
        checks["vulkan"] = {
            "status": "ok",
            "message": f"{vulkan.device_name} (API {vulkan.api_version}, Driver {vulkan.driver_version})",
        }
    else:
        checks["vulkan"] = {"status": "warning", "message": "Vulkan device details could not be probed"}

    # Check AI Engine Backends
    from integrations.llama_cpp.worker import LlamaWorker
    from integrations.piper.worker import PiperWorker
    from integrations.stable_diffusion_cpp.worker import StableDiffusionWorker
    from integrations.trellis_cpp.worker import TrellisWorker
    from integrations.whisper_cpp.worker import WhisperWorker

    for name, worker in [
        ("sd.cpp", StableDiffusionWorker()),
        ("trellis.cpp", TrellisWorker()),
        ("llama.cpp", LlamaWorker()),
        ("whisper.cpp", WhisperWorker()),
        ("piper", PiperWorker()),
    ]:
        h = worker.health()
        if h.get("status") == "ok":
            checks[name] = {"status": "ok", "message": f"{worker.backend_name} ({worker.backend_version})"}
        else:
            checks[name] = {"status": "warning", "message": h.get("message", "Not found")}

    # Offline model-file verification: every locked model file must exist on disk
    mgr = ModelManager()
    lock = mgr.get_lock()
    missing: list[str] = []
    for model_id, entry in lock.get("models", {}).items():
        for fname, fpath in entry.get("files", {}).items():
            if not mgr.resolve_locked_path(fpath).exists():
                missing.append(f"{model_id}:{fname}")
    if missing:
        checks["models"] = {"status": "error", "message": f"{len(missing)} locked file(s) missing: {missing[0]}"}
        all_ok = False
    else:
        count = len(lock.get("models", {}))
        checks["models"] = {"status": "ok", "message": f"{count} locked model(s) present on disk"}
    if offline and not as_json:
        click.echo("(offline mode: network-dependent revision checks skipped)")

    if as_json:
        print(json.dumps({"overall_status": "READY" if all_ok else "DEGRADED", "checks": checks}, indent=2))
    else:
        click.echo("========================================")
        click.echo("       HCS MovieForge - Doctor          ")
        click.echo("========================================")
        for name, data in checks.items():
            st = data["status"]
            icon = "[OK]  " if st == "ok" else ("[WARN]" if st == "warning" else "[FAIL]")
            color = "green" if st == "ok" else ("yellow" if st == "warning" else "red")
            click.secho(f"{icon} {name.upper():<10}: {data['message']}", fg=color)

        click.echo("----------------------------------------")
        if all_ok:
            click.secho("LOCAL CORE: READY", fg="green", bold=True)
        else:
            click.secho("LOCAL CORE: DEGRADED / MISSING PREREQUISITES", fg="red", bold=True)

    if not all_ok:
        sys.exit(1)


@cli.group()
def models() -> None:
    """Manage AI model manifests, downloads, and lock files."""
    pass


@models.command(name="list")
@click.pass_context
def models_list(ctx: click.Context) -> None:
    """Lists all configured model manifests and their installation status."""
    as_json = ctx.obj.get("JSON", False)
    mgr = ModelManager()
    manifests = mgr.list_manifests()
    lock = mgr.get_lock()
    installed = lock.get("models", {})

    results = []
    for m in manifests:
        m_id = m.get("id")
        is_inst = m_id in installed
        results.append(
            {
                "id": m_id,
                "name": m.get("name"),
                "role": m.get("role"),
                "backend": m.get("backend"),
                "installed": is_inst,
            }
        )

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        click.echo(f"{'ID':<30} {'ROLE':<10} {'BACKEND':<20} {'INSTALLED'}")
        click.echo("-" * 70)
        for r in results:
            inst_str = click.style("YES", fg="green") if r["installed"] else click.style("NO", fg="yellow")
            click.echo(f"{r['id']:<30} {r['role']:<10} {r['backend']:<20} {inst_str}")


@models.command(name="sync")
@click.argument("model_id")
@click.pass_context
def models_sync(ctx: click.Context, model_id: str) -> None:
    """Downloads, verifies hashes, and atomically promotes a model to active store."""
    as_json = ctx.obj.get("JSON", False)
    mgr = ModelManager()
    token = os.environ.get("HF_TOKEN")
    click.echo(f"Syncing model: {model_id}...")
    success, errors = mgr.download_and_verify(model_id, token=token)
    if success:
        if as_json:
            print(json.dumps({"status": "synced", "model_id": model_id}))
        else:
            click.secho(f"[OK] Model {model_id} successfully downloaded and verified.", fg="green")
    else:
        if as_json:
            print(json.dumps({"status": "failed", "model_id": model_id, "errors": errors}))
        else:
            click.secho(f"[FAIL] Failed to sync {model_id}: {errors}", fg="red")
        sys.exit(1)


@models.command(name="verify")
@click.argument("model_id")
@click.pass_context
def models_verify(ctx: click.Context, model_id: str) -> None:
    """Verifies local checksums of an installed model against its manifest."""
    as_json = ctx.obj.get("JSON", False)
    mgr = ModelManager()
    manifest = mgr.get_manifest(model_id)
    if not manifest:
        click.secho(f"[FAIL] Manifest not found for model: {model_id}", fg="red")
        sys.exit(1)

    lock = mgr.get_lock()
    installed = lock.get("models", {}).get(model_id)
    if not installed:
        click.secho(f"[FAIL] Model {model_id} is not recorded in lock file.", fg="red")
        sys.exit(1)

    from packages.validators.src.hash_validator import verify_sha256

    files = installed.get("files", {})
    expected_hashes = manifest.get("sha256", {})

    all_match = True
    details = {}
    for fname, fpath in files.items():
        exp = expected_hashes.get(fname)
        resolved = mgr.resolve_locked_path(fpath)
        if not resolved.exists():
            details[fname] = "MISSING_ON_DISK"
            all_match = False
        elif exp and not verify_sha256(resolved, exp):
            details[fname] = "CHECKSUM_MISMATCH"
            all_match = False
        else:
            details[fname] = "VERIFIED_OK"

    if as_json:
        print(json.dumps({"model_id": model_id, "status": "OK" if all_match else "FAILED", "files": details}))
    else:
        if all_match:
            click.secho(f"[OK] Model {model_id} integrity verified cleanly.", fg="green")
        else:
            click.secho(f"[FAIL] Model {model_id} verification failed: {details}", fg="red")
            sys.exit(1)


@cli.group()
def project() -> None:
    """Create, open, and inspect MovieForge projects."""
    pass


@project.command(name="create")
@click.argument("name")
@click.option("--id", "project_id", default=None, help="Explicit project ID")
@click.pass_context
def project_create(ctx: click.Context, name: str, project_id: str | None) -> None:
    """Creates a new canonical project directory and WAL database."""
    as_json = ctx.obj.get("JSON", False)
    mgr = ProjectManager()
    p_id = project_id or name.lower().replace(" ", "_")
    try:
        p_path = mgr.create_project(name=name, project_id=p_id)
        if as_json:
            print(json.dumps({"status": "created", "path": str(p_path), "project_id": p_id}))
        else:
            click.secho(f"[OK] Project created successfully at: {p_path}", fg="green")
    except Exception as e:
        if as_json:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            click.secho(f"Error creating project: {e}", fg="red")
        sys.exit(1)


@cli.command()
@click.option("--save", is_flag=True, help="Persist calibrated hardware profile to runtime/hardware-profile.json.")
@click.option("--hdd", is_flag=True, help="Run real HDD sequential + model cold/warm load measurements.")
@click.pass_context
def benchmark(ctx: click.Context, save: bool, hdd: bool) -> None:
    """Probes system performance and safe memory budget."""
    import time

    as_json = ctx.obj.get("JSON", False)
    profile = probe_hardware()
    hdd_result: dict[str, Any] = {}
    if hdd:
        tmp = _PROJECT_ROOT / "runtime" / "tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        blob = tmp / "hdd_bench.bin"
        size_mb = 256
        chunk = os.urandom(1024 * 1024)
        t0 = time.time()
        with open(blob, "wb") as f:
            for _ in range(size_mb):
                f.write(chunk)
        write_sec = time.time() - t0
        t0 = time.time()
        with open(blob, "rb") as f:
            while f.read(1024 * 1024):
                pass
        read_sec = time.time() - t0
        hdd_result = {
            "seq_write_mbs": round(size_mb / max(write_sec, 1e-6), 1),
            "seq_read_mbs": round(size_mb / max(read_sec, 1e-6), 1),
        }
        try:
            blob.unlink()
        except OSError:
            pass
        models = sorted((_PROJECT_ROOT / "models").rglob("*.gguf"))
        if models:
            target = max(models, key=lambda p: p.stat().st_size)
            sample = 64 * 1024 * 1024
            t0 = time.time()
            with open(target, "rb") as f:
                f.read(sample)
            cold_sec = time.time() - t0
            t0 = time.time()
            with open(target, "rb") as f:
                f.read(sample)
            warm_sec = time.time() - t0
            hdd_result["model_cold_64mb_sec"] = round(cold_sec, 2)
            hdd_result["model_warm_64mb_sec"] = round(warm_sec, 2)
            hdd_result["model_file"] = target.name
    if save:
        from engine.resource_manager.manager import ResourceManager

        saved = ResourceManager(runtime_dir=_PROJECT_ROOT / "runtime").save_profile()
        if not as_json:
            click.echo(f"Profile saved: {saved}")
    if as_json:
        data = json.loads(profile.model_dump_json())
        if hdd_result:
            data["hdd"] = hdd_result
        print(json.dumps(data, indent=2))
    else:
        click.echo("========================================")
        click.echo("       HCS MovieForge - Hardware Profile")
        click.echo("========================================")
        click.echo(f"CPU: {profile.cpu_name} ({profile.cpu_cores} Cores / {profile.cpu_threads} Threads)")
        click.echo(
            f"RAM: {profile.system_memory.total_ram_mb} MB Total, {profile.system_memory.available_ram_mb} MB Available"
        )
        click.echo(f"Vulkan: {profile.vulkan_device.device_name} (API {profile.vulkan_device.api_version})")
        click.echo(f"Storage: {profile.storage.free_gb} GB Free on {profile.storage.path}")
        click.echo("Safe UMA Memory Budgets:")
        click.echo(f"  OS Safety Reserve:  {profile.os_safety_reserve_mb} MB")
        click.echo(f"  Blender Reserve:    {profile.blender_reserve_mb} MB")
        click.echo(f"  Model Safe Budget:  {profile.model_budget_mb} MB")
        click.echo(f"  Max Heavy GPU Jobs: {profile.max_heavy_gpu_jobs}")
        if hdd_result:
            click.echo("HDD Measurements:")
            for key, value in hdd_result.items():
                click.echo(f"  {key}: {value}")


@cli.command()
@click.option("--prompt", "-p", required=True, help="Creative prompt for autonomous mini-film production.")
@click.option("--project-name", default="MiniFilm_Robot", help="Name of project to create.")
@click.option("--full", is_flag=True, help="Run the full §73 mini-film (2 chars, 6 shots, 24s).")
@click.pass_context
def produce(ctx: click.Context, prompt: str, project_name: str, full: bool) -> None:
    """Executes the complete autonomous production pipeline (GEMINI.md Section 146)."""
    as_json = ctx.obj.get("JSON", False)
    mgr = ProjectManager()
    p_id = project_name.lower().replace(" ", "_")
    p_path = mgr.projects_root / p_id
    if not p_path.exists():
        p_path = mgr.create_project(name=project_name, project_id=p_id)
    click.echo(f"Active production workspace at: {p_path}")

    from agent.director.master_agent import MasterDirectorAgent

    agent = MasterDirectorAgent(project_root=p_path)
    if full:
        res = agent.run_full_minifilm(prompt=prompt, project_id=p_id)
        if as_json:
            print(json.dumps(res, indent=2))
        return
    res = agent.run_production(prompt=prompt, project_id=p_id)
    if as_json:
        print(json.dumps(res, indent=2))


@project.command(name="open")
@click.argument("project_id")
@click.pass_context
def project_open(ctx: click.Context, project_id: str) -> None:
    """Validates and opens an existing project, printing its manifest."""
    as_json = ctx.obj.get("JSON", False)
    mgr = ProjectManager()
    try:
        manifest, _ = mgr.open_project(mgr.projects_root / project_id)
        if as_json:
            print(manifest.model_dump_json(indent=2))
        else:
            click.secho(f"[OK] Project '{manifest.name}' ({manifest.project_id}) is valid.", fg="green")
            click.echo(f"  FPS: {manifest.target_fps}  Resolution: {manifest.target_resolution}")
    except Exception as e:
        click.secho(f"[FAIL] Cannot open project: {e}", fg="red")
        sys.exit(1)


@project.command(name="save")
@click.argument("project_id")
@click.option("--reason", default="manual", help="Snapshot reason recorded in metadata.")
@click.pass_context
def project_save(ctx: click.Context, project_id: str, reason: str) -> None:
    """Creates a durable snapshot of the project database."""
    as_json = ctx.obj.get("JSON", False)
    mgr = ProjectManager()
    try:
        snap = mgr.create_snapshot(mgr.projects_root / project_id, reason=reason)
        if as_json:
            print(json.dumps({"status": "saved", "snapshot": str(snap)}))
        else:
            click.secho(f"[OK] Snapshot written: {snap}", fg="green")
    except Exception as e:
        click.secho(f"[FAIL] Save failed: {e}", fg="red")
        sys.exit(1)


@project.command(name="export")
@click.argument("project_id")
@click.option("--output", default=None, help="Destination zip path.")
@click.pass_context
def project_export(ctx: click.Context, project_id: str, output: str | None) -> None:
    """Exports a project to a portable zip and records its SHA256."""
    import hashlib
    import zipfile

    as_json = ctx.obj.get("JSON", False)
    mgr = ProjectManager()
    src = mgr.projects_root / project_id
    try:
        manifest, _ = mgr.open_project(src)
        _ = manifest
    except Exception as e:
        click.secho(f"[FAIL] Cannot export invalid project: {e}", fg="red")
        sys.exit(1)
    dest = Path(output) if output else Path(f"dist/{project_id}-export.zip")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src.rglob("*")):
            if p.is_file() and ".movieforge/locks" not in p.as_posix():
                zf.write(p, p.relative_to(src))
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    if as_json:
        print(json.dumps({"status": "exported", "path": str(dest), "sha256": sha}))
    else:
        click.secho(f"[OK] Exported {dest} (sha256={sha[:16]}...)", fg="green")


@cli.group()
def test() -> None:
    """Run verification suites (smoke, integration, stress, soak)."""
    pass


@test.command(name="smoke")
@click.pass_context
def test_smoke(ctx: click.Context) -> None:
    """Runs doctor plus the fast unit suite."""
    as_json = ctx.obj.get("JSON", False)
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(cli, ["doctor"])
    if result.exit_code != 0:
        click.secho("[FAIL] doctor check failed.", fg="red")
        sys.exit(1)
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests/unit", "-q"], capture_output=True, text=True)
    ok = proc.returncode == 0
    if as_json:
        print(json.dumps({"status": "ok" if ok else "failed", "pytest": proc.stdout[-2000:]}))
    else:
        click.echo(proc.stdout[-2000:] if proc.stdout else "")
        click.secho("[OK] Smoke passed." if ok else "[FAIL] Unit tests failed.", fg="green" if ok else "red")
    if not ok:
        sys.exit(1)


@test.command(name="integration")
@click.pass_context
def test_integration(ctx: click.Context) -> None:
    """Runs the real backend harness scripts (long: Bonsai + TRELLIS take minutes)."""
    as_json = ctx.obj.get("JSON", False)
    root = _PROJECT_ROOT
    scripts = [
        "scripts/test/test_blender.ps1",
        "scripts/test/test_ffmpeg.ps1",
        "scripts/test/test_whisper.ps1",
        "scripts/test/test_piper.ps1",
        "scripts/test/test_bonsai.ps1",
        "scripts/test/test_trellis.ps1",
        "scripts/test/test_qwen3_vl.ps1",
    ]
    use_pwsh = shutil.which("pwsh") or shutil.which("powershell")
    results: dict[str, str] = {}
    failed = False
    for script in scripts:
        path = root / script
        if not path.exists():
            results[script] = "MISSING"
            failed = True
            continue
        if use_pwsh:
            proc = subprocess.run([use_pwsh, "-File", str(path)], capture_output=True, text=True)
        else:
            sh_equiv = str(path).replace(".ps1", ".sh")
            if not Path(sh_equiv).exists():
                results[script] = "NO_RUNNER"
                failed = True
                continue
            proc = subprocess.run(["bash", sh_equiv], capture_output=True, text=True)
        results[script] = "PASS" if proc.returncode == 0 else "FAIL"
        if proc.returncode != 0:
            failed = True
    if as_json:
        print(json.dumps({"status": "failed" if failed else "ok", "harnesses": results}, indent=2))
    else:
        for name, status in results.items():
            click.echo(f"  {status:4}  {name}")
        click.secho(
            "[FAIL] Integration failed." if failed else "[OK] Integration passed.", fg="red" if failed else "green"
        )
    if failed:
        sys.exit(1)


@test.command(name="stress")
@click.pass_context
def test_stress(ctx: click.Context) -> None:
    """Runs stress suites when tests/stress exists; honest BLOCKED otherwise."""
    stress_dir = _PROJECT_ROOT / "tests" / "stress"
    cases = sorted(stress_dir.glob("test_*.py"))
    if not cases:
        click.secho("[BLOCKED] No stress suites yet (tests/stress empty, Phase F pending).", fg="yellow")
        sys.exit(2)
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests/stress", "-q"], capture_output=True, text=True)
    click.echo(proc.stdout[-2000:])
    if proc.returncode != 0:
        sys.exit(1)


@test.command(name="soak")
@click.pass_context
def test_soak(ctx: click.Context) -> None:
    """Runs soak suites when tests/soak exists; honest BLOCKED otherwise."""
    soak_dir = _PROJECT_ROOT / "tests" / "soak"
    cases = sorted(soak_dir.glob("test_*.py"))
    if not cases:
        click.secho("[BLOCKED] No soak suites yet (tests/soak empty, Phase F pending).", fg="yellow")
        sys.exit(2)
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests/soak", "-q"], capture_output=True, text=True)
    click.echo(proc.stdout[-2000:])
    if proc.returncode != 0:
        sys.exit(1)


@cli.group()
def render() -> None:
    """Render project previews and final masters through Blender + FFmpeg."""
    pass


def _find_blender() -> str | None:
    found = shutil.which("blender")
    if found:
        return found
    default = Path("C:/Program Files/Blender Foundation/Blender 5.1/blender.exe")
    return str(default) if default.exists() else None


@render.command(name="preview")
@click.argument("project_id")
@click.pass_context
def render_preview(ctx: click.Context, project_id: str) -> None:
    """Renders a turntable preview of the newest GLB in the project."""
    as_json = ctx.obj.get("JSON", False)
    src = ProjectManager().projects_root / project_id
    glbs = sorted(src.rglob("*.glb"), key=lambda p: p.stat().st_mtime) if src.exists() else []
    if not glbs:
        click.secho(f"[FAIL] No GLB asset found in project '{project_id}'.", fg="red")
        sys.exit(1)
    blender = _find_blender()
    if not blender:
        click.secho("[FAIL] Blender executable not found.", fg="red")
        sys.exit(1)
    out = src / "renders" / f"{glbs[-1].stem}_preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    script = _PROJECT_ROOT / "integrations" / "blender" / "scripts" / "import_and_render_turntable.py"
    proc = subprocess.run(
        [blender, "-b", "--python", str(script), "--", "--input", str(glbs[-1]), "--output", str(out)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0 or not out.exists():
        click.secho(f"[FAIL] Preview render failed: {proc.stderr[-1000:]}", fg="red")
        sys.exit(1)
    if as_json:
        print(json.dumps({"status": "ok", "path": str(out)}))
    else:
        click.secho(f"[OK] Preview rendered: {out}", fg="green")


@render.command(name="final")
@click.argument("project_id")
@click.option("--fps", type=int, default=24, help="Timeline framerate.")
@click.pass_context
def render_final(ctx: click.Context, project_id: str, fps: int) -> None:
    """Assembles VSE timeline from project stills + audio into a 1080p master."""
    as_json = ctx.obj.get("JSON", False)
    src = ProjectManager().projects_root / project_id
    if not src.exists():
        click.secho(f"[FAIL] Unknown project '{project_id}'.", fg="red")
        sys.exit(1)
    clips = sorted([str(p) for p in list((src / "images").glob("*.png")) + list((src / "renders").glob("*.png"))])
    if not clips:
        click.secho("[FAIL] No image clips found for timeline assembly.", fg="red")
        sys.exit(1)
    audios = sorted((src / "audio").glob("*.wav")) if (src / "audio").exists() else []
    blender = _find_blender()
    if not blender:
        click.secho("[FAIL] Blender executable not found.", fg="red")
        sys.exit(1)
    out = src / "exports" / f"{project_id}_final_1080p.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    script = _PROJECT_ROOT / "integrations" / "blender" / "scripts" / "assemble_timeline.py"
    cmd = [blender, "-b", "--python", str(script), "--", "--output", str(out), "--fps", str(fps)]
    cmd += ["--clips", *clips]
    if audios:
        cmd += ["--audio", str(audios[0])]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not out.exists():
        click.secho(f"[FAIL] Final render failed: {proc.stderr[-1000:]}", fg="red")
        sys.exit(1)
    if as_json:
        print(json.dumps({"status": "ok", "path": str(out)}))
    else:
        click.secho(f"[OK] Final master rendered: {out}", fg="green")


@cli.group()
def server() -> None:
    """Control the local supervisor process tree."""
    pass


@server.command(name="start")
@click.option("--port", type=int, default=8765, help="Control-plane API port.")
@click.option("--no-api", is_flag=True, help="Start supervisor without the API child.")
@click.pass_context
def server_start(ctx: click.Context, port: int, no_api: bool) -> None:
    """Starts the supervisor and launches the control-plane API as tracked child."""
    import psutil

    from engine.supervisor.supervisor import ProcessSupervisor

    sup = ProcessSupervisor(runtime_dir=_PROJECT_ROOT / "runtime")
    if sup.pid_file.exists():
        try:
            pid = int(sup.pid_file.read_text().strip())
            if psutil.pid_exists(pid):
                click.secho(f"[FAIL] Supervisor already running (PID {pid}).", fg="red")
                sys.exit(1)
        except (ValueError, OSError):
            pass
    sup.start()
    if not no_api:
        sup.register_service(
            "api",
            [sys.executable, "-m", "uvicorn", "apps.api.src.main:app", "--host", "127.0.0.1", "--port", str(port)],
            restart_policy="always",
            max_restarts=3,
        )
        if sup.launch_service("api"):
            click.secho(f"[OK] API child launched on 127.0.0.1:{port}.", fg="green")
        else:
            click.secho("[FAIL] API child failed to launch.", fg="red")
            sys.exit(1)
    click.secho(f"[OK] Supervisor running (pid file: {sup.pid_file}).", fg="green")


@server.command(name="stop")
@click.pass_context
def server_stop(ctx: click.Context) -> None:
    """Stops tracked child services gracefully via the persisted PID list."""
    import signal as _signal

    import psutil

    from engine.supervisor.supervisor import ProcessSupervisor

    sup = ProcessSupervisor(runtime_dir=_PROJECT_ROOT / "runtime")
    state_file = sup.state_file
    pids: list[int] = []
    if state_file.exists():
        try:
            pids = [int(p) for p in json.loads(state_file.read_text()).get("pids", [])]
        except (ValueError, OSError, KeyError):
            pids = []
    me = os.getpid()
    for pid in pids:
        if pid == me:
            continue
        try:
            if psutil.pid_exists(pid):
                os.kill(pid, _signal.SIGTERM)
        except (OSError, PermissionError):
            continue
    sup.stop()
    click.secho("[OK] Supervisor stopped.", fg="green")


@cli.group()
def release() -> None:
    """Release certification helpers."""
    pass


@release.command(name="verify")
@click.pass_context
def release_verify(ctx: click.Context) -> None:
    """Checks release gates that can be verified without hardware certification."""
    as_json = ctx.obj.get("JSON", False)
    checks: dict[str, bool] = {}
    proc = subprocess.run(["git", "diff", "--check"], capture_output=True, text=True)
    checks["git_diff_check"] = proc.returncode == 0
    proc = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    checks["worktree_clean"] = proc.stdout.strip() == ""
    checks["readme_exists"] = (_PROJECT_ROOT / "README.md").exists()
    checks["model_lock"] = (_PROJECT_ROOT / "models" / "locks" / "model-lock.json").exists()
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests/unit", "-q"], capture_output=True, text=True)
    checks["unit_tests"] = proc.returncode == 0
    proc = subprocess.run([sys.executable, "-m", "ruff", "check", "."], capture_output=True, text=True)
    checks["ruff"] = proc.returncode == 0
    ok = all(checks.values())
    if as_json:
        print(json.dumps({"status": "ok" if ok else "failed", "checks": checks}, indent=2))
    else:
        for name, passed in checks.items():
            click.echo(f"  {'PASS' if passed else 'FAIL'}  {name}")
        click.secho("[OK] Release gates green." if ok else "[FAIL] Release gates red.", fg="green" if ok else "red")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    cli()
