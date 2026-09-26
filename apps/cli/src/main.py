"""Main CLI entrypoint for HCS MovieForge implementing headless-first commands."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import click
from engine.model_manager.manager import ModelManager
from engine.project_manager.manager import ProjectManager
from packages.telemetry.src.probe import probe_hardware, probe_vulkan


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
    checks["cmake"] = {"status": "ok" if cmake_path else "warning", "message": "cmake found" if cmake_path else "cmake missing"}

    ninja_path = shutil.which("ninja")
    checks["ninja"] = {"status": "ok" if ninja_path else "warning", "message": "ninja found" if ninja_path else "ninja missing"}

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
        results.append({
            "id": m_id,
            "name": m.get("name"),
            "role": m.get("role"),
            "backend": m.get("backend"),
            "installed": is_inst,
        })

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        click.echo(f"{'ID':<30} {'ROLE':<10} {'BACKEND':<20} {'INSTALLED'}")
        click.echo("-" * 70)
        for r in results:
            inst_str = click.style("YES", fg="green") if r["installed"] else click.style("NO", fg="yellow")
            click.echo(f"{r['id']:<30} {r['role']:<10} {r['backend']:<20} {inst_str}")


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
        click.echo(f"RAM: {profile.system_memory.total_ram_mb} MB Total, {profile.system_memory.available_ram_mb} MB Available")
        click.echo(f"Vulkan: {profile.vulkan_device.device_name} (API {profile.vulkan_device.api_version})")
        click.echo(f"Storage: {profile.storage.free_gb} GB Free on {profile.storage.path}")
        click.echo("Safe UMA Memory Budgets:")
        click.echo(f"  OS Safety Reserve:  {profile.os_safety_reserve_mb} MB")
        click.echo(f"  Blender Reserve:    {profile.blender_reserve_mb} MB")
        click.echo(f"  Model Safe Budget:  {profile.model_budget_mb} MB")
        click.echo(f"  Max Heavy GPU Jobs: {profile.max_heavy_gpu_jobs}")


if __name__ == "__main__":
    cli()
