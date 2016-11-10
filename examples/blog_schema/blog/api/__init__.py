#!/usr/bin/env python3

import flask

from jsonapi_flask.api import API as FlaskAPI
from jsonapi.schema import add_schema

from ..sql import Session


class API(FlaskAPI):

    def prepare_request(self, request):
        request.settings["sql_session"] = Session()
        return None


def create_api():
    """
    Creates the API instance and adds all types to it.
    """
    api = API("/api/")

    # Add the user schema
    from .user import UserSchema
    add_schema(api, UserSchema())

    # Add the post schema
    from .post import PostSchema
    add_schema(api, PostSchema())
    return api
