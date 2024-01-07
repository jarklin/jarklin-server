# -*- coding=utf-8 -*-
r"""

"""
import flask


application = flask.Flask(__name__)


@application.get("/")
def index():
    return "Hello World"
