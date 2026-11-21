import os
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv


load_dotenv()


class APIClient:
    BASE_URL = "https://www.datos.gov.co/resource"

    def __init__(self) -> None:
        recurso = os.getenv("API_RESOURCE_ID")

        if not recurso:
            raise ValueError(
                "La variable de entorno 'API_RESOURCE_ID' no está definida."
            )

        self.url = f"{self.BASE_URL}/{recurso}.json"

        self.session = requests.Session()

        reintentos = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )

        adaptador = HTTPAdapter(max_retries=reintentos)
        self.session.mount("https://", adaptador)

    def obtener_registros(
        self,
        limite: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if not isinstance(limite, int) or limite <= 0:
            raise ValueError("El parámetro 'limite' debe ser un entero positivo.")

        if not isinstance(offset, int) or offset < 0:
            raise ValueError("El parámetro 'offset' debe ser un entero no negativo.")

        parametros = {
            "$limit": limite,
            "$offset": offset,
        }

        headers = {
            "Accept": "application/json",
        }

        token = os.getenv("API_APP_TOKEN")
        if token:
            headers["X-App-Token"] = token

        try:
            respuesta = self.session.get(
                self.url,
                params=parametros,
                headers=headers,
                timeout=(10, 30),
            )

            respuesta.raise_for_status()

            datos = respuesta.json()

        except requests.exceptions.Timeout as error:
            raise RuntimeError("La solicitud a la API tardó demasiado.") from error

        except requests.exceptions.RequestException as error:
            raise RuntimeError(f"Error al consultar la API: {error}") from error

        except ValueError as error:
            raise RuntimeError("La API no devolvió un JSON válido.") from error

        if not isinstance(datos, list):
            raise RuntimeError("La API devolvió un formato JSON inesperado.")

        return datos     