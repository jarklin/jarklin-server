# -*- coding=utf-8 -*-
r"""

"""
import os
import os.path as p
from http import HTTPStatus
from hmac import compare_digest
import flask
from werkzeug.exceptions import Unauthorized, BadRequest


WEB_UI = p.join(p.dirname(__file__), 'web-ui')
app = flask.Flask(__name__, static_url_path="/", static_folder=WEB_UI, template_folder=None)


def is_authenticated(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if (app.config.get("USERNAME") is not None and app.config.get("PASSWORD") is not None
                and 'username' not in flask.session):
            raise Unauthorized("currently not logged in")
        return fn(*args, **kwargs)

    return wrapper


@app.get("/files/<path:resource>")
@is_authenticated
def files(resource: str, download: bool = False):
    return flask.send_from_directory(os.getcwd(), resource, as_attachment=download)


@app.get("/auth/username")
def get_username():
    try:
        return flask.session["username"], HTTPStatus.OK
    except KeyError:
        return "", HTTPStatus.NO_CONTENT


@app.post("/auth/login")
def login():
    config_username, config_password = app.config.get("USERNAME"), app.config.get("PASSWORD")
    if config_username is None or config_password is None:
        return "", HTTPStatus.NO_CONTENT

    username, password = flask.request.form.get("username"), flask.request.form.get("password")
    if not username or not password:
        raise BadRequest("username or password missing in authorization")
    if not (compare_digest(username, config_username) and compare_digest(password, config_password)):
        raise Unauthorized("bad credentials provided")
    flask.session['username'] = username
    return "", HTTPStatus.NO_CONTENT


@app.post("/auth/logout")
def logout():
    if 'username' in flask.session:
        flask.session.pop('username')
    return "", HTTPStatus.NO_CONTENT


@app.get("/")
def index():
    return app.send_static_file("index.html")
