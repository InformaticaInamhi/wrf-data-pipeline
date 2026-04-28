# -*- coding: utf-8 -*-
"""Procesador genérico para variables WRF desde TIFF hacia PostgreSQL."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from typing import Iterable

import rasterio
from psycopg2.extras import execute_values

from .config_loader import get_int, get_str
from .connections import create_postgres_connection, create_smb_connection, get_id_usuario, get_schema_name
from .logger import LOGGER

HORIZONTES = [f"{h}h" for h in range(3, 73, 3)]


@dataclass(frozen=True)
class VariableConfig:
    nombre: str
    codigo_base: str
    carpeta_relativa: str
    tabla_pron: str
    patron_archivo: str
    modo_asignacion: str = "skip_first_two"


class WRFPipelineProcessor:
    def __init__(self, variable: VariableConfig) -> None:
        self.variable = variable
        self.path_modelo = get_str("SMB", "ruta_modelo")
        self.nombre_compartido = get_str("SMB", "compartido")
        self.desfase_horas = get_int("GENERAL", "desfase_horas", 5)
        self.max_workers = get_int("GENERAL", "max_workers", 5)
        self.schema = get_schema_name()
        self.id_usuario = get_id_usuario()

    def _info(self, suffix: str, message: str) -> None:
        LOGGER.info(f"INF-{self.variable.codigo_base}-{suffix}", message)

    def _warning(self, suffix: str, message: str) -> None:
        LOGGER.warning(f"WAR-{self.variable.codigo_base}-{suffix}", message)

    def _error(self, suffix: str, message: str) -> None:
        LOGGER.error(f"ERR-{self.variable.codigo_base}-{suffix}", message)

    def buscar_ultima_carpeta(self, conn) -> tuple[str, datetime]:
        carpetas = [
            f
            for f in conn.listPath(self.nombre_compartido, self.path_modelo)
            if f.isDirectory and f.filename not in [".", ".."]
        ]
        if not carpetas:
            self._error("003", "No hay carpetas disponibles en MODELO_WRF")
            raise FileNotFoundError("No hay carpetas disponibles en MODELO_WRF")

        ultima = sorted(carpetas, key=lambda x: x.last_write_time, reverse=True)[0].filename
        fecha_dato = datetime.strptime(ultima[:10], "%Y-%m-%d")
        self._info("003", f"Última carpeta detectada: {ultima}")
        return ultima, fecha_dato

    def listar_archivos(self, conn, path_carpeta: str) -> list[str]:
        archivos = sorted(
            [
                f.filename
                for f in conn.listPath(self.nombre_compartido, path_carpeta)
                if not f.isDirectory and f.filename.endswith(".tif")
            ]
        )
        self._info("004", f"Total de archivos TIFF detectados para {self.variable.nombre}: {len(archivos)}")
        return archivos

    def _build_remote_path(self, archivo: str, path_carpeta: str) -> str:
        return str(PurePosixPath(path_carpeta) / archivo)

    def _procesar_un_archivo(self, conn, archivo: str, fecha_dato: datetime, path_carpeta: str, horizonte: str):
        if not re.match(self.variable.patron_archivo, archivo):
            self._warning("005", f"Formato inválido para archivo {archivo}")
            return False

        file_obj = io.BytesIO()
        conn.retrieveFile(self.nombre_compartido, self._build_remote_path(archivo, path_carpeta), file_obj)
        file_obj.seek(0)

        with rasterio.MemoryFile(file_obj.read()) as memfile:
            with memfile.open() as src:
                datos = src.read(1)
                valores = datos.flatten()

        filas = [(fecha_dato, float(v), i + 1, self.id_usuario) for i, v in enumerate(valores)]
        if not filas:
            self._warning("006", f"Archivo sin datos utilizables: {archivo}")
            return False

        return filas

    def _iter_assignments(self, archivos: list[str]) -> Iterable[tuple[str, str]]:
        if self.variable.modo_asignacion == "skip_first_two":
            for archivo in archivos[:2]:
                self._warning("007", f"Archivo no corresponde a ningún horizonte: {archivo}")
            archivos_validos = archivos[2: 2 + len(HORIZONTES)]
            return zip(archivos_validos, HORIZONTES)

        raise ValueError(f"Modo de asignación no soportado: {self.variable.modo_asignacion}")

    def run(self) -> None:
        self._info("001", f"Inicio de procesamiento para variable {self.variable.nombre}")
        conn = None
        conn_pg = None
        cur_pg = None
        try:
            conn = create_smb_connection()
            conn_pg, cur_pg = create_postgres_connection()
            ultima_carpeta, fecha_dato = self.buscar_ultima_carpeta(conn)
            path_carpeta_interna = f"{self.path_modelo}/{ultima_carpeta}/{self.variable.carpeta_relativa}"
            archivos = self.listar_archivos(conn, path_carpeta_interna)

            total_insertados = 0
            for archivo, horizonte in self._iter_assignments(archivos):
                conn_hilo = create_smb_connection()
                try:
                    filas = self._procesar_un_archivo(conn_hilo, archivo, fecha_dato, path_carpeta_interna, horizonte)
                finally:
                    conn_hilo.close()

                if not filas:
                    continue

                sql = f'''
                INSERT INTO {self.schema}.{self.variable.tabla_pron} (fecha_dato, "{horizonte}", id_estacion, id_usuario)
                VALUES %s
                ON CONFLICT (fecha_dato, id_estacion)
                DO UPDATE SET "{horizonte}" = EXCLUDED."{horizonte}";
                '''
                execute_values(cur_pg, sql, filas, template="(%s,%s,%s,%s)", page_size=1000)
                total_insertados += 1
                self._info("008", f"Archivo {archivo} procesado y asociado al horizonte {horizonte}")

            conn_pg.commit()
            self._info("999", f"Proceso finalizado para {self.variable.nombre}. Horizontes cargados: {total_insertados}")
        except Exception as exc:
            if conn_pg is not None:
                conn_pg.rollback()
            self._error("999", f"Fallo en el procesamiento de {self.variable.nombre}: {exc}")
            raise
        finally:
            if cur_pg is not None:
                cur_pg.close()
            if conn_pg is not None:
                conn_pg.close()
            if conn is not None:
                conn.close()
