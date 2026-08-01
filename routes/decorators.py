from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)

            if not current_user.activo:
                abort(403)

            if not current_user.rol:
                abort(403)

            if current_user.rol.nombre not in roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator