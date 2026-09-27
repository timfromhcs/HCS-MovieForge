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
        if not Path(fpath).exists():
            details[fname] = "MISSING_ON_DISK"
            all_match = False
        elif exp and not verify_sha256(fpath, exp):
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
@click.pass_context
def benchmark(ctx: click.Context) -> None:
    """Probes system performance and safe memory budget."""
    as_json = ctx.obj.get("JSON", False)
    profile = probe_hardware()
    if as_json:
        print(profile.model_dump_json(indent=2))
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


@cli.command()
@click.option("--prompt", "-p", required=True, help="Creative prompt for autonomous mini-film production.")
@click.option("--project-name", default="MiniFilm_Robot", help="Name of project to create.")
@click.pass_context
def produce(ctx: click.Context, prompt: str, project_name: str) -> None:
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
    res = agent.run_production(prompt=prompt, project_id=p_id)
    if as_json:
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    cli()
