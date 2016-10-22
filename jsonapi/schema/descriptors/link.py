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
jsonapi.schema.descriptors.link
===============================
"""

# std
import logging

# local
from .base_property import ReadableProperty


__all__ = [
    "Link"
]


LOG = logging.getLogger(__file__)


class Link(ReadableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-attributes

    This descriptor can be used to mark a link on a resource level.

    :arg str href:
        If given, this URL is returned if no *getter* is defined.
    :arg callable fget:
        ``fget(schema, resource, request)``
    :arg str name:
        The JSON API name of the link
    :arg str doc:
        The docstring of this property
    """

    def __init__(self, href="", *, fget=None, name="", doc=""):
        super().__init__(fget=fget, name=name, doc=doc)

        #: A string, which is simply return per default as the link's value.
        self.href = href
        return None

    def default_get(self, schema, resource, request):
        if self.href:
            return self.href
        else:
            return getattr(resource, self.key)
