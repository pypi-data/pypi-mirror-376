# OptiData Core Package (optidata-core)

Paquete para OptiData que contiene funcionalidades para realizar una Conciliación con Pandas y Vaex.

## Descripción

Este es un paquete de Python para OptiData. Proporciona funcionalidades clave para realizar procesos de conciliación de datos utilizando las potentes librerías `pandas` y `vaex`. Además, incluye módulos para la interacción con bases de datos (MongoDB, Oracle), manejo de archivos (SFTP), y la creación de APIs (Flask).

## Características

*   Conciliación de datos de alto rendimiento con `pandas` y `vaex`.
*   Conectividad con bases de datos MongoDB y Oracle.
*   Transferencia segura de archivos a través de SFTP.
*   Capacidad para construir servicios web y APIs con `Flask` y `flask-restx`.
*   Programación de tareas con `APScheduler`.

## Requisitos

*   Python 3.9 o superior.

## Instalación

Para instalar las dependencias del proyecto, puedes usar el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Dependencias

El proyecto utiliza las siguientes dependencias:

- `APScheduler>=3.10.4`
- `chardet~=5.2.0`
- `cryptography~=42.0.5`
- `Fernet==1.0.1`
- `Flask-Bcrypt==1.0.1`
- `Flask>=3.0.2`
- `flask-restx>=1.3.0`
- `joblib>=1.3.2`
- `kafka-python>=2.0.2`
- `numpy>=1.26.4`
- `openpyxl>=3.1.2`
- `oracledb==2.1.1`
- `pandas>=2.2.1`
- `paramiko~=3.4.0`
- `pycryptodome==3.20.0`
- `pymongo==4.3.3`
- `pysftp==0.2.9`
- `retrying==1.3.4`
- `sqlalchemy==2.0.28`
- `vaex>=4.17.0`

## Autor

Gonzalo Torres Moya (<gtorres@optimisa.cl>)

## Licencia

Este proyecto está bajo la Licencia MIT.
