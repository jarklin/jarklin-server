# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    import flask
    import secrets
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.wrappers import Response
    from .._get_config import get_config
    from ...web import app

    config = get_config()

    baseurl = config.getstr('web', 'baseurl', fallback="/")
    if not baseurl.startswith("/"):
        raise ValueError("web.baseurl must start with /")
    if baseurl != "/":
        app.wsgi_app = DispatcherMiddleware(
            Response('Not Found', status=404),
            {baseurl: app.wsgi_app},
        )

    app.config['USERNAME'] = config.getstr('web', 'auth', 'username', fallback=None) or None
    app.config['PASSWORD'] = config.getstr('web', 'auth', 'password', fallback=None) or None

    app.secret_key = config.getstr('web', 'session', 'secret_key', fallback=secrets.token_hex(64))
    if baseurl != "/":
        app.config['SESSION_COOKIE_PATH'] = baseurl
    session_permanent = config.getboolean('web', 'session', 'permanent', fallback=True)
    if session_permanent:
        @app.before_request
        def make_session_permanent() -> None:
            flask.session.permanent = session_permanent
    session_lifetime = config.getint('web', 'session', 'lifetime', fallback=None)
    if session_lifetime:
        app.permanent_session_lifetime = session_lifetime  # flasks default is ~31d
    app.config['SESSION_REFRESH_EACH_REQUEST'] = \
        config.getboolean('web', 'session', 'refresh_each_request', fallback=False)

    if config.getbool('web', 'gzip', fallback=True):
        from flask_compress import Compress  # no need to load unless required
        Compress(app)

    app.run(
        host=config.getstr('web', 'host', fallback=None),
        port=config.getint('web', 'port', fallback=None),
        debug=config.getboolean('web', 'debug', fallback=False),
    )
