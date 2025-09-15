from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .hints_ai import ai_enabled, get_ai_hints
from .hints_rule import generate_hints
from .runner import run_binary
from .toolchain import (
	compile_source,
	default_flags,
	doctor,
	find_compiler,
	install_gpp,
	output_binary_name,
)
from .utils import get_logger, getenv_bool, load_config, save_config

app = typer.Typer(add_completion=False, invoke_without_command=True, help="ZPP: C++ build/run + metrics + hints")
console = Console()
LOGGER = get_logger("cli")


def _require_file(path: Path) -> None:
	if not path.exists():
		console.print(f"[red]File not found:[/red] {path}")
		raise typer.Exit(code=2)


@app.command()
def version() -> None:
	console.print(f"zpp {__version__}")


def _quick_run(file: str, args: str | None, release: bool, debug: bool, flags: str | None, timeout: float) -> int:
	path = Path(file)
	_require_file(path)
	comp = find_compiler()
	if not comp:
		console.print("[red]No compiler found[/red]. Try: zpp install-gpp")
		return 3
	fl = default_flags(release=release, debug=debug, native=not getenv_bool("ZPP_SAFE_MODE", False), extra_flags=flags)
	cm = compile_source(comp, path, flags=fl)
	table = Table(title="Compile")
	table.add_column("field")
	table.add_column("value")
	table.add_row("compiler", cm.compiler)
	table.add_row("flags", cm.flags)
	table.add_row("time", f"{cm.wall_time_s:.3f}s")
	table.add_row("size", str(cm.binary_size_bytes or 0))
	table.add_row("exit", str(cm.return_code))
	console.print(table)
	if not cm.success:
		return 4
	bin_path = output_binary_name(path)
	rm = run_binary(bin_path, args=args.split() if args else None, timeout_s=timeout)
	table2 = Table(title="Run")
	table2.add_column("field")
	table2.add_column("value")
	table2.add_row("wall", f"{rm.wall_time_s:.3f}s")
	table2.add_row("cpu", str(rm.cpu_time_s or "N/A"))
	table2.add_row("rss", str(rm.peak_rss_bytes or "N/A"))
	table2.add_row("exit", str(rm.return_code))
	console.print(table2)
	return 0 if rm.return_code == 0 else 5


@app.command("quick")
def quick(
	file: str = typer.Argument(..., help="C++ source file"),
	args: str | None = typer.Option(None, help="Arguments to pass to program"),
	release: bool = typer.Option(False, help="Release flags"),
	debug: bool = typer.Option(False, help="Debug flags"),
	flags: str | None = typer.Option(None, help="Extra compiler flags"),
	timeout: float = typer.Option(10.0, help="Run timeout seconds"),
) -> None:
	code = _quick_run(file, args, release, debug, flags, timeout)
	raise typer.Exit(code=code)


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
	if ctx.invoked_subcommand is not None:
		return
	console.print("[yellow]Usage: zpp <file.cpp>[/yellow]")
	raise typer.Exit(code=0)


@app.command()
def build(
	file: str = typer.Argument(..., help="C++ source file"),
	release: bool = typer.Option(False, help="Release flags"),
	debug: bool = typer.Option(False, help="Debug flags"),
	flags: str | None = typer.Option(None, help="Extra compiler flags"),
) -> None:
	path = Path(file)
	_require_file(path)
	comp = find_compiler()
	if not comp:
		console.print("[red]No compiler found[/red]. Try: zpp install-gpp")
		raise typer.Exit(code=3)
	fl = default_flags(release=release, debug=debug, native=not getenv_bool("ZPP_SAFE_MODE", False), extra_flags=flags)
	cm = compile_source(comp, path, flags=fl)
	console.print(json.dumps(cm.__dict__, indent=2))
	raise typer.Exit(code=0 if cm.success else 4)


@app.command()
def run(
	target: str = typer.Argument(..., help="Binary or source file"),
	args: str | None = typer.Option(None, help="Arguments to pass to program"),
	timeout: float = typer.Option(10.0, help="Run timeout seconds"),
	ui: bool = typer.Option(True, help="Show split UI with live output and metrics"),
	watch: bool = typer.Option(False, help="Watch file for changes and auto-rerun"),
) -> None:
	path = Path(target)
	if path.suffix == ".cpp":
		comp = find_compiler()
		if not comp:
			console.print("[red]No compiler found[/red]. Try: zpp install-gpp")
			raise typer.Exit(code=3)
		cm = compile_source(comp, path)
		if not cm.success:
			raise typer.Exit(code=4)
		path = output_binary_name(path)
	if watch:
		if path.suffix == ".cpp":
			source_path = Path(target)
			from .watcher import watch_file
			
			def rerun() -> None:
				console.print(f"[yellow]File changed: {source_path}[/yellow]")
				comp = find_compiler()
				if comp:
					cm = compile_source(comp, source_path)
					if cm.success:
						bin_path = output_binary_name(source_path)
						rm = run_binary(bin_path, args=args.split() if args else None, timeout_s=timeout)
						console.print(f"[green]Rerun complete (exit {rm.return_code})[/green]")
			
			console.print(f"[blue]Watching {source_path} for changes... (Ctrl+C to stop)[/blue]")
			watch_file(source_path, rerun)
		else:
			console.print("[yellow]Watch mode only works with .cpp files[/yellow]")
		raise typer.Exit(code=0)
	
	if ui and sys.stdout.isatty():
		from .ui_app import run_split_ui

		run_split_ui(path, args.split() if args else None, watch)
		raise typer.Exit(code=0)
	rm = run_binary(path, args=args.split() if args else None, timeout_s=timeout)
	console.print(json.dumps(rm.__dict__, indent=2, default=str))
	raise typer.Exit(code=0 if rm.return_code == 0 else 5)


@app.command()
def bench(
	file: str = typer.Argument(...),
	repeat: int = typer.Option(10, min=1, max=1000),
	timeout: float = typer.Option(10.0),
) -> None:
	path = Path(file)
	_require_file(path)
	comp = find_compiler()
	if not comp:
		console.print("[red]No compiler found[/red]. Try: zpp install-gpp")
		raise typer.Exit(code=3)
	cm = compile_source(comp, path)
	if not cm.success:
		raise typer.Exit(code=4)
	bin_path = output_binary_name(path)
	times: list[float] = []
	for _ in range(repeat):
		rm = run_binary(bin_path, timeout_s=timeout)
		times.append(rm.wall_time_s or 0.0)
	avg = sum(times) / len(times)
	console.print(json.dumps({"repeat": repeat, "avg_wall_s": avg, "samples": times[:5]}, indent=2))


@app.command()
def mem(file: str = typer.Argument(...), timeout: float = typer.Option(10.0)) -> None:
	path = Path(file)
	_require_file(path)
	comp = find_compiler()
	if not comp:
		console.print("[red]No compiler found[/red]. Try: zpp install-gpp")
		raise typer.Exit(code=3)
	cm = compile_source(comp, path)
	if not cm.success:
		raise typer.Exit(code=4)
	bin_path = output_binary_name(path)
	rm = run_binary(bin_path, timeout_s=timeout)
	console.print(json.dumps({"wall_s": rm.wall_time_s, "peak_rss_bytes": rm.peak_rss_bytes}, indent=2))


@app.command()
def hint(file: str = typer.Argument(...), ai: bool = typer.Option(False, help="Enable AI if available")) -> None:
	path = Path(file)
	_require_file(path)
	hints = generate_hints(path)
	data = [h.__dict__ for h in hints]
	if ai and ai_enabled():
		try:
			ai_list = asyncio.run(get_ai_hints(path))
			data.extend([{
				"title": s.title,
				"rationale": s.rationale,
				"code_before_snippet": s.code_before_snippet,
				"code_after_snippet": s.code_after_snippet,
				"risk_notes": s.risk_notes,
				"estimated_speedup_pct": s.estimated_speedup_pct,
			} for s in ai_list])
		except Exception:
			pass
	console.print(json.dumps({"suggestions": data}, indent=2))


@app.command()
def ui(
	file: str = typer.Argument(...),
	watch: bool = typer.Option(False, help="Watch file for changes and auto-refresh"),
) -> None:
	from .ui_app import run_ui

	path = Path(file)
	_require_file(path)
	run_ui(path, watch)


@app.command(name="doctor")
def doctor_cmd() -> None:
	ok, messages = doctor()
	for m in messages:
		console.print('- ' + m)
	raise typer.Exit(code=0 if ok else 3)


@app.command(name="install-gpp")
def install_gpp_cmd(dry_run: bool = typer.Option(True), yes: bool = typer.Option(False)) -> None:
	ok, notes = install_gpp(dry_run=dry_run, yes=yes)
	for n in notes:
		console.print('- ' + n)
	raise typer.Exit(code=0 if ok else 3)


@app.command()
def init(path: str = typer.Argument("main.cpp")) -> None:
	p = Path(path)
	if p.exists():
		console.print(f"[yellow]{p} exists, skipping[/yellow]")
		raise typer.Exit(code=0)
	content = (
		"#include <bits/stdc++.h>\nusing namespace std;\nint main(){\n"
		"ios::sync_with_stdio(false); cin.tie(nullptr);\n"
		"cout<<\"Hello ZynPP!\\n\"; return 0; }\n"
	)
	p.write_text(content, encoding="utf-8")
	console.print(f"Created {p}")


@app.command()
def config(
	std: str | None = typer.Option(None, help="Default -std flag"),
	flags: str | None = typer.Option(None, help="Default flags"),
	ai_provider: str | None = typer.Option(None, help="openai/gemini/groq"),
	api_key: str | None = typer.Option(None, help="API key to store"),
) -> None:
	cfg = load_config()
	if std:
		cfg["std"] = std
	if flags:
		cfg["flags"] = flags
	if ai_provider:
		cfg["ai_provider"] = ai_provider
	if api_key:
		cfg["api_key_set"] = True
	save_config(cfg)
	console.print("Config saved at ~/.zpp/config.toml")


@app.command()
def selfcheck() -> None:
	hello = Path("build/_zpp_hello.cpp")
	hello.parent.mkdir(parents=True, exist_ok=True)
	hello.write_text("int main(){return 0;}", encoding="utf-8")
	comp = find_compiler()
	ok = True
	msgs: list[str] = []
	if not comp:
		ok = False
		msgs.append("No compiler found")
	else:
		from .toolchain import compile_source

		cm = compile_source(comp, hello)
		ok = ok and cm.success
		msgs.append(f"Compile hello: {'OK' if cm.success else 'FAIL'}")
	for m in msgs:
		console.print('- ' + m)
	raise typer.Exit(code=0 if ok else 3)


@app.command(name="self-update")
def self_update(
	index_url: str | None = typer.Option(None, help="Custom index URL (e.g., TestPyPI)"),
	pre: bool = typer.Option(False, help="Include pre-releases"),
) -> None:
	"""Upgrade zpp installed via pipx or pip."""
	use_pipx = shutil.which("pipx") is not None
	extra_args: list[str] = []
	if pre:
		extra_args += ["--pre"]
	try:
		if use_pipx:
			cmd = ["pipx", "upgrade", "zynpp"]
			if index_url:
				pip_args = f"--index-url {index_url} --extra-index-url https://pypi.org/simple"
				cmd += ["--pip-args", pip_args]
			code = subprocess.call(cmd)
		else:
			cmd = [sys.executable, "-m", "pip", "install", "-U", "zynpp"] + extra_args
			if index_url:
				cmd += ["--index-url", index_url, "--extra-index-url", "https://pypi.org/simple"]
			code = subprocess.call(cmd)
		if code == 0:
			console.print("[green]zpp updated successfully[/green]")
		else:
			console.print(f"[red]Update failed (exit {code})[/red]")
		raise typer.Exit(code=code)
	except KeyboardInterrupt:
		raise typer.Exit(code=1)


def main() -> None:  # entrypoint for console script and module
	# Provide `zpp <file.cpp>` default behavior here to avoid Click conflicts with subcommands
	subcommands = {
		"version",
		"quick",
		"build",
		"run",
		"bench",
		"mem",
		"hint",
		"ui",
		"doctor",
		"install-gpp",
		"init",
		"config",
		"selfcheck",
		"self-update",
	}
	argv = sys.argv[1:]
	if argv and argv[0] not in subcommands and not argv[0].startswith("-"):
		file_candidate = argv[0]
		try:
			code = _quick_run(file_candidate, None, False, False, None, 10.0)
			raise SystemExit(code)
		except typer.Exit as e:
			raise SystemExit(e.exit_code)
	app()


if __name__ == "__main__":
	main()


