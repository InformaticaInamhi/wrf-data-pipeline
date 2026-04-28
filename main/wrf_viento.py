# -*- coding: utf-8 -*-
"""Carga de pronósticos WRF de magnitud de viento desde TIFF a PostgreSQL."""

from modules.processor import VariableConfig, WRFPipelineProcessor


VARIABLE = VariableConfig(
    nombre="viento",
    codigo_base="VTO",
    carpeta_relativa="Ecuador/viento/3horas/tif",
    tabla_pron="_037116601h",
    patron_archivo=r"(\d{4}-\d{2}-\d{2})_(\d{2})h(\d{2})_magnitud_viento\.tif",
)


def main() -> None:
    WRFPipelineProcessor(VARIABLE).run()


if __name__ == "__main__":
    main()
