from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import (
    Alumno,
    Clase,
    ClaseProfesor,
    ConsultaMaterial,
    Inscripcion,
    Material,
    MaterialAlumno,
    Profesor,
    RecursoMaterial,
    Usuario,
)
from routes.decorators import role_required


profesor_bp = Blueprint("profesor", __name__, url_prefix="/profesor")


USKOV_FIELDS = [
    "introduccion",
    "objetivo",
    "metodologia_trabajo",
    "detalles_material",
    "referencias_bibliograficas",
    "conclusion",
]


DEFAULT_ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "mp4",
    "webm",
    "mp3",
    "wav",
    "doc",
    "docx",
    "ppt",
    "pptx",
}


def current_profesor():
    return Profesor.query.filter_by(
        usuario_id=current_user.id
    ).first_or_404()


def profesor_tiene_clase(profesor_id, clase_id):
    return ClaseProfesor.query.filter_by(
        profesor_id=profesor_id,
        clase_id=clase_id
    ).first() is not None


def profesor_clase_or_404(clase_id):
    profesor = current_profesor()

    clase = (
        Clase.query
        .join(ClaseProfesor, ClaseProfesor.clase_id == Clase.id)
        .filter(
            Clase.id == clase_id,
            ClaseProfesor.profesor_id == profesor.id
        )
        .first_or_404()
    )

    return profesor, clase


def profesor_material_or_404(material_id):
    profesor = current_profesor()

    material = Material.query.filter_by(
        id=material_id,
        profesor_id=profesor.id
    ).first_or_404()

    return profesor, material


def allowed_file(filename):
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    allowed_extensions = current_app.config.get(
        "ALLOWED_EXTENSIONS",
        DEFAULT_ALLOWED_EXTENSIONS
    )

    return extension in allowed_extensions


def resource_type(filename, mimetype=None):
    extension = filename.rsplit(".", 1)[-1].lower()

    if extension == "pdf":
        return "PDF"

    if extension in {"png", "jpg", "jpeg", "gif", "webp"}:
        return "IMAGEN"

    if extension in {"mp4", "webm"}:
        return "VIDEO"

    if extension in {"mp3", "wav"}:
        return "AUDIO"

    if extension in {"ppt", "pptx"}:
        return "PRESENTACION"

    return "DOCUMENTO"


def form_bool(nombre):
    return request.form.get(nombre) in {"on", "true", "1", "si", "sí"}


def clases_del_profesor(profesor_id, solo_activas=False):
    consulta = (
        Clase.query
        .join(ClaseProfesor, ClaseProfesor.clase_id == Clase.id)
        .filter(ClaseProfesor.profesor_id == profesor_id)
    )

    if solo_activas:
        consulta = consulta.filter(Clase.activa.is_(True))

    return (
        consulta
        .order_by(Clase.id.desc())
        .all()
    )


def alumnos_activos_de_clase(clase_id):
    return (
        Alumno.query
        .join(Inscripcion, Inscripcion.alumno_id == Alumno.id)
        .join(Usuario, Usuario.id == Alumno.usuario_id)
        .filter(
            Inscripcion.clase_id == clase_id,
            Inscripcion.estado == "ACTIVO",
            Usuario.activo.is_(True)
        )
        .order_by(
            Usuario.apellido_paterno,
            Usuario.apellido_materno,
            Usuario.nombre
        )
        .all()
    )


@profesor_bp.route("/dashboard")
@role_required("PROFESOR")
def dashboard():
    profesor = current_profesor()

    clases = clases_del_profesor(
        profesor_id=profesor.id,
        solo_activas=True
    )

    materiales = Material.query.filter_by(
        profesor_id=profesor.id
    ).count()

    publicados = Material.query.filter_by(
        profesor_id=profesor.id,
        estado="PUBLICADO"
    ).count()

    return render_template(
        "profesor/dashboard.html",
        clases=clases,
        materiales=materiales,
        publicados=publicados
    )


@profesor_bp.route("/clases")
@role_required("PROFESOR")
def clases():
    profesor = current_profesor()

    clases_lista = clases_del_profesor(
        profesor_id=profesor.id,
        solo_activas=False
    )

    return render_template(
        "profesor/clases.html",
        clases=clases_lista
    )


@profesor_bp.route("/clases/<int:clase_id>")
@role_required("PROFESOR")
def detalle_clase(clase_id):
    profesor, clase = profesor_clase_or_404(clase_id)

    inscripciones = (
        Inscripcion.query
        .join(Alumno, Alumno.id == Inscripcion.alumno_id)
        .join(Usuario, Usuario.id == Alumno.usuario_id)
        .filter(
            Inscripcion.clase_id == clase.id,
            Inscripcion.estado == "ACTIVO"
        )
        .order_by(
            Usuario.apellido_paterno,
            Usuario.apellido_materno,
            Usuario.nombre
        )
        .all()
    )

    materiales = (
        Material.query
        .filter_by(
            clase_id=clase.id,
            profesor_id=profesor.id
        )
        .order_by(Material.actualizado_en.desc())
        .all()
    )

    return render_template(
        "profesor/detalle_clase.html",
        clase=clase,
        inscripciones=inscripciones,
        materiales=materiales
    )


@profesor_bp.route("/materiales")
@role_required("PROFESOR")
def materiales():
    profesor = current_profesor()

    lista = (
        Material.query
        .filter_by(profesor_id=profesor.id)
        .order_by(Material.actualizado_en.desc())
        .all()
    )

    return render_template(
        "profesor/materiales.html",
        materiales=lista
    )


@profesor_bp.route("/materiales/crear", methods=["GET", "POST"])
@role_required("PROFESOR")
def crear_material():
    profesor = current_profesor()

    clases = clases_del_profesor(
        profesor_id=profesor.id,
        solo_activas=True
    )

    material = Material(
        profesor_id=profesor.id,
        permite_descarga=False,
        alcance="TODA_LA_CLASE",
        estado="BORRADOR",
        activo=True
    )

    clase_id = request.args.get("clase_id", type=int)

    if clase_id and profesor_tiene_clase(profesor.id, clase_id):
        material.clase_id = clase_id

    return guardar_material(
        material=material,
        clases=clases,
        nuevo=True
    )


@profesor_bp.route("/materiales/<int:material_id>/editar", methods=["GET", "POST"])
@role_required("PROFESOR")
def editar_material(material_id):
    profesor, material = profesor_material_or_404(material_id)

    clases = clases_del_profesor(
        profesor_id=profesor.id,
        solo_activas=True
    )

    return guardar_material(
        material=material,
        clases=clases,
        nuevo=False
    )


def guardar_material(material, clases, nuevo):
    clase_id = (
        request.form.get("clase_id", type=int)
        if request.method == "POST"
        else material.clase_id
    )

    alumnos = []

    if clase_id:
        profesor_clase_or_404(clase_id)
        alumnos = alumnos_activos_de_clase(clase_id)

    if request.method == "POST":
        errores = []

        clases_ids = {clase.id for clase in clases}

        if not clase_id or clase_id not in clases_ids:
            errores.append("La clase seleccionada no pertenece al profesor.")

        titulo = request.form.get("titulo", "").strip()

        if not titulo:
            errores.append("El título del material es obligatorio.")

        for campo in USKOV_FIELDS:
            if not request.form.get(campo, "").strip():
                errores.append("Todas las secciones de la metodología Uskov son obligatorias.")
                break

        alcance = request.form.get("alcance", "TODA_LA_CLASE")

        if alcance not in {"TODA_LA_CLASE", "ALUMNOS_SELECCIONADOS"}:
            errores.append("El alcance seleccionado no es válido.")

        alumnos_seleccionados = {
            int(item)
            for item in request.form.getlist("alumnos")
            if item.isdigit()
        }

        alumnos_permitidos = {
            alumno.id
            for alumno in alumnos
        }

        if alcance == "ALUMNOS_SELECCIONADOS":
            if not alumnos_seleccionados:
                errores.append("Selecciona al menos un alumno.")

            if not alumnos_seleccionados.issubset(alumnos_permitidos):
                errores.append("Solo puedes seleccionar alumnos inscritos en la clase.")

        uploaded_files = [
            archivo
            for archivo in request.files.getlist("recursos")
            if archivo and archivo.filename
        ]

        portada = request.files.get("portada")

        archivos_a_validar = uploaded_files.copy()

        if portada and portada.filename:
            archivos_a_validar.append(portada)

        for archivo in archivos_a_validar:
            if not allowed_file(archivo.filename):
                errores.append("Hay archivos con extensión no permitida.")
                break

        if errores:
            for error in errores:
                flash(error, "danger")

            return render_template(
                "profesor/creacion.html" if nuevo else "profesor/editar_material.html",
                material=material,
                clases=clases,
                alumnos=alumnos
            )

        material.clase_id = clase_id
        material.titulo = titulo
        material.descripcion_corta = request.form.get("descripcion_corta", "").strip() or None

        material.introduccion = request.form["introduccion"].strip()
        material.objetivo = request.form["objetivo"].strip()
        material.metodologia_trabajo = request.form["metodologia_trabajo"].strip()
        material.detalles_material = request.form["detalles_material"].strip()
        material.referencias_bibliograficas = request.form["referencias_bibliograficas"].strip()
        material.conclusion = request.form["conclusion"].strip()

        material.alcance = alcance
        material.permite_descarga = form_bool("permite_descarga")

        if request.form.get("accion") == "publicar":
            material.estado = "PUBLICADO"
            material.fecha_publicacion = material.fecha_publicacion or datetime.utcnow()
        else:
            material.estado = "BORRADOR"

        material.activo = True

        db.session.add(material)
        db.session.flush()

        actualizar_alumnos_asignados(
            material=material,
            alcance=alcance,
            alumnos_seleccionados=alumnos_seleccionados
        )

        save_uploads(
            material=material,
            portada=portada,
            uploaded_files=uploaded_files
        )

        db.session.commit()

        flash("Material guardado correctamente.", "success")

        return redirect(
            url_for(
                "profesor.detalle_material",
                material_id=material.id
            )
        )

    return render_template(
        "profesor/creacion.html" if nuevo else "profesor/editar_material.html",
        material=material,
        clases=clases,
        alumnos=alumnos
    )


def actualizar_alumnos_asignados(material, alcance, alumnos_seleccionados):
    MaterialAlumno.query.filter_by(
        material_id=material.id
    ).delete(synchronize_session=False)

    if alcance != "ALUMNOS_SELECCIONADOS":
        return

    for alumno_id in alumnos_seleccionados:
        db.session.add(
            MaterialAlumno(
                material_id=material.id,
                alumno_id=alumno_id
            )
        )


def save_uploads(material, portada, uploaded_files):
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads/materiales")

    target = Path(upload_folder) / str(material.id)
    target.mkdir(parents=True, exist_ok=True)

    if portada and portada.filename and allowed_file(portada.filename):
        nombre_seguro = secure_filename(portada.filename)
        destino = target / nombre_seguro

        portada.save(destino)

        material.portada_ruta = f"{material.id}/{nombre_seguro}"

    start = len(material.recursos)

    for index, archivo in enumerate(uploaded_files, start=start + 1):
        nombre_seguro = secure_filename(archivo.filename)
        destino = target / nombre_seguro

        archivo.seek(0, 2)
        tamanio = archivo.tell()
        archivo.seek(0)

        archivo.save(destino)

        db.session.add(
            RecursoMaterial(
                material_id=material.id,
                tipo=resource_type(nombre_seguro, archivo.mimetype),
                nombre_original=archivo.filename,
                ubicacion=f"{material.id}/{nombre_seguro}",
                mime_type=archivo.mimetype,
                tamanio_bytes=tamanio,
                descripcion=request.form.get("descripcion_recurso", "").strip() or None,
                texto_alternativo=request.form.get("texto_alternativo", "").strip() or None,
                orden=index
            )
        )


@profesor_bp.route("/materiales/<int:material_id>")
@role_required("PROFESOR")
def detalle_material(material_id):
    _, material = profesor_material_or_404(material_id)

    return render_template(
        "profesor/detalle_material.html",
        material=material
    )


@profesor_bp.route("/materiales/<int:material_id>/publicar", methods=["POST"])
@role_required("PROFESOR")
def publicar_material(material_id):
    _, material = profesor_material_or_404(material_id)

    material.estado = "PUBLICADO"
    material.fecha_publicacion = material.fecha_publicacion or datetime.utcnow()

    db.session.commit()

    flash("Material publicado correctamente.", "success")

    return redirect(
        url_for(
            "profesor.detalle_material",
            material_id=material.id
        )
    )


@profesor_bp.route("/materiales/<int:material_id>/archivar", methods=["POST"])
@role_required("PROFESOR")
def archivar_material(material_id):
    _, material = profesor_material_or_404(material_id)

    material.estado = "ARCHIVADO"

    db.session.commit()

    flash("Material archivado correctamente.", "success")

    return redirect(
        url_for("profesor.materiales")
    )


@profesor_bp.route("/uploads/<path:filename>")
@role_required("PROFESOR")
def archivo(filename):
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads/materiales")

    return send_from_directory(
        upload_folder,
        filename
    )