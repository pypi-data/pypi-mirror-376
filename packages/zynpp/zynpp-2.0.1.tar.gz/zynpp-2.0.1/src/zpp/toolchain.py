from __future__ import annotations

import os
import shlex
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path

from .metrics import CompileMetrics
from .utils import OSInfo, detect_os, get_logger, getenv_bool, which

LOGGER = get_logger("toolchain")


def find_compiler() -> str | None:
    for c in ("g++", "clang++"):
        p = which(c)
        if p:
            return p
    return None


def default_flags(
    release: bool = False,
    debug: bool = False,
    native: bool = False,
    extra_flags: str | None = None,
) -> list[str]:
    flags: list[str] = ["-std=c++17", "-O2", "-pipe", "-Wall", "-Wextra"]
    if debug:
        flags = ["-std=c++17", "-g", "-O0", "-Wall", "-Wextra"]
    if release:
        flags += ["-DNDEBUG", "-flto"]
    if native and not getenv_bool("ZPP_SAFE_MODE", False):
        flags += ["-march=native"]
    if extra_flags:
        flags += shlex.split(extra_flags)
    return flags


def output_binary_name(source_file: Path) -> Path:
    base = source_file.stem
    exe = base + (".exe" if os.name == "nt" else "")
    return Path("build") / exe


def compile_source(
    compiler: str,
    source_file: Path,
    output: Path | None = None,
    flags: Sequence[str] | None = None,
    timeout_s: float = 60.0,
) -> CompileMetrics:
    out_path = output or output_binary_name(source_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    argv = [compiler, str(source_file), "-o", str(out_path)] + list(flags or default_flags())
    t0 = time.perf_counter()
    p = subprocess.run(argv, text=True, capture_output=True, timeout=timeout_s)
    t1 = time.perf_counter()
    size = out_path.stat().st_size if out_path.exists() and p.returncode == 0 else None
    return CompileMetrics(
        success=p.returncode == 0,
        return_code=p.returncode,
        wall_time_s=t1 - t0,
        binary_size_bytes=size,
        compiler=Path(compiler).name,
        flags=" ".join(argv[3:]),
        stdout=p.stdout,
        stderr=p.stderr,
    )


def doctor() -> tuple[bool, list[str]]:
    ok = True
    messages: list[str] = []
    comp = find_compiler()
    if not comp:
        ok = False
        messages.append("No C++ compiler found (g++/clang++). Try: zpp install-gpp")
    else:
        messages.append(f"Compiler detected: {comp}")
    try:
        Path("build").mkdir(parents=True, exist_ok=True)
        messages.append("Writable build/ directory OK")
    except Exception as e:
        ok = False
        messages.append(f"Cannot create build/ directory: {e}")
    return ok, messages


def install_commands_for_os(info: OSInfo) -> list[str]:
    system = info.system
    distro_like = (info.distro_like or "").lower()
    distro_id = (info.distro_id or "").lower()
    cmds: list[str] = []
    if system == "Linux":
        if "debian" in distro_like or distro_id in {"debian", "ubuntu", "linuxmint"}:
            cmds = [
                "sudo apt-get update -y",
                "sudo apt-get install -y g++",
            ]
        elif distro_id in {"arch", "manjaro"} or "arch" in distro_like:
            cmds = ["sudo pacman -Sy --noconfirm gcc"]
        elif distro_id in {"fedora"}:
            cmds = ["sudo dnf install -y gcc-c++"]
        else:
            cmds = ["sudo apt-get update -y || true", "sudo apt-get install -y g++ || true"]
    elif system == "Darwin":
        cmds = [
            "xcode-select --install || true",
            "command -v brew >/dev/null 2>&1 && brew install gcc || true",
        ]
    elif system == "Windows":
        cmds = [
            "powershell -Command \"iwr get.scoop.sh -useb | iex; scoop install gcc\"",
            "choco install -y mingw --limit-output || echo Use Chocolatey to install MinGW-w64",
        ]
    return cmds


def install_gpp(dry_run: bool = False, yes: bool = False) -> tuple[bool, list[str]]:
    info = detect_os()
    cmds = install_commands_for_os(info)
    notes: list[str] = [f"Detected OS: {info.system} ({info.distro_id or '?'} | like {info.distro_like or '?'})"]
    if dry_run or not yes:
        notes.append("Dry run or --yes not specified. Will not execute.")
        notes += [f"Run: {c}" for c in cmds]
        return False, notes
    ok = True
    for c in cmds:
        try:
            p = subprocess.run(c, shell=True, text=True)
            if p.returncode != 0:
                ok = False
                notes.append(f"Command failed (exit {p.returncode}): {c}")
        except Exception as e:
            ok = False
            notes.append(f"Command error: {c} -> {e}")
    return ok, notes


