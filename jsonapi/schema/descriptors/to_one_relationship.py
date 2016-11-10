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
jsonapi.schema.descriptors.to_one_relationship
==============================================
"""

# std
import logging

# local
from .relationship import Relationship


__all__ = [
    "ToOneRelationship"
]


LOG = logging.getLogger(__file__)


class ToOneRelationship(Relationship):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-linkage

    This descriptor can be used to mark the methods for getting and changing
    the value of a *to-one* relationship.

    :arg list remote_types:
        A list with the JSON API typenames of the related resources.
    :arg callable fget:
        ``fget(schema, resource, request)`` returning the related resource or
        ``None``.
    :arg callable fset:
        ``fset(schema, resource, d, new_relative, request)``
    :arg str name:
        The JSON API name of the relationship
    :arg str doc:
        The docstring ot this property
    :arg bool writable:
        If true, the default setter allows to change the value of the
        relationship.
    """

    to_one = True
    to_many = False

    def __init__(
        self, remote_types=None, *, fget=None, fset=None, name="", doc="",
        writable=False
        ):
        super().__init__(
            remote_types=remote_types,fget=fget, fset=fset, name=name, doc=doc,
            writable=writable
        )
        return None

    def default_get(self, schema, resource, request):
        return getattr(resource, self.key)

    def default_set(self, schema, resource, d, new_relative, request):
        if not self.writable:
            raise ReadOnlyField(schema.typename, self.name)
        if self.fget:
            LOG.warning(
                "The relationship '%s.%s' has a *getter*, but no *setter*. "\
                "You should either define a *setter* or mark it as not "\
                "*writable*.", schema.typename, self.name
            )
        return setattr(resource, self.key, new_relative)
