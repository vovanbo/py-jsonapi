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


@flask.request_started.connect
def _create_session(*args, **kargs):
    """
    Create the sql session, which is used during a request.
    """
    from .sql import Session
    flask.g.sql_session = Session()
    return None


@flask.request_tearing_down.connect
def _close_session(*args, **kargs):
    """
    Close the sql session created at the begin of the request.
    """
    flask.g.sql_session.close()
    return None
