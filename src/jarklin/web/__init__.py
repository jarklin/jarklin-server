# -*- coding=utf-8 -*-
r"""

"""
import io
import os
import os.path as p
import mimetypes
from http import HTTPStatus
import flask
from PIL import Image
from werkzeug.exceptions import Unauthorized as HTTPUnauthorized, BadRequest as HTTPBadRequest, NotFound as HTTPNotFound
from .utility import requires_authenticated, validate_user, to_bool


WEB_UI = p.join(p.dirname(__file__), 'web-ui')
app = flask.Flask(__name__, static_url_path="/", static_folder=WEB_UI, template_folder=None)


@app.get("/files/<path:resource>")
@requires_authenticated
def files(resource: str):
    optimize = flask.request.args.get("optimize", default=False, type=to_bool)
    download = flask.request.args.get("download", default=False, type=to_bool)

    root = p.abspath(os.getcwd())
    fp = p.join(root, resource)
    if fp in app.config['EXCLUDE']:
        raise HTTPNotFound()
    if p.commonpath([root, fp]) != root:
        raise HTTPNotFound(f"{fp!s}")

    file = fp

    if optimize and flask.current_app.config['JIT_OPTIMIZATION']:
        mimetype, _ = mimetypes.guess_type(fp)
        if mimetype and mimetype.startswith("image/"):
            with Image.open(fp) as image:
                # we don't support animated images
                if not getattr(image, 'is_animated', False):
                    # support for giant image commonly found in comics or mangas
                    boundary = (2000, 2000)
                    if image.width > 2 * image.height or image.height > image.width * 2:
                        boundary = (4000, 4000)

                    image.thumbnail(boundary, resample=Image.Resampling.BICUBIC)  # resize but keep aspect

                    buffer = io.BytesIO()
                    image.save(buffer, format='WEBP')  # WebP should be better than JPEG or PNG
                    buffer.seek(0)
                    file = buffer

                # ensure image gets closed
                image.close()
                del image

            if isinstance(file, io.BytesIO):
                return flask.send_file(file, "image/webp", as_attachment=download,
                                       download_name="optimized.webp", conditional=False, etag=False)

    return flask.send_file(file, as_attachment=download)


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
