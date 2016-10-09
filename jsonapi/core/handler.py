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
jsonapi.core.handler
====================

The JSON API specification knows four different endpoint types:

*   Collection
*   Resource
*   Relationship
*   and Related.

This module contains the handlers, which implement the logic for handling
a request to one of those endpoints, based on a
:class:`~jsonapi.core.schema.type.Type`.
"""

# std
from collections import OrderedDict
import json
import logging

# local
from . import errors
from . import validation
from .response import Response
from .pagination import Pagination


__all__ = [
    "Handler",
    "CollectionHandler",
    "ResourceHandler",
    "RelationshipHandler",
    "ToOneRelationshipHandler",
    "ToManyRelationshipHandler",
    "RelatedHandler",
    "ToOneRelatedHandler",
    "ToManyRelatedHandler"
]


LOG = logging.getLogger(__file__)


class Handler(object):
    """
    The interface for request handlers.

    :arg ~jsonapi.core.api.API api:
        The API, which owns this handler.
    :arg ~jsonapi.core.schema.Type type_:
        The Type, which is associated with this handler.
    """

    def __init__(self, api, type_):
        self.api = api
        self.type = type_
        return None

    def handle(self, request):
        if request.method == "delete":
            return self.delete(request)
        elif request.method == "get":
            return self.get(request)
        elif request.method == "head":
            return self.head(request)
        elif request.method == "post":
            return self.post(request)
        elif request.method == "patch":
            return self.patch(request)
        elif request.method == "options":
            return self.options(request)
        raise errors.MethodNotAllowed()

    def delete(self, request):
        raise errors.MethodNotAllowed()

    def get(self, request):
        raise errors.MethodNotAllowed()

    def head(self, request):
        raise errors.MethodNotAllowed()

    def post(self, request):
        raise errors.MethodNotAllowed()

    def patch(self, request):
        raise errors.MethodNotAllowed()

    def options(self, request):
        raise errors.MethodNotAllowed()


class CollectionHandler(Handler):
    """
    Handles the collection endpoint for a resource type.

    Example: **/api/articles/**
    """

    def get(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.get_collection`
        :seealso: http://jsonapi.org/format/#fetching-resources
        """
        # Fetch the resources
        resources, total_number = self.type.get_collection(
            query_params = {
                "filters": request.japi_filters,
                "sort": request.japi_sort,
                "limit": request.japi_page_limit,
                "offset": request.japi_page_offset,
                "include": request.japi_include
            },
            request=request
        )
        included = self.api.get_included(
            resources, request.japi_include, request
        )

        # Build the response body
        body = OrderedDict()
        body["data"] = self.api.serialize_many(resources, request)
        body["included"] = self.api.serialize_many(included, request)
        body["jsonapi"] = self.api.jsonapi_object

        if request.japi_paginate:
            pager = Pagination.from_request(request, total_number)
            body.setdefault("meta", OrderedDict()).update(pager.json_meta)
            body.setdefault("links", OrderedDict()).update(pager.json_links)

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp

    def post(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.create_resource`
        :seealso: http://jsonapi.org/format/#crud-creating

        .. todo::

            Support other *success* status codes, like *202 Accepted* or
            *204 No Content*.
        """
        if request.content_type[0] != "application/vnd.api+json":
            raise errors.UnsupportedMediaType()

        # Create the new resource
        validation.assert_data_is_resource_object(request.json)
        resource = self.type.create_resource(request.json["data"], request)
        included = self.api.get_included(
            [resource], request.japi_include, request
        )

        # Build the response body.
        body = OrderedDict()
        body["data"] = self.api.serialize(resource, request)
        body["included"] = self.api.serialize_many(included, request)
        body["jsonapi"] = self.api.jsonapi_object

        # Build the response header.
        headers = dict()
        headers["content-type"] = "application/vnd.api+json"
        headers["location"] = self.api.resource_uri(resource)

        # Create the response
        resp = Response(
            status=201,
            headers=headers,
            body=self.api.dump_json(body)
        )
        return resp


class ResourceHandler(Handler):
    """
    Handles the resource endpoint.

    Example: **/api/articles/42**
    """

    def get(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.get_resource`
        :seealso: http://jsonapi.org/format/#fetching-resources
        """
        # Fetch the resource
        resource = self.type.get_resource(
            request.japi_uri_arguments["id"], request.japi_include, request
        )
        included = self.api.get_included(
            [resource], request.japi_include, request
        )

        # Build the response body
        body = OrderedDict()
        body["data"] = self.api.serialize(resource, request)
        body["included"] = self.api.serialize_many(included, request)
        body["jsonapi"] = self.api.jsonapi_object

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp

    def patch(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.update_resource`
        :seealso: http://jsonapi.org/format/#crud-updating

        .. todo::

            Support other status codes like *202 Accepted* or *204 No Content*.
        """
        if request.content_type[0] != "application/vnd.api+json":
            raise errors.UnsupportedMediaType()

        # The update method of the Type will automatically load the
        # resource if it is not yet loaded and return it.
        validation.assert_data_is_resource_object(request.json)
        resource = self.type.update_resource(
            request.japi_uri_arguments["id"], request.json["data"], request
        )
        included = self.api.get_included(
            [resource], request.japi_include, request
        )

        # Build the response body
        body = OrderedDict()
        body["data"] = self.api.serialize(resource, request)
        body["included"] = self.api.serialize_many(included, request)
        body["jsonapi"] = self.api.jsonapi_object

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp

    def delete(self, request):
        """
        :seealso: http://jsonapi.org/format/#crud-deleting
        :seealso: :meth:`~jsonapi.core.schema.type.Type.delete_resource`

        .. todo::

            Support other status codes like *202 Accepted* or *200 OK*.
        """
        # Delete the resource
        self.type.delete_resource(request.japi_uri_arguments["id"], request)

        # Create the response
        resp = Response(
            status=204,
            headers={"content-type": "application/vnd.api+json"}
        )
        return resp


class RelationshipHandler(Handler):
    """
    The base for the relationship handler endpoints
    :class:`ToOneRelationshipHandler`, :class:`ToManyRelationshipHandler`.
    """

    def __init__(self, api, type_, relname):
        assert relname in type_.relationships

        super().__init__(api=api, type_=type_)
        self.relname = relname
        return None

    def get(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.serialize_relationship`
        :seealso: http://jsonapi.org/format/#fetching-relationships
        """
        # Get the resource
        resource = self.type.get_resource(
            request.japi_uri_arguments["id"], [[self.relname]], request
        )

        # Build the body.
        body = self.type.serialize_relationship(
            self.relname, resource, request, require_data=True
        )
        body["jsonapi"] = self.api.jsonapi_object

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp

    def patch(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.update_relationship`
        :seealso: http://jsonapi.org/format/#crud-updating-relationships

        .. todo::

            Support other status codes like *202 Accepted* or *204 No Content*.
        """
        if request.content_type[0] != "application/vnd.api+json":
            raise errors.UnsupportedMediaType()

        # Get the resource
        validation.assert_relationship_object(request.json)
        resource = self.type.update_relationship(
            self.relname, request.japi_uri_arguments["id"], request.json,
            request
        )

        # Build the body.
        body = self.type.serialize_relationship(
            self.relname, resource, request, require_data=True
        )
        body["jsonapi"] = self.api.jsonapi_object

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp


class ToOneRelationshipHandler(RelationshipHandler):
    """
    The handler for a *to-one* relationship endpoint
    """


class ToManyRelationshipHandler(RelationshipHandler):
    """
    The handler for a *to-many* relationship endpoint

    This handler also supports the *POST* and *DELETE* http methods for
    extending and clearing the relationship list.
    """

    def post(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.extend_relationship`
        :seealso: http://jsonapi.org/format/#crud-updating-relationships (POST)
        """
        if request.content_type[0] != "application/vnd.api+json":
            raise errors.UnsupportedMediaType()

        # Get the resource
        validation.assert_relationship_object(request.json)
        resource = self.type.extend_relationship(
            self.relname, request.japi_uri_arguments["id"], request.json,
            request
        )

        # Build the body.
        body = self.type.serialize_relationship(
            self.relname, resource, request, require_data=True
        )
        body["jsonapi"] = self.api.jsonapi_object

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp

    def delete(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.remove_relationship`
        :seealso: http://jsonapi.org/format/#crud-updating-relationships (DELETE)
        """
        if request.content_type[0] != "application/vnd.api+json":
            raise errors.UnsupportedMediaType()

        # Get the resource
        validation.assert_relationship_object(request.json)
        resource = self.type.remove_relationship(
            self.relname, request.japi_uri_arguments["id"], request.json,
            request
        )

        # Build the body.
        body = self.type.serialize_relationship(
            self.relname, resource, request, require_data=True
        )
        body["jsonapi"] = self.api.jsonapi_object

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp


class RelatedHandler(Handler):
    """
    The base for the *related* endpoint handlers :class:`ToOneRelatedHandler`,
    :class:`ToManyRelatedHandler`.
    """

    def __init__(self, api, type_, relname):
        super().__init__(api=api, type_=type_)
        self.relname = relname
        return None


class ToOneRelatedHandler(RelatedHandler):
    """
    The *related* endpoint handler for a *to-one* relationship.
    """

    def get(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.get_related`
        :seealso: http://jsonapi.org/format/#fetching-includes
        """
        # Get the resource
        relative, total_number = self.type.get_related(
            self.relname, request.japi_uri_arguments["id"],
            query_params={"include": request.japi_include},
            request=request
        )

        if relative:
            included = self.api.get_included(
                [relative], request.japi_include, request
            )

            # Build the response body.
            body = OrderedDict()
            body["data"] = self.api.serialize(relative, request)
            body["included"] = self.api.serialize_many(included, request)
            body["jsonapi"] = self.api.jsonapi_object
        else:
            body = OrderedDict()
            body["data"] = None
            body["jsonapi"] = self.api.jsonapi_object

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp


class ToManyRelatedHandler(RelatedHandler):
    """
    The *related* endpoint handler for a *to-many* relationship.
    """

    def get(self, request):
        """
        :seealso: :meth:`~jsonapi.core.schema.type.Type.get_related`
        :seealso: http://jsonapi.org/format/#fetching-includes
        """
        # Get the resource
        relatives, total_number = self.type.get_related(
            self.relname, request.japi_uri_arguments["id"],
            query_params={
                "filters": request.japi_filters,
                "order": request.japi_sort,
                "limit": request.japi_page_limit,
                "offset": request.japi_page_offset,
                "include": request.japi_include
            },
            request=request
        )
        included = self.api.get_included(
            relatives, request.japi_include, request
        )

        # Build the body.
        body = OrderedDict()
        body["data"] = self.api.serialize_many(relatives, request)
        body["included"] = self.api.serialize_many(included, request)
        body["jsonapi"] = self.api.jsonapi_object

        if request.japi_paginate:
            pager = Pagination.from_request(request, total_number)
            body.setdefault("meta", OrderedDict()).update(pager.meta)
            body.setdefault("links", OrderedDict()).update(pager.links)

        # Create the response
        resp = Response(
            status=200,
            headers={"content-type": "application/vnd.api+json"},
            body=self.api.dump_json(body)
        )
        return resp
