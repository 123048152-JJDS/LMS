import click

from flask import Flask, flash, redirect, render_template, url_for
from werkzeug.security import generate_password_hash

from config import Config
from extensions import csrf, db, login_manager, migrate
from models import Rol, Usuario
from routes import register_blueprints
from db_bootstrap import inicializar_base_datos


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_message = "Inicia sesión para continuar."

    inicializar_base_datos(app, db)

    register_login_manager()
    register_routes(app)
    register_blueprints(app)
    register_cli(app)
    register_error_handlers(app)

    return app


def register_login_manager():
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(Usuario, int(user_id))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def unauthorized():
        flash("Inicia sesión para continuar.", "warning")
        return redirect(url_for("bienvenida"))


def register_routes(app):
    @app.route("/")
    def bienvenida():
        return render_template("Bienvenida.html")


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500


def register_cli(app):
    @app.cli.command("sembrar-catalogos")
    def seed_catalogs():
        roles = [
            (
                "ADMINISTRADOR",
                "Gestiona usuarios, materias, clases y asignaciones"
            ),
            (
                "PROFESOR",
                "Crea y publica materiales educativos"
            ),
            (
                "ALUMNO",
                "Consulta los materiales educativos asignados"
            ),
        ]

        for nombre, descripcion in roles:
            rol = Rol.query.filter_by(nombre=nombre).first()

            if rol is None:
                rol = Rol(
                    nombre=nombre,
                    descripcion=descripcion
                )
                db.session.add(rol)
            else:
                rol.descripcion = descripcion

        db.session.commit()

        click.echo("Catálogos sembrados correctamente.")

    @app.cli.command("crear-admin")
    def create_admin():
        nombre = click.prompt("Nombre")
        apellido_paterno = click.prompt("Apellido paterno")
        apellido_materno = click.prompt(
            "Apellido materno",
            default="",
            show_default=False
        )
        correo = click.prompt("Correo").strip().lower()
        password = click.prompt(
            "Contraseña",
            hide_input=True,
            confirmation_prompt=True
        )

        rol = Rol.query.filter_by(nombre="ADMINISTRADOR").first()

        if rol is None:
            rol = Rol(
                nombre="ADMINISTRADOR",
                descripcion="Gestiona usuarios, materias, clases y asignaciones"
            )
            db.session.add(rol)
            db.session.flush()

        if Usuario.query.filter_by(correo=correo).first():
            raise click.ClickException(
                "Ya existe un usuario con ese correo."
            )

        usuario = Usuario(
            rol_id=rol.id,
            nombre=nombre.strip(),
            apellido_paterno=apellido_paterno.strip(),
            apellido_materno=apellido_materno.strip() or None,
            correo=correo,
            password_hash=generate_password_hash(password),
            activo=True,
        )

        db.session.add(usuario)
        db.session.commit()

        click.echo("Administrador creado correctamente.")


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)