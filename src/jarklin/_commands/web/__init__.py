# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    import logging
    import secrets
    import os.path as p
    import flask
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
        logging.debug(f"serving under {baseurl!r}")
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
    session_permanent = config.getbool('web', 'session', 'permanent', fallback=True)
    if session_permanent:
        @app.before_request
        def make_session_permanent() -> None:
            flask.session.permanent = session_permanent
    session_lifetime = config.getint('web', 'session', 'lifetime', fallback=None)
    if session_lifetime:
        app.permanent_session_lifetime = session_lifetime  # flasks default is ~31d
    app.config['SESSION_REFRESH_EACH_REQUEST'] = \
        config.getbool('web', 'session', 'refresh_each_request', fallback=False)

    if config.gettype('web', 'optimize') is dict:
        app.config['JIT_OPTIMIZATION'] = {
            key: config.getbool('web', 'optimize', key)
            for key in config.get('web', 'optimize').keys()
        }
        logging.debug(f"jit-optimization: {app.config['JIT_OPTIMIZATION']}")
    elif config.getbool('web', 'optimize', fallback=False):
        import warnings
        warnings.warn("'web.optimize: {yes,no}' is soon deprecated. use 'web.optimize.*'", PendingDeprecationWarning)
        logging.warning("'web.optimize: {yes,no}' is soon deprecated. use 'web.optimize.*'")
        app.config['JIT_OPTIMIZATION'] = dict(image=True, video=True)
        logging.debug(f"jit-optimization: {app.config['JIT_OPTIMIZATION']}")

    if config.getbool('web', 'gzip', fallback=True):
        from flask_compress import Compress  # no need to load unless required
        logging.debug("enabling gzip compression")
        Compress(app)

    # pip install flask-kaccel for nginx
    # app.config['USE_X_SENDFILE'] = config.getboolean('web', 'x_sendfile', fallback=False)

    if config.has('web', 'proxy_fix'):
        proxy_fix = config.getinterface('web', 'proxy_fix')
        logging.debug(f"enabling proxy fix: {proxy_fix}")
        app.wsgi_app = ProxyFix(
            app=app,
            x_for=proxy_fix.getint('x_forwarded_for', fallback=1),
            x_proto=proxy_fix.getint('x_forwarded_proto', fallback=1),
            x_host=proxy_fix.getint('x_forwarded_host', fallback=0),
            x_port=proxy_fix.getint('x_forwarded_port', fallback=0),
            x_prefix=proxy_fix.getint('x_forwarded_prefix', fallback=0),
        )

    if config.getbool('web', 'debug', fallback=False):
        logging.debug("using flasks simple-serve debug server")
        app.run(
            debug=True,
            # host=config.getstr('web', 'host', fallback=None),
            # port=config.getint('web', 'port', fallback=None),
            **config.get('web', 'server', fallback={})
        )
    else:
        import waitress
        logging.debug("using waitress production server")
        waitress.serve(
            app=app,
            ident="jarklin",
            **config.get('web', 'server', fallback={})
        )
