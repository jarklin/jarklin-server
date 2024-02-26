# -*- coding=utf-8 -*-
r"""

"""
import os
import os.path as p
import logging
from http import HTTPStatus
import flask
from werkzeug.exceptions import Unauthorized as HTTPUnauthorized, BadRequest as HTTPBadRequest, NotFound as HTTPNotFound
from .utility import requires_authenticated, validate_user, to_bool
from . import optimization


WEB_UI = p.join(p.dirname(__file__), 'web-ui')
app = flask.Flask(__name__, static_url_path="/", static_folder=WEB_UI, template_folder=None)


@app.get("/files/<path:resource>")
@requires_authenticated
def files(resource: str):
    attempt_optimization = flask.request.args.get("optimize", default=False, type=to_bool)
    as_download = flask.request.args.get("download", default=False, type=to_bool)

    root = p.abspath(os.getcwd())
    fp = p.abspath(p.join(root, resource))
    if fp in app.config['EXCLUDE']:
        raise HTTPNotFound()
    if p.commonpath([root, fp]) != root:
        raise HTTPNotFound(f"{fp!s}")

    if attempt_optimization and flask.current_app.config['JIT_OPTIMIZATION']:
        try:
            response = optimization.optimize_file(fp)
            if response is not None:
                return response
        except NotImplementedError:  # this is fine
            pass
        except Exception as error:  # no-fail
            logging.error(f"optimization for {resource!r} failed", exc_info=error)

    return flask.send_file(fp, as_attachment=as_download)


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
