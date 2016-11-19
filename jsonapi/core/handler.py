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

This module contains the base class for all *py-jsonapi* resource handlers.
The implementation is straight forward::

    class Article(Handler):

        def get(self, request):
            pagination = jsonapi.core.pagination.NumberSize.from_request(
                request, query(Article).count()
            )
            articles = query(Article)\\
                .limit(pagination.limit)\\
                .offset(pagination.offset)\\
                .all()
            return jsonapi.core.response_builder.Collection(request, data=articles)

The handler receives a :class:`~jsonapi.core.request.Request` instance as
parameter and returns either a :class:`~jsonapi.core.response.Response`
or a :class:`~jsonapi.core.response_builder.ResponseBuilder` object.

If a :class:`~jsonapi.core.response_builder.ResponseBuilder` is returned,
the :meth:`~jsonapi.core.response_builder.IncludeMixin.fetch_include` method
is called automatic.
"""

# std
import logging

# local
from . import errors


__all__ = [
    "Handler"
]


LOG = logging.getLogger(__file__)


class Handler(object):
    """
    The interface for a request handler.

    :arg ~jsonapi.core.api.API api:
        The API, which owns this handler.
    """

    def __init__(self, api=None):
        self.api = api
        return None

    def init_api(self, api):
        """
        Binds the handler to the *api*.

        :arg ~jsonapi.core.api.API:
        """
        assert self.api is None or self.api is api
        self.api = api
        return None

    def handle(self, request):
        """
        Calls the correct handler method (*get*, *patch*, ...) depending on HTTP
        :attr:`~jsonapi.core.request.Request.method`.

        :arg ~jsonapi.core.request.Request request:

        :returns:
            A :class:`~jsonapi.core.response.Response` or
            :class:`~jsonapi.core.response_builder.ResponseBuilder`
        """
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
