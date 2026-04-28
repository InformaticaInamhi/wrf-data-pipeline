# -*- coding: utf-8 -*-
"""Carga de pronósticos WRF de precipitación desde TIFF a PostgreSQL."""

from modules.processor import VariableConfig, WRFPipelineProcessor


VARIABLE = VariableConfig(
    nombre="precipitacion",
    codigo_base="PREC",
    carpeta_relativa="Ecuador/prec/3horas/tif",
    tabla_pron="_017146601h",
    patron_archivo=r"(\d{4}-\d{2}-\d{2})_(\d{2})h(\d{2})p\.tif",
)


def main() -> None:
    WRFPipelineProcessor(VARIABLE).run()


if __name__ == "__main__":
    main()
