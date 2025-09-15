"""Command Deck CLI — Automate all the things."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import typer

__version__ = "0.1.2"


def version_callback(value: bool):
    if value:
        typer.echo(f"deck version {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Command Deck CLI — Automate all the things.", callback=None)


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    )
) -> None:
    """Command Deck CLI — Automate all the things."""
    pass


# --------------------------
# new/* — create agents and projects
# --------------------------
new_app = typer.Typer(help="Create new agents and projects")
app.add_typer(new_app, name="new")


@new_app.command("agent")
def new_agent(name: str) -> None:
    """Scaffold a new agent project with pyproject, tests, and CI."""
    agent_path = Path(name)
    if agent_path.exists():
        abort(f"Directory {name} already exists")

    # Create project structure
    agent_path.mkdir()
    (agent_path / "src").mkdir()
    (agent_path / "tests").mkdir()
    (agent_path / "src" / name.replace("-", "_")).mkdir()

    # Create pyproject.toml
    pyproject_content = f"""[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "0.1.0"
description = "Agent: {name}"
requires-python = ">=3.12"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "mypy>=1.10",
    "ruff>=0.6.0",
    "pytest-cov>=5.0",
]

[tool.ruff]
target-version = "py312"
src = ["src", "tests"]
line-length = 100

[tool.ruff.lint]
select = ["E","F","I","UP","B","A","C4","SIM","PERF","RUF100"]

[tool.mypy]
python_version = "3.12"
files = ["src"]
strict = true
"""
    (agent_path / "pyproject.toml").write_text(pyproject_content)

    # Create basic module
    module_content = f'''"""
{name} agent module
"""

def main():
    print("Hello from {name}!")

if __name__ == "__main__":
    main()
'''
    (agent_path / "src" / name.replace("-", "_") / "__init__.py").write_text(
        module_content
    )

    # Create basic test
    test_content = f'''"""Tests for {name}"""

def test_basic():
    assert True
'''
    (agent_path / "tests" / "test_basic.py").write_text(test_content)

    # Create README
    readme_content = f"""# {name}

Agent project scaffolded with Command Deck.

## Setup

```bash
pip install -e .[dev]
```

## Quality Gates

```bash
ruff check .
mypy src
pytest
```
"""
    (agent_path / "README.md").write_text(readme_content)

    ok(f"Agent {name} scaffolded successfully!")
    info(f"Next: cd {name} && pip install -e .[dev]")


# --------------------------
# qa/* — quality gates
# --------------------------
qa_app = typer.Typer(help="Quality assurance: lint, type, test, all")
app.add_typer(qa_app, name="qa")


@qa_app.command("lint")
def qa_lint() -> None:
    """Run ruff check on the current directory."""
    result = subprocess.run([sys.executable, "-m", "ruff", "check", "."])
    raise typer.Exit(result.returncode // 256)


@qa_app.command("type")
def qa_type() -> None:
    """Run mypy type checking on src/."""
    result = subprocess.run([sys.executable, "-m", "mypy", "src"])
    raise typer.Exit(result.returncode // 256)


@qa_app.command("test")
def qa_test() -> None:
    """Run pytest on the current directory."""
    result = subprocess.run([sys.executable, "-m", "pytest"])
    raise typer.Exit(result.returncode // 256)


@qa_app.command("all")
def qa_all() -> None:
    """Run all quality gates: lint, type, test."""
    commands = [
        (["python", "-m", "ruff", "check", "."], "lint"),
        (["python", "-m", "mypy", "src"], "type"),
        (["python", "-m", "pytest"], "test"),
    ]

    failed = []
    for cmd, name in commands:
        info(f"Running {name}...")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            failed.append(name)

    if failed:
        abort(f"Quality gates failed: {', '.join(failed)}")
    ok("All quality gates passed!")


# Utility stubs (replace with your real logging/feedback)
def info(msg):
    print(f"[INFO] {msg}")


def ok(msg):
    print(f"[OK] {msg}")


def abort(msg):
    print(f"[ABORT] {msg}")
    raise typer.Exit(1)


# --------------------------
# ship/* — build & release
# --------------------------
ship_app = typer.Typer(help="Build wheels/images and cut releases")
app.add_typer(ship_app, name="ship")


@ship_app.command("build")
@ship_app.command("build")
def ship_build() -> None:
    """Build wheel + sdist for the current project."""
    try:
        # Try to build directly
        result = subprocess.run([sys.executable, "-m", "build"])
        if result.returncode != 0:
            # If build module not found, install it first
            info("Installing build module...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "build"], check=True
            )
            result = subprocess.run([sys.executable, "-m", "build"], check=True)
        ok("Build completed successfully")
    except subprocess.CalledProcessError:
        abort("Build failed")


@ship_app.command("release")
def ship_release(
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview release without publishing"
    )
) -> None:
    """Cut a release: tag, changelog, (optionally) publish to PyPI."""
    steps = [
        [sys.executable, "-m", "pip", "install", "-U", "pip", "build", "twine"],
        [sys.executable, "-m", "build"],
        [sys.executable, "-m", "twine", "check", "dist/*"],
    ]
    if not dry_run:
        steps.append([sys.executable, "-m", "twine", "upload", "dist/*"])

    if dry_run:
        info("DRY RUN - would execute:")
        for cmd in steps:
            info(f"  → {' '.join(cmd)}")
        return

    for cmd in steps:
        info(f"→ {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            abort("Release step failed")
    ok("Release flow completed")


# --------------------------
# nas/* — stubs for NAS deck integration
# --------------------------
nas_app = typer.Typer(help="NAS deck: sync/backup/validate stubs (fill in your infra)")
app.add_typer(nas_app, name="nas")


@nas_app.command("status")
def nas_status(config: Path | None = None) -> None:
    """Show NAS targets from a config file (YAML/JSON)."""
    if not config:
        typer.echo("No config provided. Example keys: mounts, shares, backups")
        raise typer.Exit(0)
    data = json.loads(config.read_text()) if config.suffix == ".json" else {}
    typer.echo(json.dumps({"detected": list(data.keys())}, indent=2))


@nas_app.command("sync")
def nas_sync(source: Path, target: Path) -> None:
    """Local rsync-style copy (placeholder for your real NAS sync)."""
    if target.exists() and any(target.iterdir()):
        info("target exists; copying into it")
    shutil.copytree(source, target, dirs_exist_ok=True)
    ok(f"synced {source} → {target}")


@nas_app.command("backup")
def nas_backup(path: Path, out: Path) -> None:
    """Create a compressed archive as a cheap local backup artifact."""
    archive = shutil.make_archive(str(out), "zip", root_dir=path)
    ok(f"backup archive created: {archive}")


@nas_app.command("restore")
def nas_restore(archive: Path, out: Path) -> None:
    """Restore a backup archive (zip) to a target directory."""
    shutil.unpack_archive(str(archive), extract_dir=out)
    ok(f"restored {archive} → {out}")


@nas_app.command("init")
def nas_init() -> None:
    """Write example NAS config (nas.config.example.yaml) to current directory."""
    config_content = """# NAS Configuration Example
# Supports both YAML (if pyyaml installed) and JSON formats

sync_targets:
  artifacts:
    source: "./artifacts"
    target: "/mnt/work/agents/artifacts" 
    excludes:
      - "**/__pycache__/**"
      - "**/*.tmp"
      - "**/.DS_Store"
    checksum: true
  
  backups:
    source: "./data"
    target: "/mnt/backups/data"
    excludes:
      - "*.log"
      - "temp/**"
    checksum: false

backup_targets:
  daily:
    path: "./workspace"
    archive_name: "workspace_backup"
    excludes:
      - "node_modules/**"
      - ".git/**"
      - "**/*.tmp"
"""
    config_path = Path("nas.config.example.yaml")
    config_path.write_text(config_content)
    ok(f"NAS config example written to {config_path}")


@nas_app.command("verify")
def nas_verify(target: Path) -> None:
    """Verify target directory against .manifest.json checksums."""
    manifest_path = target / ".manifest.json"
    if not manifest_path.exists():
        abort(f"No manifest found at {manifest_path}")

    manifest = json.loads(manifest_path.read_text())
    failures = []

    for file_path, expected_hash in manifest.get("checksums", {}).items():
        full_path = target / file_path
        if not full_path.exists():
            failures.append(f"Missing file: {file_path}")
            continue

        import hashlib

        actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            failures.append(f"Checksum mismatch: {file_path}")

    if failures:
        for failure in failures:
            typer.echo(f"❌ {failure}")
        abort(f"Verification failed: {len(failures)} issues found")

    ok("All checksums verified successfully")


@nas_app.command("plan")
def nas_plan(
    config: Path = typer.Option("nas.yaml", help="NAS config file (YAML/JSON)")
) -> None:
    """Show what nas run would do (dry-run plan)."""
    if not config.exists():
        abort(f"Config file not found: {config}. Run 'deck nas init' first.")

    try:
        # Try YAML first, fall back to JSON
        import yaml

        config_data = yaml.safe_load(config.read_text())
    except ImportError:
        config_data = json.loads(config.read_text())
    except Exception as e:
        abort(f"Failed to parse config: {e}")

    plan = {"sync_operations": [], "backup_operations": [], "checksums_required": []}

    # Plan sync operations
    for name, target in config_data.get("sync_targets", {}).items():
        source = Path(target["source"]).resolve()
        dest = Path(target["target"]).resolve()
        plan["sync_operations"].append(
            {
                "name": name,
                "source": str(source),
                "target": str(dest),
                "checksum": target.get("checksum", False),
                "excludes": target.get("excludes", []),
            }
        )
        if target.get("checksum"):
            plan["checksums_required"].append(str(dest))

    # Plan backup operations
    for name, target in config_data.get("backup_targets", {}).items():
        source = Path(target["path"]).resolve()
        archive_name = target.get("archive_name", name)
        plan["backup_operations"].append(
            {
                "name": name,
                "source": str(source),
                "archive": f"{archive_name}.zip",
                "excludes": target.get("excludes", []),
            }
        )

    typer.echo(json.dumps(plan, indent=2))


@nas_app.command("run")
def nas_run(
    config: Path = typer.Option("nas.yaml", help="NAS config file (YAML/JSON)")
) -> None:
    """Execute NAS plan: sync + backup + verify with SHA256 manifest."""
    if not config.exists():
        abort(f"Config file not found: {config}. Run 'deck nas init' first.")

    try:
        # Try YAML first, fall back to JSON
        import yaml

        config_data = yaml.safe_load(config.read_text())
    except ImportError:
        config_data = json.loads(config.read_text())
    except Exception as e:
        abort(f"Failed to parse config: {e}")

    import hashlib

    # Execute sync operations
    for name, target in config_data.get("sync_targets", {}).items():
        source = Path(target["source"])
        dest = Path(target["target"])

        info(f"Syncing {name}: {source} → {dest}")

        # Simple copy operation (replace with rsync in production)
        if source.exists():
            dest.mkdir(parents=True, exist_ok=True)
            if source.is_file():
                shutil.copy2(source, dest / source.name)
            else:
                shutil.copytree(source, dest, dirs_exist_ok=True)

        # Generate manifest if checksums required
        if target.get("checksum", False):
            manifest = {"checksums": {}}
            for file_path in dest.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(dest)
                    checksum = hashlib.sha256(file_path.read_bytes()).hexdigest()
                    manifest["checksums"][str(rel_path)] = checksum

            manifest_path = dest / ".manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2))
            info(f"Generated manifest: {manifest_path}")

    # Execute backup operations
    for name, target in config_data.get("backup_targets", {}).items():
        source = Path(target["path"])
        archive_name = target.get("archive_name", name)

        if source.exists():
            info(f"Creating backup {name}: {source} → {archive_name}.zip")
            shutil.make_archive(archive_name, "zip", root_dir=source)
            ok(f"Backup created: {archive_name}.zip")

    ok("NAS operations completed successfully")


# --------------------------
# repos/* — work across multiple repositories
# --------------------------
repos_app = typer.Typer(help="Work across many repos: discover, plan, run deck tasks")
app.add_typer(repos_app, name="repos")


def _repo_roots_from_env() -> list[Path]:
    """Get repository root paths from DECK_REPOS environment variable."""
    env = os.getenv("DECK_REPOS", "").strip()
    if not env:
        return []
    return [Path(p).expanduser().resolve() for p in env.split(":") if p]


def _discover_repos(roots: list[Path]) -> list[Path]:
    """Discover all git repositories under the given root paths."""
    repos = []
    for root in roots:
        if not root.exists():
            continue
        for git_dir in root.rglob(".git"):
            if git_dir.is_dir():
                repos.append(git_dir.parent)
    return repos


@repos_app.command("list")
def repos_list() -> None:
    """List all git repos under DECK_REPOS (colon-separated paths)."""
    roots = _repo_roots_from_env()
    repos = sorted({str(p) for p in _discover_repos(roots)})
    result = {"roots": [str(r) for r in roots], "repos": repos, "count": len(repos)}
    typer.echo(json.dumps(result, indent=2))


@repos_app.command("qa")
def repos_qa(task: str = "all") -> None:
    """Run deck qa tasks across all discovered repos (experimental)."""
    if task not in ["lint", "type", "test", "all"]:
        abort(f"Invalid task: {task}. Use: lint, type, test, or all")

    roots = _repo_roots_from_env()
    repos = _discover_repos(roots)

    if not repos:
        abort(
            "No repos found under DECK_REPOS. Set it like: export DECK_REPOS=~/code:~/work/repos"
        )

    failures = {}
    for repo in repos:
        info(f"→ {repo} :: qa {task}")
        # Use subprocess instead of os.system for better error handling
        cmd = ["python3", "-m", "command_deck", "qa", task]
        result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)

        if result.returncode != 0:
            failures[str(repo)] = {
                "return_code": result.returncode,
                "stderr": result.stderr.strip() if result.stderr else "",
                "stdout": result.stdout.strip() if result.stdout else "",
            }

    if failures:
        typer.echo(json.dumps({"failed": failures}, indent=2))
        abort(f"QA failed for {len(failures)} repos")

    ok(f"QA {task} succeeded for all {len(repos)} repos")


# --------------------------
# Entry
# --------------------------
def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
