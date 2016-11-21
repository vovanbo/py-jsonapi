#!/usr/bin/env python3

import flask
import mongoengine

from api import create_api
from model import Employee


def create_app():
    """
    Factory function for the main flask application.
    """
    app = flask.Flask(__name__)

    api = create_api()
    api.init_app(app)
    return app


if __name__ == "__main__":
    mongoengine.connect()
    #Employee.drop_collection()

    app = create_app()
    app.run(debug=True)
