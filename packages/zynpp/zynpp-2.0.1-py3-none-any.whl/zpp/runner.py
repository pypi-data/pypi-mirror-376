from __future__ import annotations

import platform
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .metrics import RunMetrics


def safe_run(cmd: Sequence[str], timeout_s: float) -> tuple[int, str, str]:
    p: subprocess.Popen[str] | None = None
    kwargs: dict[str, Any] = dict(text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if platform.system() == "Windows":
            p = subprocess.Popen(cmd, **kwargs)
        else:
            import os

            p = subprocess.Popen(cmd, preexec_fn=os.setsid, **kwargs)
        assert p is not None
        out, err = p.communicate(timeout=timeout_s)
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        if p is not None:
            try:
                if platform.system() == "Windows":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    try:
                        import os
                        import signal

                        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                    except Exception:
                        p.kill()
            except Exception:
                pass
        return 124, "", "Timeout"
    except Exception as e:
        return 1, "", str(e)


def run_binary(binary_path: Path, args: list[str] | None = None, timeout_s: float = 10.0) -> RunMetrics:
    argv = [str(binary_path)] + (args or [])
    t0 = time.perf_counter()
    code, out, err = safe_run(argv, timeout_s=timeout_s)
    t1 = time.perf_counter()
    wall = t1 - t0
    # CPU and RSS not sampled here; caller may use psutil sampling for precision.
    success = code == 0
    return RunMetrics(
        success=success,
        return_code=code,
        wall_time_s=wall,
        cpu_time_s=None,
        peak_rss_bytes=None,
        stdout=out,
        stderr=err,
    )


