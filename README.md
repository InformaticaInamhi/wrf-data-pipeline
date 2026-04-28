# wrf-data-pipeline

Pipeline para la carga automatizada de variables del modelo WRF desde archivos TIFF almacenados en SMB hacia tablas PostgreSQL del esquema `forecast_wrf`.

## Objetivo

Este repositorio centraliza el proceso de ingestión de cuatro variables del modelo WRF:

- temperatura
- humedad relativa
- precipitación
- magnitud de viento

Cada variable cuenta con su propio script de ejecución, pero todas comparten la misma arquitectura de configuración, conexión, logging y carga a base de datos.

## Estructura del proyecto

```text
wrf-data-pipeline/
├── config.ini
├── requirements.txt
├── README.md
└── main/
    ├── run_all.py
    ├── wrf_temperatura.py
    ├── wrf_humedad.py
    ├── wrf_precipitacion.py
    ├── wrf_viento.py
    ├── logs/
    └── modules/
        ├── __init__.py
        ├── config_loader.py
        ├── logger.py
        ├── connections.py
        └── processor.py
```

## Archivos principales

### `config.ini`
Archivo de configuración externo ubicado en la raíz del proyecto. Contiene los parámetros sensibles y configurables del pipeline, incluyendo:

- credenciales SMB
- credenciales PostgreSQL
- configuración general del proceso
- parámetros auxiliares de CORS y correo

### `requirements.txt`
Lista de dependencias del proyecto.

### `main/run_all.py`
Script maestro que ejecuta las cuatro variables de forma secuencial.

### Scripts por variable

- `main/wrf_temperatura.py`
- `main/wrf_humedad.py`
- `main/wrf_precipitacion.py`
- `main/wrf_viento.py`

Cada uno define únicamente la configuración particular de su variable:

- nombre lógico
- tabla destino
- carpeta SMB
- patrón de nombre de archivo
- código base para logging

### `main/modules/processor.py`
Implementa el procesador genérico reutilizable para todas las variables.

### `main/modules/logger.py`
Implementa el sistema de logs en formato ELF.

### `main/modules/connections.py`
Centraliza las conexiones a SMB y PostgreSQL.

## Variables procesadas

| Variable | Carpeta SMB | Tabla PostgreSQL |
|---|---|---|
| Temperatura | `Ecuador/temp/3horas/tif` | `_029036601h` |
| Humedad relativa | `Ecuador/hr/3horas/tif` | `_009016601h` |
| Precipitación | `Ecuador/prec/3horas/tif` | `_017146601h` |
| Viento | `Ecuador/viento/3horas/tif` | `_037116601h` |

## Lógica del proceso

1. Se conecta al recurso SMB.
2. Se identifica la carpeta más reciente dentro de `MODELO_WRF`.
3. Se listan los archivos TIFF de la variable correspondiente.
4. Se ignoran los dos primeros archivos.
5. Los archivos restantes se asignan secuencialmente a los horizontes `3h` hasta `72h`.
6. Cada raster se lee en memoria y se aplana.
7. Los valores se insertan o actualizan por `fecha_dato` e `id_estacion`.
8. El proceso registra todos los eventos en logs diarios.

## Formato de logs

Cada línea del log usa el formato ELF definido para el proyecto:

```text
Fecha y Hora | Tipo | Direccion IP | Codigo | Mensaje | Usuario | Contexto
```

Ejemplo:

```text
2026-04-23 10:15:30 | INFO | N/A | INF-TEMP-008 | Archivo 2026-04-23_06h00_temperatura.tif procesado y asociado al horizonte 3h | wrf_pipeline | archivo: processor.py, clase: WRFPipelineProcessor, metodo: run, linea: 142
```

### Niveles permitidos

- ERROR
- WARNING
- INFO
- DEBUG

## Instalación

Crear entorno e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Antes de ejecutar, editar `config.ini` con credenciales reales.

## Ejecución individual

```bash
cd main
python wrf_temperatura.py
python wrf_humedad.py
python wrf_precipitacion.py
python wrf_viento.py
```

## Ejecución maestra

```bash
cd main
python run_all.py
```

## Ejecución programada con crontab

Ejemplo cada 3 horas:

```bash
0 */3 * * * cd /ruta/wrf-data-pipeline/main && /usr/bin/python3 run_all.py >> /ruta/wrf-data-pipeline/main/logs/cron_exec.log 2>&1
```

## Recomendaciones operativas

- no subir credenciales reales al repositorio
- agregar `config.ini` al `.gitignore` si el repositorio será compartido
- usar ramas para cambios antes de pasar a producción
- validar conectividad a SMB y PostgreSQL desde el servidor donde correrá el cron
- revisar diariamente los logs en `main/logs/`

## Posibles mejoras futuras

- validación de archivos faltantes por horizonte
- envío de alertas por correo ante fallos críticos
- ejecución paralela controlada por variable
- pruebas unitarias para módulos comunes
- integración con GitHub Actions para validación sintáctica y despliegue
