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

The response builders make it easier to create common response types (
collection, resource, new resource, relationship, ...).
"""

# std
import logging

# local
from .response import Response


__all__ = [
    "ResponseBuilder",
    "IncludeMixin",
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
        The request context
        """
        return self.__request

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


class IncludeMixin(object):
    """
    Mixin for fetching all include paths specified in the requests query string.
    """

    def __init__(self, included=None):
        self.included = included or list()
        return None

    def fetch_include(self):
        """
        If :attr:`data` contains resources, this method will fetch all related
        resources.
        """
        typename = self.request.japi_uri_arguments["type"]
        includer = self.api.get_includer(typename, None)
        if includer is None:
            return None

        data = getattr(self, "data", None) or list()
        data = data if isinstance(data, list) else [self.data]

        included = includer.fetch_paths(
            data, self.request.japi_include, self.request
        )
        self.included.extend(included)
        return None


class Collection(ResponseBuilder, IncludeMixin):
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
        ResponseBuilder.__init__(self, request=request)
        IncludeMixin.__init__(self, included=included)

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

        if self.pagination is not None:
            d.setdefault("links", dict()).update(self.pagination.json_links())
            d.setdefault("meta", dict()).update(self.pagination.json_meta())
        return d


class Resource(ResponseBuilder, IncludeMixin):
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
        ResponseBuilder.__init__(self, request=request)
        IncludeMixin.__init__(self, included=included)

        self.data = data
        self.included = included or list()
        self.links = links or dict()
        self.meta = meta or dict()
        return None

    def render(self):
        """
        """
        d = super().render()

        if self.data is None:
            d["data"] = None
        else:
            d["data"] = self.api.serialize(self.data, self.request)

        if self.included:
            d["included"] = self.api.serialize_many(self.included, self.request)
        if self.links:
            d["links"] = self.links
        if self.meta:
            d["meta"] = self.meta
        return d


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
        encoder = self.api.get_encoder(self.resource)
        relationship_object = encoder.serialize_relationship(
            relname=self.relname, resource=self.resource, request=self.request,
            require_data=True, pagination=self.pagination
        )

        d = super().render()
        d.update(relationship_object)

        if self.pagination is not None:
            d.setdefault("links", dict()).update(self.pagination.json_links())
            d.setdefault("meta", dict()).update(self.pagination.json_meta())
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
        return d
