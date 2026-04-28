# -*- coding: utf-8 -*-
"""Carga de pronósticos WRF de humedad relativa desde TIFF a PostgreSQL."""

from modules.processor import VariableConfig, WRFPipelineProcessor


VARIABLE = VariableConfig(
    nombre="humedad_relativa",
    codigo_base="HR",
    carpeta_relativa="Ecuador/hr/3horas/tif",
    tabla_pron="_009016601h",
    patron_archivo=r"(\d{4}-\d{2}-\d{2})_(\d{2})h(\d{2})_humedad\.tif",
)


def main() -> None:
    WRFPipelineProcessor(VARIABLE).run()


if __name__ == "__main__":
    main()
