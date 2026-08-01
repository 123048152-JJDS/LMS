from flask import Blueprint, render_template


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def bienvenida():
    return render_template("Bienvenida.html")


def register_blueprints(app):
    from routes.admin import admin_bp
    from routes.alumno import alumno_bp
    from routes.auth import auth_bp
    from routes.profesor import profesor_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profesor_bp)
    app.register_blueprint(alumno_bp)
