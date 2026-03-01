from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User, Role


def require_roles(*roles):
    def inner(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            verify_jwt_in_request()
            uid = get_jwt_identity()
            user = User.query.get(int(uid))
            if not user or user.role not in roles:
                return jsonify({'message': 'Forbidden'}), 403
            return fn(*args, **kwargs)

        return wrapped

    return inner
