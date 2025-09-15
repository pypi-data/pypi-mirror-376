from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path


def watch_file(file_path: Path, callback: Callable[[], None], interval: float = 0.5) -> None:
    """Simple file watcher that calls callback when file is modified."""
    if not file_path.exists():
        return
    
    last_mtime = file_path.stat().st_mtime
    
    while True:
        try:
            time.sleep(interval)
            if not file_path.exists():
                continue
            
            current_mtime = file_path.stat().st_mtime
            if current_mtime > last_mtime:
                last_mtime = current_mtime
                try:
                    callback()
                except KeyboardInterrupt:
                    break
                except Exception:
                    continue
        except KeyboardInterrupt:
            break
        except Exception:
            continue
