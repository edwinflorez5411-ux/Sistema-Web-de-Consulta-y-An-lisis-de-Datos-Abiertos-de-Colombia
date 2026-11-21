import os
import sys

from dotenv import load_dotenv

from api.api_client import APIClient


def verificar_entorno() -> None:
    load_dotenv()
    recurso = os.getenv("API_RESOURCE_ID")

    if not recurso:
        raise RuntimeError("Falta 'API_RESOURCE_ID' en el archivo .env.")

    token = os.getenv("API_APP_TOKEN")
    print(f"[OK] .env cargado -> API_RESOURCE_ID={recurso}")
    print(f"[INFO] API_APP_TOKEN={'definido' if token else 'no definido (opcional)'}")


def verificar_cliente() -> APIClient:
    cliente = APIClient()
    print(f"[OK] URL construida -> {cliente.url}")
    return cliente


def verificar_json(cliente: APIClient) -> list[dict[str, object]]:
    registros = cliente.obtener_registros(limite=3)

    if not isinstance(registros, list):
        raise RuntimeError("La API no devolvió una lista JSON.")

    if not registros:
        raise RuntimeError("La API devolvió una lista de registros vacía.")

    if not all(isinstance(registro, dict) for registro in registros):
        raise RuntimeError("Los registros del JSON no son objetos.")

    print(f"[OK] JSON recibido -> {len(registros)} registros")
    print(f"[OK] Campos -> {', '.join(registros[0].keys())}")
    return registros


def verificar_paginacion(cliente: APIClient) -> None:
    primera = cliente.obtener_registros(limite=1, offset=0)
    segunda = cliente.obtener_registros(limite=1, offset=1)

    if not primera or not segunda:
        raise RuntimeError("La paginación no devolvió registros.")

    if primera == segunda:
        raise RuntimeError("El parámetro 'offset' no cambió los resultados.")

    print("[OK] Paginación verificada (offset).")


def main() -> int:
    try:
        verificar_entorno()
        cliente = verificar_cliente()
        registros = verificar_json(cliente)
        verificar_paginacion(cliente)

        print("[OK] Ejemplo de registro:")
        for clave, valor in registros[0].items():
            print(f"     {clave}: {valor}")

        print("[OK] Conexión y acceso a JSON verificados correctamente.")
        return 0

    except Exception as error:
        print(f"[ERROR] {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
