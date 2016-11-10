#!/usr/bin/env python3

import jsonapi.core
import jsonapi.schema

from ..models import User


class UserSchema(jsonapi.schema.Schema):
    resource_class = User
    typename = "User"

    id = jsonapi.schema.ID()
    name = jsonapi.schema.Attribute(writable=True)
    posts = jsonapi.schema.ToManyRelationship(remote_types=["Post"])

    @jsonapi.schema.Meta()
    def greeting(self, user, request):
        return "Hello {}!".format(user.name)

    @jsonapi.schema.Link()
    def greeting_documentation(self, user, request):
        return "https://github.com"

    # Now we have to override some methods, to make sure, that changes made to
    # the models are stored in the database.
    #
    # We would not have to do this, if we used the sqlalchemy extension.

    def create_resource(self, data, *, request):
        new_user = super().create_resource(data, request=request)
        session = request.settings["sql_session"]
        session.add(new_user)
        session.commit()
        return new_user

    def update_resource(self, user, data, *, request):
        user = super().update_resource(user, data, request=request)
        session = request.settings["sql_session"]
        print(user.name)
        session.add(user)
        session.commit()
        return user

    def delete_resource(self, user, *, request):
        session = request.settings["sql_session"]

        # user is only the id of the user.
        if isinstance(user, str):
            user_id = user
            user = session.query(User).get(user_id)
            if user is None:
                raise jsonapi.core.errors.ResourceNotFound(user_id)

        session.delete(user)
        session.commit()
        return None


    def update_relationship(self, relname, user, data, *, request):
        user = super().update_relationship(relname, user, data, request=request)
        session = request.settings["sql_session"]
        session.add(user)
        session.commit()
        return user

    def add_relationship(self, relname, user, data, *, request):
        user = super().add_relationship(relname, user, data, request=request)
        session = request.settings["sql_session"]
        session.add(user)
        session.commit()
        return user

    def delete_relationship(self, relname, resource, data, *, request):
        user = super().delete_relationship(relname, user, data, request=request)
        session = request.settings["sql_session"]
        session.add(user)
        session.commit()
        return user


    def get_collection(self, *, request):
        session = request.settings["sql_session"]

        pagination = jsonapi.core.pagination.NumberSize.from_request(
            request, total_resources=session.query(User).count()
        )

        users = session.query(User)\
            .limit(pagination.limit)\
            .offset(pagination.offset)\
            .all()
        return (users, pagination)

    def get_resources(self, ids, *, request, include=None):
        session = request.settings["sql_session"]
        users = dict()
        for user_id in ids:
            user = session.query(User).get(user_id)
            if user is None:
                raise jsonapi.core.errors.ResourceNotFound((self.typename, user_id))
            users[("User", user_id)] = user
        return users
