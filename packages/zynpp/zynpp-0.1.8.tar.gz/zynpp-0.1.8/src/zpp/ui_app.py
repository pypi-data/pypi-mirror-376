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

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical():
                yield self.code_view
            with Vertical():
                yield self.box_compile
                yield self.box_run
                yield self.box_hints
        yield Footer()

    async def on_mount(self) -> None:
        self.title = f"ZPP UI - {self.source.name}"
        self.code_view.code = self.source.read_text(encoding="utf-8", errors="ignore")
        self.code_view.path = str(self.source)
        await self.refresh_metrics()

    async def refresh_metrics(self) -> None:
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
        if comp.success:
            runm = await asyncio.to_thread(self._run)
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


def run_ui(source: Path) -> None:
    ZPPApp(source).run()


