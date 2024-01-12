# -*- coding=utf-8 -*-
r"""

"""
import os
import secrets
import os.path as p
from http import HTTPStatus
from hmac import compare_digest
import flask
from werkzeug.exceptions import Forbidden, BadRequest


WEB_UI = p.join(p.dirname(__file__), 'web-ui')
application = flask.Flask(__name__, static_url_path="/", static_folder=WEB_UI, template_folder=None)
application.secret_key = "secret" if __debug__ else secrets.token_hex(64)


def is_authenticated(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'username' not in flask.session:
            raise Forbidden("currently not logged in")
        return fn(*args, **kwargs)

    return wrapper


@application.get("/files/<path:resource>")
@is_authenticated
def files(resource: str, download: bool = False):
    return flask.send_from_directory(os.getcwd(), resource, as_attachment=download)


@application.post("/login")
def login():
    username, password = flask.request.form.get("username"), flask.request.form.get("password")
    if not username or not password:
        raise BadRequest("username or password missing in authorization")
    if not (compare_digest(username, "admin") and compare_digest(password, "admin")):
        raise Forbidden("bad credentials provided")
    flask.session['username'] = username
    return "", HTTPStatus.NO_CONTENT


@application.post("/logout")
def logout():
    if 'username' in flask.session:
        flask.session.pop('username')
    return "", HTTPStatus.NO_CONTENT


@application.get("/")
def index():
    return application.send_static_file("index.html")


# @application.get("/")
# @application.get("/<path:resource>")
# def index(resource: str = "./"):
#     if resource.endswith("/"):
#         resource += "index.html"
#     try:
#         return flask.send_from_directory(WEB_UI, resource)
#     except NotFound:
#         pass
#     return flask.send_from_directory(WEB_UI, "404.html"), HTTPStatus.NOT_FOUND
