import os
import secrets

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from dotenv import load_dotenv

from api.api_client import APIClient
from models.datos_model import consultar_registros, guardar_registros, obtener_resumen

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "no").lower() == "yes",
)


def obtener_token_csrf() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@app.route("/", methods=["GET"])
def inicio():
    filtro = request.args.get("q", "").strip()
    try:
        registros = consultar_registros(filtro)
        resumen = obtener_resumen()
    except Exception:
        app.logger.exception("No se pudo consultar la base de datos")
        registros = []
        resumen = {
            "total_programas": 0,
            "total_universidades": 0,
            "total_ciudades": 0,
            "promedio_duracion": 0,
        }
        flash("Base de datos no disponible: se muestran datos vacíos.", "error")
    return render_template(
        "index.html",
        registros=registros,
        resumen=resumen,
        filtro=filtro,
        csrf_token=obtener_token_csrf(),
    )


@app.route("/sincronizar", methods=["POST"])
def sincronizar():
    token = request.form.get("csrf_token", "")
    if not token or token != session.get("csrf_token"):
        abort(403)

    try:
        registros = APIClient().obtener_registros(limite=1000)
        insertados = guardar_registros(registros)
        flash(f"Sincronización completada: {insertados} registros guardados.", "exito")
    except Exception:
        app.logger.exception("Error al sincronizar los datos de la API")
        flash("No se pudo completar la sincronización. Intente de nuevo.", "error")

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
