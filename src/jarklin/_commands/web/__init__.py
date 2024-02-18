# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    import os.path as p
    import flask
    import secrets
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.middleware.proxy_fix import ProxyFix
    from .._get_config import get_config
    from ...web import app

    config, config_fp = get_config(return_fp=True)

    app.config['EXCLUDE'] = [config_fp]

    baseurl = config.getstr('web', 'baseurl', fallback="/")
    if not baseurl.startswith("/"):
        raise ValueError("web.baseurl must start with /")
    if baseurl != "/":
        from werkzeug.wrappers import Response
        app.wsgi_app = DispatcherMiddleware(
            Response('Not Found', status=404),
            {baseurl: app.wsgi_app},
        )

    app.config['USERPASS'] = {}
    simple_username = config.getstr('web', 'auth', 'username', fallback=None) or None
    simple_password = config.getstr('web', 'auth', 'password', fallback=None) or None
    if simple_username and simple_password:
        app.config['USERPASS'][simple_username] = simple_password
    if config.has('web', 'auth', 'userpass'):
        from ...common.userpass import parse_userpass
        userpass_fp = p.abspath(config.getstr('web', 'auth', 'userpass'))
        app.config['EXCLUDE'].append(userpass_fp)
        userpass = parse_userpass(userpass_fp)
        app.config['USERPASS'].update(userpass)

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

    if config.getboolean('web', 'gzip', fallback=True):
        from flask_compress import Compress  # no need to load unless required
        Compress(app)

    # pip install flask-kaccel for nginx
    # app.config['USE_X_SENDFILE'] = config.getboolean('web', 'x_sendfile', fallback=False)

    if config.has('web', 'proxy_fix'):
        proxy_fix = config.getinterface('web', 'proxy_fix')
        app.wsgi_app = ProxyFix(
            app=app,
            x_for=proxy_fix.getint('x_forwarded_for', fallback=1),
            x_proto=proxy_fix.getint('x_forwarded_proto', fallback=1),
            x_host=proxy_fix.getint('x_forwarded_host', fallback=0),
            x_port=proxy_fix.getint('x_forwarded_port', fallback=0),
            x_prefix=proxy_fix.getint('x_forwarded_prefix', fallback=0),
        )

    if config.getboolean('web', 'debug', fallback=False):
        app.run(
            debug=True,
            # host=config.getstr('web', 'host', fallback=None),
            # port=config.getint('web', 'port', fallback=None),
            **config.get('web', 'server', fallback={})
        )
    else:
        import waitress
        waitress.serve(
            app=app,
            ident="jarklin",
            **config.get('web', 'server', fallback={})
        )
