#!/usr/bin/env python3

import flask


def create_app():
    """
    Creates the flask application, which serves the API.
    """
    app = flask.Flask(__name__)

    # Create the tables for our models.
    from . import models
    from .sql import Base, engine
    Base.metadata.create_all(bind=engine)

    # Bind the API to the flask application.
    from .api import create_api
    api = create_api()
    api.init_app(app)
    return app
