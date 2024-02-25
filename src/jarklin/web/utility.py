# -*- coding=utf-8 -*-
r"""

"""
from hmac import compare_digest
import flask
from werkzeug.exceptions import Unauthorized as HTTPUnauthorized


def validate_user(username: str, password: str) -> True:
    userpass = flask.current_app.config.get('USERPASS')
    return userpass and username in userpass and compare_digest(password, userpass[username])


def requires_authenticated(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if flask.current_app.config.get("USERPASS"):
            authenticated = False

            auth = flask.request.authorization
            if (auth is not None
                    and auth.type == "basic"
                    and validate_user(username=auth.username, password=auth.password)):
                authenticated = True

            if 'username' in flask.session:
                authenticated = True

            if not authenticated:
                raise HTTPUnauthorized("currently not logged in")
        return fn(*args, **kwargs)

    return wrapper


def to_bool(value: str) -> bool:
    # important: this evaluates empty strings to true (/resource?download)
    return value.lower() in {"true", "yes", "1", ""}
