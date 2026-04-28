# -*- coding: utf-8 -*-
"""Logger en formato ELF para el pipeline WRF."""

from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config_loader import get_str

EC_TZ = ZoneInfo("America/Guayaquil")
ALLOWED_LEVELS = {"ERROR", "WARNING", "INFO", "DEBUG"}
BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / get_str("GENERAL", "log_dir", "main/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


class LogError(Exception):
    """Error del sistema de logs."""


class ELFLogger:
    def __init__(self, user: str, ip: str) -> None:
        self.user = user
        self.ip = ip

    @staticmethod
    def _now_str() -> str:
        return datetime.now(EC_TZ).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _log_file_path() -> Path:
        filename = f"app_{datetime.now(EC_TZ).strftime('%Y_%m_%d')}.log"
        return LOG_DIR / filename

    @staticmethod
    def _build_context(stack_depth: int = 2) -> str:
        frame = inspect.stack()[stack_depth]
        archivo = Path(frame.filename).name
        clase = "N/A"
        self_obj = frame.frame.f_locals.get("self")
        if self_obj is not None:
            clase = self_obj.__class__.__name__
        metodo = frame.function
        linea = frame.lineno
        return f"archivo: {archivo}, clase: {clase}, metodo: {metodo}, linea: {linea}"

    def write(self, level: str, code: str, message: str, *, stack_depth: int = 2) -> None:
        level = level.upper().strip()
        if level not in ALLOWED_LEVELS:
            raise LogError(f"Nivel de log no permitido: {level}")

        clean_message = " ".join(str(message).split())[:300]
        context = self._build_context(stack_depth=stack_depth)
        line = (
            f"{self._now_str()} | {level} | {self.ip} | {code} | {clean_message} | "
            f"{self.user} | {context}"
        )
        log_path = self._log_file_path()
        with log_path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")
        print(line)

    def info(self, code: str, message: str) -> None:
        self.write("INFO", code, message, stack_depth=3)

    def warning(self, code: str, message: str) -> None:
        self.write("WARNING", code, message, stack_depth=3)

    def error(self, code: str, message: str) -> None:
        self.write("ERROR", code, message, stack_depth=3)

    def debug(self, code: str, message: str) -> None:
        self.write("DEBUG", code, message, stack_depth=3)


LOGGER = ELFLogger(
    user=get_str("GENERAL", "usuario_app", "wrf_pipeline"),
    ip=get_str("GENERAL", "ip", "N/A"),
)
