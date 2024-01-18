# -*- coding=utf-8 -*-
r"""

"""


def run() -> None:
    import secrets
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.wrappers import Response
    from .._get_config import get_config
    from ...web import app

    config = get_config()

    app.secret_key = config.getstr('web', 'secret_key', fallback=secrets.token_hex(64))

    app.config['username'] = config.getstr('web', 'auth', 'username', fallback=None)
    app.config['password'] = config.getstr('web', 'auth', 'password', fallback=None)

    app.wsgi_app = DispatcherMiddleware(
        Response('Not Found', status=404),
        {config.getstr('web', 'baseurl', fallback="/"): app.wsgi_app},
    )

    config = get_config()

    app.run(
        host=config.getstr('web', 'host', fallback=None),
        port=config.getint('web', 'port', fallback=None),
        debug=config.getboolean('web', 'debug', fallback=False),
    )
