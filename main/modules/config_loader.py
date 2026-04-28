# -*- coding: utf-8 -*-
"""Carga centralizada de configuración desde config.ini."""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config.ini"


class ConfigError(Exception):
    """Error de configuración del proyecto."""


_config: ConfigParser | None = None


def load_config() -> ConfigParser:
    global _config
    if _config is None:
        if not CONFIG_PATH.exists():
            raise ConfigError(f"No se encontró el archivo de configuración: {CONFIG_PATH}")

        parser = ConfigParser()
        parser.read(CONFIG_PATH, encoding="utf-8")
        _config = parser
    return _config


def get_section(section: str):
    parser = load_config()
    if section not in parser:
        raise ConfigError(f"La sección [{section}] no existe en {CONFIG_PATH.name}")
    return parser[section]


def get_str(section: str, key: str, fallback: str | None = None) -> str:
    return get_section(section).get(key, fallback)


def get_int(section: str, key: str, fallback: int | None = None) -> int:
    if fallback is None:
        return get_section(section).getint(key)
    return get_section(section).getint(key, fallback=fallback)


def get_bool(section: str, key: str, fallback: bool | None = None) -> bool:
    if fallback is None:
        return get_section(section).getboolean(key)
    return get_section(section).getboolean(key, fallback=fallback)
