from __future__ import annotations

import time
from dataclasses import dataclass

import psutil

from .utils import human_bytes, human_seconds


@dataclass
class CompileMetrics:
    success: bool
    return_code: int
    wall_time_s: float
    binary_size_bytes: int | None
    compiler: str
    flags: str
    stdout: str
    stderr: str


@dataclass
class RunMetrics:
    success: bool
    return_code: int
    wall_time_s: float | None
    cpu_time_s: float | None
    peak_rss_bytes: int | None
    stdout: str
    stderr: str

    def as_human(self) -> dict[str, str]:
        return {
            "wall": human_seconds(self.wall_time_s),
            "cpu": human_seconds(self.cpu_time_s),
            "rss": human_bytes(self.peak_rss_bytes),
            "exit": str(self.return_code),
        }


def sample_peak_rss(process: psutil.Process, interval_s: float = 0.05) -> int:
    peak = 0
    try:
        while True:
            try:
                mem = process.memory_info().rss
                if mem > peak:
                    peak = mem
            except Exception:
                pass
            if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                break
            time.sleep(interval_s)
    except Exception:
        pass
    return peak


def measure_process(pid: int, start_time: float) -> RunMetrics:
    proc = psutil.Process(pid)
    peak_rss = sample_peak_rss(proc)
    try:
        cpu_times = proc.cpu_times()
        cpu_time = float(cpu_times.user + cpu_times.system)
    except Exception:
        cpu_time = None
    end = time.perf_counter()
    wall = end - start_time
    return RunMetrics(
        success=True,
        return_code=0,
        wall_time_s=wall,
        cpu_time_s=cpu_time,
        peak_rss_bytes=peak_rss,
        stdout="",
        stderr="",
    )


