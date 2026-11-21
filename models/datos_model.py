import os
import json
import pyodbc
from dotenv import load_dotenv

load_dotenv()


def obtener_conexion():
    servidor = os.getenv("DB_SERVER")
    base_datos = os.getenv("DB_NAME")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    trusted = os.getenv("DB_TRUSTED", "yes").lower()

    if trusted == "yes":
        cadena = (
            f"DRIVER={{{driver}}};"
            f"SERVER={servidor};"
            f"DATABASE={base_datos};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
    else:
        usuario = os.getenv("DB_USER")
        clave = os.getenv("DB_PASSWORD")
        cadena = (
            f"DRIVER={{{driver}}};"
            f"SERVER={servidor};"
            f"DATABASE={base_datos};"
            f"UID={usuario};"
            f"PWD={clave};"
            "TrustServerCertificate=yes;"
        )

    return pyodbc.connect(cadena, timeout=3)


def guardar_registros(registros):
    conexion = None
    cursor = None
    insertados = 0

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        for registro in registros:
            # Identificador único real del programa según el JSON de la API
            identificador = str(registro.get("snies_programa") or "").strip()
            if not identificador:
                continue

            # Conversión segura de duración a entero
            duracion_raw = registro.get("duracion")
            try:
                duracion_num = int(float(duracion_raw)) if duracion_raw is not None else None
            except (ValueError, TypeError):
                duracion_num = None

            cursor.execute(
                """
                IF NOT EXISTS (
                    SELECT 1 FROM RegistrosAPI WHERE id_api = ?
                )
                INSERT INTO RegistrosAPI (
                    id_api,
                    universidad,
                    ubicacion,
                    direccion,
                    programas,
                    modalidad,
                    duracion,
                    periodo,
                    json_original
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                identificador,
                identificador,
                registro.get("universidad"),
                registro.get("ubicacion"),
                registro.get("direccion"),
                registro.get("programas"),
                registro.get("modalidad"),
                duracion_num,
                registro.get("periodo"),
                json.dumps(registro, ensure_ascii=False),
            )

            if cursor.rowcount > 0:
                insertados += 1

        conexion.commit()
        return insertados

    except Exception:
        if conexion:
            conexion.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


def consultar_registros(filtro=""):
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        if filtro:
            patron = f"%{filtro}%"
            cursor.execute(
                """
                SELECT TOP 100
                    id_api,
                    universidad,
                    ubicacion,
                    direccion,
                    programas,
                    modalidad,
                    duracion,
                    periodo
                FROM RegistrosAPI
                WHERE universidad LIKE ?
                   OR ubicacion LIKE ?
                   OR programas LIKE ?
                   OR modalidad LIKE ?
                ORDER BY id DESC
                """,
                patron,
                patron,
                patron,
                patron,
            )
        else:
            cursor.execute(
                """
                SELECT TOP 100
                    id_api,
                    universidad,
                    ubicacion,
                    direccion,
                    programas,
                    modalidad,
                    duracion,
                    periodo
                FROM RegistrosAPI
                ORDER BY id DESC
                """
            )

        columnas = [columna[0] for columna in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


def obtener_resumen():
    conexion = None
    cursor = None

    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_programas,
                COUNT(DISTINCT universidad) AS total_universidades,
                COUNT(DISTINCT ubicacion) AS total_ciudades,
                COALESCE(ROUND(AVG(CAST(duracion AS FLOAT)), 1), 0) AS promedio_duracion
            FROM RegistrosAPI
            """
        )
        fila = cursor.fetchone()

        return {
            "total_programas": fila[0],
            "total_universidades": fila[1],
            "total_ciudades": fila[2],
            "promedio_duracion": fila[3],
        }

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()