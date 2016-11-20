#!/usr/bin/env python3

from flask import g
import jsonapi.core as jsonapi
from ..models import User, Post


__all__ = [
    "init_api"
]


class PostEncoder(jsonapi.encoder.Encoder):
    resource_class = Post

    text = jsonapi.encoder.Attribute()

    @jsonapi.encoder.ToOneRelationship()
    def author(self, post, request, *, require_data=False):
        d = dict()
        if post.author_id:
            d["data"] = {"type": "User", "id": str(post.author_id)}
        else:
            d["data"] = None
        return d


class PostIncluder(jsonapi.includer.Includer):
    resource_class = Post
    author = jsonapi.includer.ToOneRelationship()


class BasePostValidator(jsonapi.validator.Validator):
    id = jsonapi.validator.ID(regex="\d+")
    type = jsonapi.validator.Type(types=["Post"])


class NewPostValidator(BasePostValidator):
    text = jsonapi.validator.Attribute(type=str, required=True)
    author = jsonapi.validator.ToOneRelationship(
        types=["User"], required=True, require_data=True
    )


class UpdatePostValidator(BasePostValidator):
    text = jsonapi.validator.Attribute(type=str)
    author = jsonapi.validator.ToOneRelationship(
        types=["User"], require_data=True
    )


class PostCollection(jsonapi.handler.Handler):

    def get(self, request):
        pagination = jsonapi.pagination.NumberSize.from_request(
            request, g.sql_session.query(Post).count()
        )
        posts = g.sql_session.query(Post)\
            .limit(pagination.limit).offset(pagination.offset)

        resp = jsonapi.response_builder.Collection(
            request, data=posts, pagination=pagination
        )
        resp.fetch_include()
        return resp.to_response()

    def post(self, request):
        NewPostValidator().assert_resource_object(request.json)

        # Load the author.
        author_id = request.json["relationships"]["author"]["data"]["id"]
        author = g.sql_session.query(User).get(author_id)
        if author is None:
            raise jsonapi.errors.NotFound()

        # Create the new post.
        post = Post(
            text=request.json["attributes"]["text"],
            author=author
        )
        g.sql_session.add(post)
        g.sql_session.commit()

        resp = jsonapi.response_builder.NewResource(request, data=post)
        resp.fetch_include()
        return resp.to_response()


class PostResource(jsonapi.handler.Handler):

    def get(self, request):
        post = g.sql_session.query(Post).get(request.japi_uri_arguments["id"])
        if post is None:
            raise jsonapi.errors.NotFound()

        resp = jsonapi.response_builder.Resource(request, data=post)
        resp.fetch_include()
        return resp

    def patch(self, request):
        post = g.sql_session.query(Post).get(request.japi_uri_arguments["id"])
        if post is None:
            raise jsonapi.errors.NotFound()

        UpdatePostValidator().assert_resource_object(request.json)

        if "text" in request.json["attributes"]:
            post.text = request.json["attributes"]["text"]
        if "author" in request.json["relationships"]:
            author_id = request.json["relationships"]["author"]["data"]["id"]
            author = g.sql_session.query(User).get(author_id)
            if author is None:
                raise jsonapi.errors.NotFound()

            post.author = author

        g.sql_session.add(post)
        g.sql_session.commit()

        resp = jsonapi.response_builder.Resource(request, data=post)
        resp.fetch_include()
        return resp.to_response()

    def delete(self, request):
        post = g.sql_session.query(Post).get(request.japi_uri_arguments["id"])
        if post is None:
            raise jsonapi.errors.NotFound()

        g.sql_session.delete(post)
        g.commit()
        return jsonapi.response.Response(status=204)


class PostRelationshipsAuthor(jsonapi.handler.Handler):

    def get(self, request):
        post = g.sql_session.query(Post).get(request.japi_uri_arguments["id"])
        if post is None:
            raise jsonapi.errors.NotFound()

        resp = jsonapi.response_builder.Relationship(request, data=post)
        return resp.to_response()


class PostRelatedPosts(jsonapi.handler.Handler):

    def get(self, request):
        post = g.sql_session.query(Post)\
            .options(sqlalchemy.subqueryload("author"))\
            .get(request.japi_uri_arguments["id"])
        if post is None:
            raise jsonapi.errors.NotFound()

        resp = jsonapi.response_builder.Resource(request, data=post.author)
        resp.fetch_include()
        return resp.to_response()


def init_api(api):
    encoder = PostEncoder()
    includer = PostIncluder()

    api.add_type(encoder, includer)
    api.add_handler(
        handler=PostCollection(), typename=encoder.typename,
        endpoint_type="collection"
    )
    api.add_handler(
        handler=PostResource(), typename=encoder.typename,
        endpoint_type="resource"
    )
    api.add_handler(
        handler=PostRelationshipsAuthor(), typename=encoder.typename,
        endpoint_type="relationship", relname="author"
    )
    api.add_handler(
        handler=PostRelatedPosts(), typename=encoder.typename,
        endpoint_type="related", relname="author"
    )
    return None
