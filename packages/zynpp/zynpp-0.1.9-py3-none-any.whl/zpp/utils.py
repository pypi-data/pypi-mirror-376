from __future__ import annotations

import logging
import os
import platform
import shutil
import sys
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, cast

try:  # Python 3.11+
	import tomllib as toml_reader
except Exception:  # pragma: no cover
	import tomli as toml_reader

import tomli_w

ZPP_HOME = Path(os.environ.get("ZPP_HOME", Path.home() / ".zpp")).expanduser()
ZPP_CONFIG = ZPP_HOME / "config.toml"
ZPP_LOG_DIR = ZPP_HOME / "logs"


def ensure_dirs() -> None:
	ZPP_HOME.mkdir(parents=True, exist_ok=True)
	ZPP_LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str, level: int = logging.WARNING) -> logging.Logger:
	ensure_dirs()
	logger = logging.getLogger(f"zpp.{name}")
	if logger.handlers:
		return logger
	logger.setLevel(level)
	log_path = ZPP_LOG_DIR / "zpp.log"
	handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3)
	formatter = logging.Formatter(
		fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	# Also log warnings+ to stderr in human sessions
	stderr_handler = logging.StreamHandler(sys.stderr)
	stderr_handler.setLevel(logging.WARNING)
	stderr_handler.setFormatter(formatter)
	logger.addHandler(stderr_handler)
	return logger


LOGGER = get_logger("core")


def is_windows() -> bool:
	return platform.system() == "Windows"


@dataclass
class OSInfo:
	system: str
	distro_like: str | None
	distro_id: str | None


def detect_os() -> OSInfo:
	system = platform.system()
	distro_like: str | None = None
	distro_id: str | None = None
	if system == "Linux":
		try:
			data: dict[str, str] = {}
			with open("/etc/os-release", encoding="utf-8") as f:
				for line in f:
					if "=" in line:
						k, v = line.strip().split("=", 1)
						data[k] = v.strip('"')
			distro_like = data.get("ID_LIKE")
			distro_id = data.get("ID")
		except Exception:
			pass
	return OSInfo(system=system, distro_like=distro_like, distro_id=distro_id)


def which(program: str) -> str | None:
	return shutil.which(program)


def human_bytes(num: int | None) -> str:
	if num is None:
		return "N/A"
	step = 1024.0
	for unit in ["B", "KB", "MB", "GB", "TB"]:
		if num < step:
			return f"{num:.0f} {unit}"
		num = int(num / step)
	return f"{num} PB"


def human_seconds(sec: float | None) -> str:
	if sec is None:
		return "N/A"
	if sec < 1e-3:
		return f"{sec * 1e6:.0f} µs"
	if sec < 1:
		return f"{sec * 1e3:.1f} ms"
	return f"{sec:.3f} s"


def read_text(path: Path) -> str:
	return path.read_text(encoding="utf-8", errors="ignore")


def write_text_atomic(path: Path, content: str) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	tmp = path.with_suffix(path.suffix + ".tmp")
	tmp.write_text(content, encoding="utf-8")
	os.replace(tmp, path)


def load_config() -> dict[str, Any]:
	ensure_dirs()
	if not ZPP_CONFIG.exists():
		return {}
	with open(ZPP_CONFIG, "rb") as f:
		return cast(dict[str, Any], toml_reader.load(f))


def save_config(cfg: dict[str, Any]) -> None:
	ensure_dirs()
	with open(ZPP_CONFIG, "wb") as f:
		tomli_w.dump(cfg, f)


def getenv_bool(name: str, default: bool = False) -> bool:
	v = os.environ.get(name)
	if v is None:
		return default
	return v.lower() in {"1", "true", "yes", "on"}


