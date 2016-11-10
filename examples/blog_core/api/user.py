#!/usr/bin/env python3

from jsonapi.core import encoder, includer, validator

from ..models import User, Post


__all__ = [
    "UserEncoder",
    "UserIncluder"
]


class UserEncoder(encoder.Encoder):
    resource_class = User

    name = encoder.Attribute()
    posts = encoder.ToManyRelationship()


class UserIncluder(includer.Includer):
    resource_class = User
    posts = includer.ToManyRelationship()

    def fetch_resources(self, ids, request):
        session = request.settings["sql_session"]
        resources = {id_: session.query(User).get(id_) for id_ in ids}
        return resources
