from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    send_from_directory,
)
from flask_login import current_user

from extensions import db
from models import (
    Alumno,
    Clase,
    ConsultaMaterial,
    Inscripcion,
    Material,
    MaterialAlumno,
    RecursoMaterial,
    Unidad,
)
from routes.decorators import role_required


alumno_bp = Blueprint("alumno", __name__, url_prefix="/alumno")


def current_alumno():
    return Alumno.query.filter_by(
        usuario_id=current_user.id
    ).first_or_404()


def upload_folder():
    return current_app.config.get(
        "UPLOAD_FOLDER",
        "uploads/materiales"
    )


def alumno_tiene_inscripcion_activa(alumno_id, clase_id):
    return (
        Inscripcion.query
        .join(Clase)
        .filter(
            Inscripcion.clase_id == clase_id,
            Inscripcion.alumno_id == alumno_id,
            Inscripcion.estado == "ACTIVO",
            Clase.activa.is_(True)
        )
        .first()
        is not None
    )


def alumno_tiene_material_asignado(alumno_id, material_id):
    return (
        MaterialAlumno.query
        .filter_by(
            alumno_id=alumno_id,
            material_id=material_id
        )
        .first()
        is not None
    )


def alumno_can_access(material, alumno):
    if material is None:
        return False

    if material.estado != "PUBLICADO":
        return False

    if not material.activo:
        return False

    if not material.unidad or not material.unidad.clase:
        return False

    clase = material.unidad.clase

    if not clase.activa:
        return False

    if not alumno_tiene_inscripcion_activa(
        alumno_id=alumno.id,
        clase_id=clase.id
    ):
        return False

    if material.alcance == "TODA_LA_CLASE":
        return True

    if material.alcance == "ALUMNOS_SELECCIONADOS":
        return alumno_tiene_material_asignado(
            alumno_id=alumno.id,
            material_id=material.id
        )

    return False


def registrar_consulta(material, alumno):
    consulta = ConsultaMaterial.query.filter_by(
        material_id=material.id,
        alumno_id=alumno.id
    ).first()

    ahora = datetime.utcnow()

    if consulta:
        consulta.ultima_consulta = ahora
        consulta.numero_consultas += 1
    else:
        consulta = ConsultaMaterial(
            material_id=material.id,
            alumno_id=alumno.id,
            primera_consulta=ahora,
            ultima_consulta=ahora,
            numero_consultas=1
        )
        db.session.add(consulta)

    db.session.commit()


def obtener_inscripciones_activas(alumno):
    return (
        Inscripcion.query
        .join(Clase)
        .filter(
            Inscripcion.alumno_id == alumno.id,
            Inscripcion.estado == "ACTIVO",
            Clase.activa.is_(True)
        )
        .order_by(Clase.id.desc())
        .all()
    )


def obtener_materiales_disponibles(alumno, clase_id=None):
    query = (
        Material.query
        .join(Unidad, Unidad.id == Material.unidad_id)
        .join(Clase, Clase.id == Unidad.clase_id)
        .filter(
            Material.estado == "PUBLICADO",
            Material.activo.is_(True),
            Clase.activa.is_(True)
        )
    )

    if clase_id is not None:
        query = query.filter(Unidad.clase_id == clase_id)
    else:
        inscripciones = obtener_inscripciones_activas(alumno)
        clases_ids = [
            inscripcion.clase_id
            for inscripcion in inscripciones
        ]

        if not clases_ids:
            return []

        query = query.filter(Unidad.clase_id.in_(clases_ids))

    materiales_base = (
        query
        .order_by(Material.fecha_publicacion.desc(), Material.id.desc())
        .all()
    )

    return [
        material
        for material in materiales_base
        if alumno_can_access(material, alumno)
    ]


@alumno_bp.route("/dashboard")
@role_required("ALUMNO")
def dashboard():
    alumno = current_alumno()

    inscripciones = obtener_inscripciones_activas(alumno)

    materiales = obtener_materiales_disponibles(alumno)

    consultas = (
        ConsultaMaterial.query
        .filter(ConsultaMaterial.alumno_id == alumno.id)
        .all()
    )

    return render_template(
        "alumno/dashboard.html",
        alumno=alumno,
        inscripciones=inscripciones,
        materiales=materiales,
        consultas=consultas
    )


@alumno_bp.route("/clases")
@role_required("ALUMNO")
def clases():
    alumno = current_alumno()

    inscripciones = obtener_inscripciones_activas(alumno)

    return render_template(
        "alumno/clases.html",
        alumno=alumno,
        inscripciones=inscripciones
    )


@alumno_bp.route("/clases/<int:clase_id>")
@role_required("ALUMNO")
def detalle_clase(clase_id):
    alumno = current_alumno()

    inscripcion = (
        Inscripcion.query
        .join(Clase)
        .filter(
            Inscripcion.clase_id == clase_id,
            Inscripcion.alumno_id == alumno.id,
            Inscripcion.estado == "ACTIVO",
            Clase.activa.is_(True)
        )
        .first_or_404()
    )

    materiales = obtener_materiales_disponibles(
        alumno=alumno,
        clase_id=clase_id
    )

    return render_template(
        "alumno/detalle_clase.html",
        alumno=alumno,
        clase=inscripcion.clase,
        materiales=materiales
    )


@alumno_bp.route("/materiales/<int:material_id>")
@role_required("ALUMNO")
def material(material_id):
    alumno = current_alumno()

    material_obj = Material.query.get_or_404(material_id)

    if not alumno_can_access(material_obj, alumno):
        abort(403)

    registrar_consulta(
        material=material_obj,
        alumno=alumno
    )

    return render_template(
        "alumno/material.html",
        alumno=alumno,
        material=material_obj
    )


@alumno_bp.route("/recursos/<int:recurso_id>/ver")
@role_required("ALUMNO")
def ver_recurso(recurso_id):
    alumno = current_alumno()

    recurso = RecursoMaterial.query.get_or_404(recurso_id)

    if not alumno_can_access(recurso.material, alumno):
        abort(403)

    return send_from_directory(
        upload_folder(),
        recurso.ubicacion,
        as_attachment=False
    )


@alumno_bp.route("/recursos/<int:recurso_id>/descargar")
@role_required("ALUMNO")
def descargar_recurso(recurso_id):
    alumno = current_alumno()

    recurso = RecursoMaterial.query.get_or_404(recurso_id)

    if not alumno_can_access(recurso.material, alumno):
        abort(403)

    if not recurso.material.permite_descarga:
        abort(403)

    return send_from_directory(
        upload_folder(),
        recurso.ubicacion,
        as_attachment=True,
        download_name=recurso.nombre_original
    )