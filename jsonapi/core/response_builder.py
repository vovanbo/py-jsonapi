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
jsonapi.core.response_builder
=============================

This module contains some helper classes, which help building the most common
JSON API response types.
"""

# std
import logging

# local
from .response import Response


__all__ = [
    "ResponseBuilder",
    "Collection",
    "Resource",
    "NewResource",
    "Relationship",
    "MetaOnly"
]


LOG = logging.getLogger(__file__)


class ResponseBuilder(object):
    """
    This class helps building a JSON API response.

    :arg ~jsonapi.core.request.Request request:
        The request, to which this object responds
    """

    def __init__(self, request):
        self.__request = request
        self.__api = request.api
        return None

    @property
    def api(self):
        """
        The :class:`~jsonapi.core.api.API`, which handles the :attr:`request`.
        """
        return self.__api

    @property
    def request(self):
        """
        The request, to which we built the response.
        """
        return self.__request

    def fetch_include(self):
        """
        If :attr:`data` contains resources, this method will fetch all related
        resources.
        """
        typename = self.__request.japi_uri_arguments["type"]
        includer = self.__api.get_includer(typename)

        data = getattr(self, "data", None) or list()
        data = data if isinstance(data, list) else [self.data]

        # If this is an asynchronous includer, this will return a coroutine,
        # but that is fine.
        return includer.fetch_include(
            data, self.__request.japi_include, self.__request
        )

    def render(self):
        """
        :rtype: dict
        :returns:
            The JSON API response document
        """
        d = dict()
        d["jsonapi"] = self.__api.jsonapi_object
        return d

    def to_response(self, status=200, headers=None):
        """
        Builds the :class:`~jsonapi.core.response.Response` and sets
        the ``application/vnd.api+json`` content type header.

        :rtype: ~jsonapi.core.response.Response
        """
        headers = headers or dict()
        headers["content-type"] = "application/vnd.api+json"

        body = self.render()
        body = self.__api.dump_json(body)

        resp = Response(status=status, headers=headers, body=body)
        return resp


class Collection(ResponseBuilder):
    """
    Builds a collection response. The primary :attr:`data` contains a list
    of resources.

    :arg ~jsonapi.core.request.Request request:
        The request, to which this object responds
    :arg list data:
        A list of resources of the same type
    :arg list included:
        A list of all related resources, which should be included into the
        response.
    :arg dict links:
        The JSON API links object
    :arg dict meta:
        The JSON API meta object
    :arg ~jsonapi.core.pagination.BasePagination pagination:
        A pagination instance, which describes the pagination of the collection.
    """

    def __init__(
        self, request, *, data=None, included=None, links=None, meta=None,
        pagination=None
        ):
        """
        """
        super().__init__(request=request)

        self.data = data or list()
        self.included = included or list()
        self.links = links or dict()
        self.meta = meta or dict()

        self.pagination = pagination
        return None

    def render(self):
        """
        """
        d = super().render()
        d["data"] = self.api.serialize_many(self.data, self.request)
        if self.included:
            d["included"] = self.api.serialize_many(self.included, self.request)
        if self.links:
            d["links"] = self.links
        if self.meta:
            d["meta"] = self.meta

        if pagination is not None:
            d.setdefault("links", dict()).update(pagination.json_links())
            d.setdefault("meta", dict()).update(pagination.json_meta())
        return d


class Resource(ResponseBuilder):
    """
    Contains a resource or ``None`` as primary :attr:`data`.

    :arg ~jsonapi.core.request.Request request:
        The request, to which this object responds
    :arg data:
        A single resource or ``None``.
    :arg list included:
        A list of all related resources, which should be included into the
        response.
    :arg dict links:
        The JSON API links object
    :arg dict meta:
        The JSON API meta object
    """

    def __init__(
        self, request, *, data=None, included=None, links=None, meta=None
        ):
        """
        """
        super().__init__(request=request)

        self.data = data
        self.included = included or list()
        self.links = links or dict()
        self.meta = meta or dict()
        return None

    def render(self):
        """
        """
        d = super().render()
        d["data"] = self.api.serialize(self.data, self.request)
        if self.included:
            d["included"] = self.api.serialize_many(self.included, self.request)
        if self.links:
            d["links"] = self.links
        if self.meta:
            d["meta"] = self.meta
        return


class NewResource(Resource):
    """
    This response sets the ``LOCATION`` http header and should be used for
    a new resource, which has been created during the request handling.
    """

    def to_response(self, status=200, headers=None):
        """
        """
        headers = headers or dict()
        headers["location"] = self.api.resource_uri(self.data)
        return super().to_response(status=status, headers=headers)


class Relationship(ResponseBuilder):
    """
    Builds a JSON API response, which contains a relationship.

    :arg ~jsonapi.core.request.Request request:
        The request, to which this object responds
    :arg resource:
        A resource object
    :arg str relname:
        The name of the relationship, which is returned in the response.
        If not given, we will extract the name from the request.
    :arg ~jsonapi.core.pagination.BasePagination pagination:
        A pagination instance, which describes the pagination of the collection.
        (Only *to-many* relationships should support pagination.)
    """

    def __init__(
        self, request, *, resource=None, relname=None, pagination=None
        ):
        """
        """
        super().__init__(request=request)

        self.relname = relname or request.japi_uri_arguments["relname"]
        self.resource = resource
        self.pagination = pagination
        return None

    def render(self):
        """
        """
        encoder = self.api.get_encoder(resource)
        relationship_object = encoder.serialize_relationship(
            relname=self.relname, resource=resource, request=request,
            require_data=True, pagination=pagination
        )

        d = super().render()
        d.update(relationship_object)

        if pagination is not None:
            d.setdefault("links", dict()).update(pagination.json_links())
            d.setdefault("meta", dict()).update(pagination.json_meta())
        return d


class MetaOnly(ResponseBuilder):
    """
    Only responds with top-level :attr:`meta` data.

    :arg ~jsonapi.core.request.Request request:
        The request, to which this object responds
    :arg dict meta:
        The JSON API meta object
    """

    def __init__(self, request, *, meta=None):
        """
        """
        super().__init__(request=request)
        self.meta = meta or dict()
        return None

    def render(self):
        """
        """
        d = super().render()
        d["meta"] = self.meta
        return None
