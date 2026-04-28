# -*- coding: utf-8 -*-
"""Carga de pronósticos WRF de temperatura desde TIFF a PostgreSQL."""

from modules.processor import VariableConfig, WRFPipelineProcessor


VARIABLE = VariableConfig(
    nombre="temperatura",
    codigo_base="TEMP",
    carpeta_relativa="Ecuador/temp/3horas/tif",
    tabla_pron="_029036601h",
    patron_archivo=r"(\d{4}-\d{2}-\d{2})_(\d{2})h(\d{2})_temperatura\.tif",
)


def main() -> None:
    WRFPipelineProcessor(VARIABLE).run()


if __name__ == "__main__":
    main()
