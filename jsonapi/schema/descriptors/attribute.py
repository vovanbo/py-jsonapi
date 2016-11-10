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
jsonapi.schema.descriptors.attribute
====================================

The :class:`Attribute` descriptor allows you to declare a JSON API attribute
on a :class:`~jsonapi.schema.schema.Schema`.
"""

# std
import logging

# local
from .base_property import WriteableProperty
from jsonapi.core.errors import ReadOnlyField


__all__ = [
    "Attribute"
]


LOG = logging.getLogger(__file__)


class Attribute(WriteableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-attributes

    This descriptor can be used to mark methods for getting and changing the
    value of an attribute.

    :arg callable fget:
        ``fget(schema, resource, request)``
    :arg callable fset:
        ``fget(schema, resource, new_value, request)``
    :arg str name:
        The JSON API name of the attribute
    :arg str doc:
        The docstring of the property
    :arg bool writable:
        If true, the attribute is writable.
    """

    def __init__(
        self, *, fget=None, fset=None, name="", doc="", writable=False
        ):
        super().__init__(
            fget=fget, fset=fset, name=name, doc=doc, writable=writable
        )
        return None

    def default_get(self, schema, resource, request):
        return getattr(resource, self.key)

    def default_set(self, schema, resource, new_value, request):
        if not self.writable:
            raise ReadOnlyField(schema.typename, self.name)
        if self.fget:
            LOG.warning(
                "The attribute '%s.%s' has a *getter*, but no *setter*. "\
                "You should either define a *setter* or mark it as not "\
                "*writable*.", schema.typename, self.name
            )
        setattr(resource, self.key, new_value)
        return None
