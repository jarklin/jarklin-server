# -*- coding=utf-8 -*-
r"""

"""
import os
import os.path as p
from http import HTTPStatus
import flask
from werkzeug.exceptions import Unauthorized as HTTPUnauthorized, BadRequest as HTTPBadRequest, NotFound as HTTPNotFound
from .utility import requires_authenticated, validate_user


WEB_UI = p.join(p.dirname(__file__), 'web-ui')
app = flask.Flask(__name__, static_url_path="/", static_folder=WEB_UI, template_folder=None)


@app.get("/files/<path:resource>")
@requires_authenticated
def files(resource: str, download: bool = False):
    fp = p.join(os.getcwd(), resource)
    if fp in app.config['EXCLUDE']:
        raise HTTPNotFound()
    return flask.send_from_directory(os.getcwd(), resource, as_attachment=download)


@app.get("/auth/username")
def get_username():
    try:
        return flask.session["username"], HTTPStatus.OK
    except KeyError:
        return "", HTTPStatus.NO_CONTENT


@app.post("/auth/login")
def login():
    userpass = app.config.get('USERPASS')
    if not userpass:
        return "", HTTPStatus.NO_CONTENT

    username, password = flask.request.form.get("username"), flask.request.form.get("password")
    if not username or not password:
        raise HTTPBadRequest("username or password missing in authorization")

    if not validate_user(username=username, password=password):
        raise HTTPUnauthorized("bad credentials provided")
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
