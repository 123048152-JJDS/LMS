from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from extensions import db
from models import Usuario


auth_bp = Blueprint("auth", __name__)


ROUTE_ROLES = {
    "alumno": (
        "ALUMNO",
        "Inicio de sesión para alumnos",
        "alumno.dashboard"
    ),
    "profesor": (
        "PROFESOR",
        "Inicio de sesión para profesores",
        "profesor.dashboard"
    ),
    "administrador": (
        "ADMINISTRADOR",
        "Acceso administrativo",
        "admin.dashboard"
    ),
}


def usuario_tiene_rol(usuario, rol_esperado):
    return (
        usuario
        and usuario.rol
        and usuario.rol.nombre == rol_esperado
    )


def dashboard_por_rol(usuario):
    if not usuario or not usuario.rol:
        return "bienvenida"

    rol = usuario.rol.nombre

    if rol == "ADMINISTRADOR":
        return "admin.dashboard"

    if rol == "PROFESOR":
        return "profesor.dashboard"

    if rol == "ALUMNO":
        return "alumno.dashboard"

    return "bienvenida"


@auth_bp.route("/login/<tipo_usuario>", methods=["GET", "POST"])
def login_tipo(tipo_usuario):
    config = ROUTE_ROLES.get(tipo_usuario)

    if config is None:
        return render_template("errors/404.html"), 404

    rol_esperado, titulo, destino = config

    if current_user.is_authenticated:
        if usuario_tiene_rol(current_user, rol_esperado):
            return redirect(url_for(destino))

        return redirect(url_for(dashboard_por_rol(current_user)))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(correo=correo).first()

        credenciales_validas = (
            usuario
            and usuario.activo
            and usuario_tiene_rol(usuario, rol_esperado)
            and check_password_hash(usuario.password_hash, password)
        )

        if credenciales_validas:
            usuario.ultimo_acceso = datetime.utcnow()
            db.session.commit()

            login_user(usuario)

            flash("Inicio de sesión correcto.", "success")
            return redirect(url_for(destino))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template(
        "auth/login.html",
        tipo_usuario=tipo_usuario,
        titulo=titulo
    )


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("bienvenida"))