# -*- coding=utf-8 -*-
r"""

"""
import os
import os.path as p
import logging
from http import HTTPStatus
import flask
from werkzeug.exceptions import Unauthorized as HTTPUnauthorized, BadRequest as HTTPBadRequest, NotFound as HTTPNotFound
from loggext.decorators import add_logging
from .utility import requires_authenticated, validate_user, to_bool
from . import optimization


logger = logging.getLogger(__name__)
WEB_UI = p.join(p.dirname(__file__), 'web-ui')
app = flask.Flask(__name__, static_url_path="/", static_folder=WEB_UI, template_folder=None)


@app.get("/")
@add_logging()
def index():
    return app.send_static_file("index.html")


@app.get("/files/<path:resource>")
@requires_authenticated
@add_logging()
def files(resource: str):
    attempt_optimization = flask.request.args.get("optimize", default=False, type=to_bool)
    as_download = flask.request.args.get("download", default=False, type=to_bool)

    root = p.abspath(os.getcwd())
    fp = p.abspath(p.join(root, resource))
    if fp in app.config['EXCLUDE']:
        logger.warning(f"attempt to access excluded file ({resource})")
        raise HTTPNotFound(resource)
    if p.commonpath([root, fp]) != root:
        logger.warning(f"attempt to access files outside root directory ({resource})")
        raise HTTPNotFound(resource)

    if attempt_optimization and flask.current_app.config['JIT_OPTIMIZATION']:
        try:
            response = optimization.optimize_file(fp)
            if response is not None:
                return response
        except NotImplementedError:  # this is fine
            pass
        except Exception as error:  # no-fail
            logger.error(f"optimization for {resource!r} failed", exc_info=error)

    try:
        return flask.send_file(fp, as_attachment=as_download)
    except FileNotFoundError:
        raise HTTPNotFound(resource)


@app.get("/api/config")
@add_logging()
def get_config():
    return dict(
        requires_auth=bool(flask.current_app.config.get('USERPASS')),
        allows_optimization=True in flask.current_app.config.get('JIT_OPTIMIZATION', {}).values(),
    )


@app.get("/api/video-resolutions")
@add_logging()
def get_video_resolutions():
    return {
        name: info._asdict()
        for name, info in optimization.VIDEO_BITRATE_MAP.items()
    }


@app.get("/auth/username")
@add_logging()
def get_username():
    try:
        return flask.session["username"], HTTPStatus.OK
    except KeyError:
        return "", HTTPStatus.NO_CONTENT


@app.post("/auth/login")
@add_logging()
def login():
    userpass = app.config.get('USERPASS')
    if not userpass:
        return "", HTTPStatus.NO_CONTENT

    username, password = flask.request.form.get("username"), flask.request.form.get("password")
    if not username or not password:
        raise HTTPBadRequest("username or password missing in authorization")

    if not validate_user(username=username, password=password):
        logger.warning(f"failed login attempt for username {username!r}")
        raise HTTPUnauthorized("bad credentials provided")
    logger.debug(f"New login from {username!r}")
    flask.session['username'] = username
    return "", HTTPStatus.NO_CONTENT


@app.post("/auth/logout")
@add_logging()
def logout():
    if 'username' in flask.session:
        flask.session.pop('username')
    return "", HTTPStatus.NO_CONTENT
