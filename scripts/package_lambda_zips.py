#!/usr/bin/env python3
"""Build separate ZIP packages for the backend and Gradio UI Lambdas."""

import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
MAX_BACKEND_UNCOMPRESSED_SIZE = 250 * 1024 * 1024
MAX_UI_UNCOMPRESSED_SIZE = 240 * 1024 * 1024

BACKEND_DEPENDENCIES = (
    "boto3",
    "botocore",
    "eth-account",
    "mcp",
    "numpy",
    "openai",
    "openai-agents",
    "pydantic",
    "python-dotenv",
    "redis",
    "requests",
    "web3",
)

UI_DEPENDENCIES = (
    "gradio",
    "numpy",
    "pandas",
    "plotly",
    "pydantic",
    "python-dotenv",
    "redis",
)

BACKEND_SOURCE_FILES = (
    "lambda_function.py",
    "config.py",
    "model_config.py",
    "redis_store.py",
    "app_logging",
    "crypto_agents",
    "database",
    "entities",
    "instructions",
    "mcp_servers",
    "models",
    "output_models",
    "resources",
    "services",
    "tracers",
    "utils",
)

UI_SOURCE_FILES = (
    "app.py",
    "model_config.py",
    "redis_store.py",
    "output_models",
    "ui",
)


def _run(command: list[str], cwd: Path = PROJECT_ROOT) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _copy_sources(target: Path, source_names: tuple[str, ...]) -> None:
    for source_name in source_names:
        source = PROJECT_ROOT / source_name
        destination = target / source_name
        if source.is_dir():
            shutil.copytree(
                source,
                destination,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.db", "*.db-*", ".pytest_cache"
                ),
            )
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        else:
            raise FileNotFoundError(f"Required Lambda source path is missing: {source}")


def _install_dependencies(
    target: Path,
    constraints_file: Path,
    dependencies: tuple[str, ...],
) -> None:
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("Install uv before building Lambda packages")

    _run(
        [
            uv,
            "pip",
            "install",
            "--python",
            sys.executable,
            "--target",
            str(target),
            "--constraint",
            str(constraints_file),
            *dependencies,
        ]
    )


def _prune_development_files(package_root: Path) -> None:
    removable_directory_names = {
        "__pycache__",
        ".pytest_cache",
        "benchmarks",
        "tests",
    }
    directories = sorted(
        (
            path
            for path in package_root.rglob("*")
            if path.is_dir() and path.name in removable_directory_names
        ),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        shutil.rmtree(directory)

    # Type stubs and source maps are not needed at runtime.
    for pattern in ("*.pyi", "*.map"):
        for path in package_root.rglob(pattern):
            path.unlink()

    plotly_datasets = package_root / "plotly" / "package_data" / "datasets"
    if plotly_datasets.exists():
        shutil.rmtree(plotly_datasets)

    for relative_path in (
        "gradio/templates/node",
        "plotly/labextension",
        "plotly/package_data/widgetbundle.js",
    ):
        unused_path = package_root / relative_path
        if unused_path.is_dir():
            shutil.rmtree(unused_path)
        elif unused_path.is_file():
            unused_path.unlink()


def _uncompressed_size(package_root: Path) -> int:
    return sum(path.stat().st_size for path in package_root.rglob("*") if path.is_file())


def _write_zip(package_root: Path, zip_path: Path, maximum_size: int) -> None:
    uncompressed_size = _uncompressed_size(package_root)
    if uncompressed_size > maximum_size:
        raise RuntimeError(
            f"{zip_path.name} expands to {uncompressed_size / 1024 / 1024:.1f} MB; "
            f"the configured safe limit is {maximum_size / 1024 / 1024:.0f} MB"
        )

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as archive:
        for path in sorted(package_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package_root))

    print(
        f"Created {zip_path.relative_to(PROJECT_ROOT)} "
        f"({zip_path.stat().st_size / 1024 / 1024:.1f} MB zipped, "
        f"{uncompressed_size / 1024 / 1024:.1f} MB uncompressed)"
    )


def _prepare_backend_uv(package_root: Path) -> None:
    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("Install uv before building the backend Lambda package")

    uv_target = package_root / "bin" / "uv"
    uv_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(uv, uv_target)
    uv_target.chmod(0o755)


def _add_ui_bootstrap(package_root: Path) -> None:
    run_script = package_root / "run.sh"
    run_script.write_text(
        "#!/bin/sh\n"
        "cd /var/task\n"
        "exec python3 app.py\n",
        encoding="utf-8",
    )
    run_script.chmod(0o755)


def main() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Build Lambda ZIPs with Python 3.12")
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise RuntimeError("Build Lambda ZIPs on Linux x86_64 for the configured runtime")

    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("Install uv before building Lambda packages")

    with tempfile.TemporaryDirectory(prefix="crypto-trader-lambda-") as temp_dir:
        work_dir = Path(temp_dir)
        constraints_file = work_dir / "locked-requirements.txt"
        _run(
            [
                uv,
                "export",
                "--locked",
                "--no-dev",
                "--no-emit-project",
                "--no-hashes",
                "--format",
                "requirements-txt",
                "--output-file",
                str(constraints_file),
            ]
        )

        backend_root = work_dir / "backend"
        _install_dependencies(
            backend_root,
            constraints_file,
            BACKEND_DEPENDENCIES,
        )
        _copy_sources(backend_root, BACKEND_SOURCE_FILES)
        _prepare_backend_uv(backend_root)
        _prune_development_files(backend_root)
        _write_zip(
            backend_root,
            DIST_DIR / "backend.zip",
            MAX_BACKEND_UNCOMPRESSED_SIZE,
        )

        ui_root = work_dir / "ui"
        _install_dependencies(ui_root, constraints_file, UI_DEPENDENCIES)
        _copy_sources(ui_root, UI_SOURCE_FILES)
        _add_ui_bootstrap(ui_root)
        _prune_development_files(ui_root)
        _write_zip(
            ui_root,
            DIST_DIR / "ui.zip",
            MAX_UI_UNCOMPRESSED_SIZE,
        )


if __name__ == "__main__":
    main()
