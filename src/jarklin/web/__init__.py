# -*- coding=utf-8 -*-
r"""

"""
from http import HTTPStatus
import flask
from werkzeug.exceptions import NotFound


application = flask.Flask(__name__)


@application.get("/")
@application.get("/<path:resource>")
def index(resource: str = "./"):
    if resource.endswith("/"):
        resource += "index.html"
    try:
        return flask.send_from_directory("./web-ui/", resource)
    except NotFound:
        return flask.send_from_directory("./web-ui/", "404.html"), HTTPStatus.NOT_FOUND
