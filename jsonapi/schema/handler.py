#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2016 Benedikt Schmitt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
jsonapi.schema.handler
======================
"""

# std
import logging

# local
from jsonapi.core import response_builder
from jsonapi.core.handler import Handler as BaseHandler


__all__ = [
    "Collection",
    "Resource",
    "Relationship",
    "ToOneRelationship",
    "ToManyRelationship",
    "Related",
    "ToOneRelated",
    "ToManyRelated"
]


LOG = logging.getLogger(__file__)


class Handler(BaseHandler):
    """
    The base for all handlers, which are built upon a :class:`Schema`.

    :arg ~jsonapi.core.api.API api:
        The API, which owns this handler.
    :arg ~jsonapi.schema.schema.Schema schema:
        The schema (controller), which will be used to handle the request.
    """

    def __init__(self, api, schema):
        self.api = api
        self.schema = schema
        return None


class Collection(Handler):
    """
    ``/api/Article/``

    The collection endpoint allows the client to query a list with all resources
    in the collection and to create new resources.
    """

    def get(self, request):
        data, pagination = self.schema.get_collection(request)
        resp = response_builder.Collection(
            request=request, data=data, pagination=pagination
        )
        resp.fetch_include()
        return resp.to_response()

    def post(self, request):
        resource = self.schema.create_resource(
            data=request.json, request=request
        )
        resp = response_builder.NewResource(request=request, data=resource)
        resp.fetch_include()
        return resp.to_response()


class Resource(Handler):
    """
    ``/api/Article/42``

    The resource endpoint allows the client to fetch, update and delete a
    resource.
    """

    def __init__(self, api, schema):
        self.api = api
        self.schema = schema
        return None

    def get(self, request):
        resource_id = request.japi_uri_arguments["id"]
        resource = self.schema.get_resource(
            resource_id, request.japi_include, request=request
        )
        resp = response_builder.Resource(request=request, data=resource)
        resp.fetch_include()
        return resp.to_response()

    def patch(self, request):
        resource_id = request.japi_uri_arguments["id"]
        resource = self.schema.update_resource(
            resource_id, request.json, request=request
        )
        resp = response_builder.Resource(request=request, data=resource)
        resp.fetch_include()
        return resp.to_response()

    def delete(self, request):
        resource_id = request.japi_uri_arguments["id"]
        self.schema.delete_resource(resource_id, request=request)
        return Response(status=204)


class Relationship(Handler):
    """
    ``/api/Article/42/relationships/author``,
    ``/api/Article/42/relationships/comments``

    All relationship endpoints allow the client to get the relationship
    (linkage) and to update it.
    """

    def get(self, request):
        relname = request.japi_uri_arguments["relname"]
        resource_id = request.japi_uri_arguments["id"]
        resource = self.schema.get_resource(
            resource_id, include=[relname], request=request
        )
        resp = response_builder.Relationship(
            request=request, resource=resource, relname=relname
        )
        return resp.to_response()

    def patch(self, request):
        relname = request.japi_uri_arguments["relname"]
        resource_id = request.japi_uri_arguments["id"]
        resource = self.schema.update_relationship(
            relname, resource_id, request.json, request=request
        )
        resp = response_builder.Relationship(
            request=request, resource=resource, relname=relname
        )
        return resp.to_response()


class ToOneRelationship(Relationship):
    """
    ``/api/Article/42/relationships/author``,

    The *to-one* relationship endpoint allows the client to get and update
    the relationship.
    """


class ToManyRelationship(Relationship):
    """
    ``/api/Article/42/relationships/comments``,

    The *to-one* relationship endpoint allows the client to get and update
    the relationship. It also supports adding and deleting relatives.
    """

    def post(self, request):
        relname = request.japi_uri_arguments["relname"]
        resource_id = request.japi_uri_arguments["id"]
        resource = self.schema.add_relationship(
            relname, resource_id, request.json, request=request
        )
        resp = response_builder.Relationship(
            request=request, resource=resource, relname=relname
        )
        return resp.to_response()

    def delete(self, request):
        relname = request.japi_uri_arguments["relname"]
        resource_id = request.japi_uri_arguments["id"]
        resource = self.schema.delete_relationship(
            relname, resource_id, request.json, request=request
        )
        resp = response_builder.Relationship(
            request=request, resource=resource, relname=relname
        )
        return resp.to_response()


class Related(Handler):
    """
    ``/api/Article/42/author``, ``/api/Article/42/comments``

    The related endpoint allows a client to query the related resources.
    """


class ToOneRelated(Related):
    """
    ``/api/Article/42/author``

    Handles the related endpoint of a *to-one* relationship.
    """

    def get(self, request):
        relname = request.japi_uri_arguments["relname"]
        resource_id = request.japi_uri_arguments["id"]
        resource = self.schema.get_related(
            relname, resource_id, request=request
        )
        resp = response_builder.Resource(request=request, data=resource)
        resp.fetch_include()
        return resp.to_response()


class ToManyRelated(Handler):
    """
    ``/api/Article/42/comments``

    Handles the related endpoint of a *to-many* relationship. This endpoint
    will return a collection as response.
    """

    def get(self, request):
        relname = request.japi_uri_arguments["relname"]
        resource_id = request.japi_uri_arguments["id"]
        resources = self.schema.get_related(
            relname, resource_id, request=request
        )
        resp = response_builder.Collection(request=request, data=resources)
        resp.fetch_include()
        return resp.to_response()
