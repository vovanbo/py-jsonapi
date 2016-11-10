#!/usr/bin/env python3

import flask
from jsonapi_flask.api import API

from ..sql import Session


def create_api():
    """
    Creates the API instance and adds all types to it.
    """
    api = API("/api/")

    # Add the user api.
    from . import user
    user.init_api(api)

    # Add the post api.
    from . import post
    post.init_api(api)
    return api
