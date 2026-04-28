# -*- coding: utf-8 -*-
"""Ejecución maestra del pipeline WRF."""

from modules.logger import LOGGER
from wrf_humedad import main as run_humedad
from wrf_precipitacion import main as run_precipitacion
from wrf_temperatura import main as run_temperatura
from wrf_viento import main as run_viento


PIPELINES = [
    ("temperatura", run_temperatura),
    ("humedad_relativa", run_humedad),
    ("precipitacion", run_precipitacion),
    ("viento", run_viento),
]


def main() -> None:
    LOGGER.info("INF-MASTER-001", "Inicio de ejecución maestra del pipeline WRF")
    errores = []

    for nombre, funcion in PIPELINES:
        try:
            LOGGER.info("INF-MASTER-002", f"Inicio de subproceso: {nombre}")
            funcion()
            LOGGER.info("INF-MASTER-003", f"Subproceso completado: {nombre}")
        except Exception as exc:
            errores.append((nombre, str(exc)))
            LOGGER.error("ERR-MASTER-001", f"Fallo en subproceso {nombre}: {exc}")

    if errores:
        detalle = "; ".join([f"{nombre}: {error}" for nombre, error in errores])
        LOGGER.error("ERR-MASTER-999", f"Ejecución maestra finalizada con errores: {detalle}")
        raise RuntimeError(detalle)

    LOGGER.info("INF-MASTER-999", "Ejecución maestra finalizada correctamente")


if __name__ == "__main__":
    main()
