#!/usr/bin/env python3

import jsonapi.core
import jsonapi.schema

from ..models import Post


class PostSchema(jsonapi.schema.Schema):
    resource_class = Post
    typename = "Post"

    id = jsonapi.schema.ID()
    text = jsonapi.schema.Attribute(writable=True)
    author = jsonapi.schema.ToOneRelationship(remote_types=["Post"], writable=True)

    # Now we have to override some methods, to make sure, that changes made to
    # the models are stored in the database.
    #
    # We would not have to do this, if we used the sqlalchemy extension.

    def create_resource(self, data, *, request):
        new_post = super().create_resource(data, request=request)
        session = request.settings["sql_session"]
        session.add(new_post)
        session.commit()
        return new_post

    def update_resource(self, post, data, *, request):
        post = super().update_resource(post, data, request=request)
        session = request.settings["sql_session"]
        session.add(post)
        session.commit()
        return post

    def delete_resource(self, post, *, request):
        session = request.settings["sql_session"]

        # post is only the id of the post.
        if isinstance(post, str):
            post_id = post
            post = session.query(Post).get(post_id)
            if post is None:
                raise jsonapi.core.errors.ResourceNotFound(post_id)

        session.delete(post)
        session.commit()
        return None


    def update_relationship(self, relname, post, data, *, request):
        post = super().update_relationship(relname, post, data, request=request)
        session = request.settings["sql_session"]
        session.add(post)
        session.commit()
        return post

    def add_relationship(self, relname, post, data, *, request):
        post = super().add_relationship(relname, post, data, request=request)
        session = request.settings["sql_session"]
        session.add(post)
        session.commit()
        return post

    def delete_relationship(self, relname, resource, data, *, request):
        post = super().delete_relationship(relname, post, data, request=request)
        session = request.settings["sql_session"]
        session.add(post)
        session.commit()
        return post


    def get_collection(self, *, request):
        session = request.settings["sql_session"]

        pagination = jsonapi.core.pagination.NumberSize.from_request(
            request, total_resources=session.query(Post).count()
        )

        posts = session.query(Post)\
            .limit(pagination.limit)\
            .offset(pagination.offset)\
            .all()
        return (posts, pagination)

    def get_resources(self, ids, *, request, include=None):
        session = request.settings["sql_session"]
        posts = dict()
        for post_id in ids:
            post = session.query(Post).get(post_id)
            if post is None:
                raise jsonapi.core.errors.ResourceNotFound((self.typename, post_id))
            posts[("Post", post_id)] = post
        return posts
