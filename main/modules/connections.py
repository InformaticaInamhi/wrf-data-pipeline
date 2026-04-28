# -*- coding: utf-8 -*-
"""Conexiones reutilizables a SMB y PostgreSQL."""

from __future__ import annotations

from smb.SMBConnection import SMBConnection
import psycopg2

from .config_loader import get_int, get_section, get_str
from .logger import LOGGER


class ConnectionErrorPipeline(Exception):
    """Error de conexión del pipeline."""


SMB_PORT = 445


def create_smb_connection() -> SMBConnection:
    smb_cfg = get_section("SMB")
    conn = SMBConnection(
        smb_cfg.get("usuario"),
        smb_cfg.get("password"),
        smb_cfg.get("cliente"),
        smb_cfg.get("servidor"),
        domain=smb_cfg.get("dominio"),
        use_ntlm_v2=True,
        is_direct_tcp=True,
    )
    server = smb_cfg.get("servidor")
    if not conn.connect(server, SMB_PORT):
        LOGGER.error("ERR-CONN-001", f"No se pudo conectar al servidor SMB {server}")
        raise ConnectionErrorPipeline(f"No se pudo conectar al servidor SMB {server}")
    LOGGER.info("INF-CONN-001", f"Conexión SMB establecida con {server}")
    return conn


def create_postgres_connection():
    pg_cfg = get_section("POSTGRES")
    db_config = {
        "host": pg_cfg.get("host"),
        "database": pg_cfg.get("database"),
        "user": pg_cfg.get("user"),
        "password": pg_cfg.get("password"),
        "port": get_int("POSTGRES", "port", 5432),
    }
    try:
        conn_pg = psycopg2.connect(**db_config)
        cur_pg = conn_pg.cursor()
        LOGGER.info(
            "INF-CONN-002",
            f"Conexión PostgreSQL establecida con {db_config['host']}:{db_config['port']}",
        )
        return conn_pg, cur_pg
    except Exception as exc:
        LOGGER.error("ERR-CONN-002", f"Error al conectar PostgreSQL: {exc}")
        raise


def get_schema_name() -> str:
    return get_str("POSTGRES", "schema", "forecast_wrf")


def get_id_usuario() -> int:
    return get_int("GENERAL", "id_usuario", 1)
