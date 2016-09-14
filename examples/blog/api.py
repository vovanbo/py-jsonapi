#!/usr/bin/env python3

import flask

import jsonapi
import jsonapi_flask

from models import User, Post
from api_types import UserAPI, PostAPI
from sql import Base, engine, Session


class API(jsonapi_flask.api.API):

    def prepare_request(self, request):
        """
        This method is called, before a request is given to the request handler.
        """
        # Create a new sqlalchemy session, which can be used during the request.
        session = Session()
        request.settings["sql_session"] = session

        # Load the current user from the database.
        # - Since py-jsonapi requires a web framework on top, we don't have
        #   cookies. So load the first user from the database -_-
        #
        # In a production setup, you would have loaded the OAuth
        # token or something similar.
        user = session.query(User).first()
        print("The user '{}' is logged in.".format(user))
        request.settings["user"] = user
        return None


def create_api():
    """
    Creates the API instance and adds all types to it.
    """
    api = API("/api/")

    user_api = UserAPI()
    api.add_type(user_api)

    post_api = PostAPI()
    api.add_type(post_api)
    return api


def create_app():
    """
    Creates the flask application, which serves the API.
    """
    app = flask.Flask(__name__)

    # Create the tables for our models.
    Base.metadata.create_all(bind=engine)

    # Bind the API to the flask application.
    api = create_api()
    api.init_app(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
