from __future__ import annotations

import asyncio
from pathlib import Path

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static

from .hints_ai import ai_enabled, get_ai_hints
from .hints_rule import generate_hints
from .metrics import CompileMetrics, RunMetrics
from .toolchain import compile_source, find_compiler, output_binary_name


class OutputPane(Static):
    def __init__(self) -> None:
        super().__init__("")
        self._buffer: list[str] = []

    def clear(self) -> None:
        self._buffer.clear()
        self.update("")

    def write_line(self, line: str) -> None:
        self._buffer.append(line)
        self.update("\n".join(self._buffer[-1000:]))

    def write(self, data: str) -> None:
        if data.endswith("\n"):
            for part in data.splitlines():
                self.write_line(part)
        else:
            self.write_line(data)



class CodeView(Static):
    code = reactive("")
    path = reactive("")

    def render(self) -> Syntax:
        return Syntax(self.code, "cpp", theme="monokai", line_numbers=True)


class Box(Static):
    def __init__(self, title: str) -> None:
        super().__init__(f"[b]{title}[/b]\n")
        self.title = title

    def update_lines(self, lines: list[str]) -> None:
        self.update("[b]" + self.title + "[/b]\n" + "\n".join(lines))


class ZPPApp(App[None]):
    CSS = ""

    def __init__(self, source: Path) -> None:
        super().__init__()
        self.source = source
        self.code_view = CodeView()
        self.box_compile = Box("Compile")
        self.box_run = Box("Run")
        self.box_hints = Box("Hints")
        self.output_log = OutputPane()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical():
                yield self.code_view
            with Vertical():
                yield self.output_log
            with Vertical():
                yield self.box_compile
                yield self.box_run
                yield self.box_hints
        yield Footer()

    async def on_mount(self) -> None:
        self.title = f"ZynPP UI - {self.source.name}"
        self.code_view.code = self.source.read_text(encoding="utf-8", errors="ignore")
        self.code_view.path = str(self.source)
        await self.refresh_metrics()

    async def refresh_metrics(self) -> None:
        self.output_log.clear()
        comp = await asyncio.to_thread(self._compile)
        self.box_compile.update_lines(
            [
                f"compiler: {comp.compiler}",
                f"flags: {comp.flags}",
                f"time: {comp.wall_time_s:.3f}s",
                f"size: {comp.binary_size_bytes or 0} B",
                f"exit: {comp.return_code}",
            ]
        )
        if comp.stdout:
            for line in comp.stdout.splitlines():
                self.output_log.write_line(line)
        if comp.stderr:
            for line in comp.stderr.splitlines():
                self.output_log.write_line(line)
        if comp.success:
            runm = await asyncio.to_thread(self._run_stream)
            self.box_run.update_lines(
                [
                    f"wall: {runm.wall_time_s:.3f}s",
                    f"cpu: {runm.cpu_time_s if runm.cpu_time_s is not None else 'N/A'}",
                    f"rss: {runm.peak_rss_bytes if runm.peak_rss_bytes is not None else 'N/A'}",
                    f"exit: {runm.return_code}",
                ]
            )
        else:
            self.box_run.update_lines(["Run skipped (build failed)"])

        hints: list[str] = []
        rule_hints = await asyncio.to_thread(generate_hints, self.source)
        for h in rule_hints[:5]:
            hints.append(f"- {h.title}")
        if ai_enabled():
            try:
                ai = await asyncio.wait_for(get_ai_hints(self.source), timeout=6.0)
                for s in ai[:3]:
                    hints.append(f"AI: {s.title}")
            except Exception:
                pass
        if not hints:
            hints = ["No suggestions"]
        self.box_hints.update_lines(hints)

    def _compile(self) -> CompileMetrics:
        comp = find_compiler() or "g++"
        return compile_source(comp, self.source)

    def _run(self) -> RunMetrics:
        bin_path = output_binary_name(self.source)
        from .runner import run_binary

        return run_binary(bin_path)

    def _run_stream(self) -> RunMetrics:
        import subprocess
        import time as _time

        bin_path = output_binary_name(self.source)
        t0 = _time.perf_counter()
        try:
            p = subprocess.Popen([str(bin_path)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except Exception as e:  # pragma: no cover
            self.output_log.write_line(f"spawn error: {e}")
            return RunMetrics(False, 1, 0.0, None, None, "", str(e))
        out_buf: list[str] = []
        err_text = ""
        try:
            assert p.stdout is not None
            for line in p.stdout:
                out_buf.append(line)
                self.output_log.write(line)
        except Exception:
            pass
        code = p.wait()
        t1 = _time.perf_counter()
        return RunMetrics(
            success=code == 0,
            return_code=code,
            wall_time_s=t1 - t0,
            cpu_time_s=None,
            peak_rss_bytes=None,
            stdout="".join(out_buf),
            stderr=err_text,
        )


def run_ui(source: Path) -> None:
    ZPPApp(source).run()


class RunApp(App[None]):
    def __init__(self, binary: Path, args: list[str] | None = None) -> None:
        super().__init__()
        self.binary = binary
        self.args = args or []
        self.output_log = OutputPane()
        self.box_run = Box("Run")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical():
                yield self.output_log
            with Vertical():
                yield self.box_run
        yield Footer()

    async def on_mount(self) -> None:
        await asyncio.to_thread(self._run_stream)

    def _run_stream(self) -> None:
        import subprocess
        import time as _time

        t0 = _time.perf_counter()
        try:
            p = subprocess.Popen([str(self.binary)] + self.args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        except Exception as e:
            self.output_log.write_line(f"spawn error: {e}")
            self.box_run.update_lines(["exit: 1"])
            return
        try:
            assert p.stdout is not None
            for line in p.stdout:
                self.output_log.write(line)
        except Exception:
            pass
        code = p.wait()
        t1 = _time.perf_counter()
        self.box_run.update_lines([
            f"wall: {t1 - t0:.3f}s",
            f"exit: {code}",
        ])


def run_split_ui(binary: Path, args: list[str] | None = None) -> None:
    RunApp(binary, args or []).run()


