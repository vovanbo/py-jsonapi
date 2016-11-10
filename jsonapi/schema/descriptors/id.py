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
jsonapi.schema.descriptors.id
=============================
"""

# std
import logging

# local
from .base_property import WriteableProperty
from jsonapi.core.errors import Forbidden


__all__ = [
    "ID"
]


LOG = logging.getLogger(__file__)


class ID(WriteableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-identification

    The ID descriptor tells *py-jsonapi* how the id of a resource can be
    found and changed.

    :arg callable fget:
        ``fget(schema, resource)``
    :arg callable fset:
        ``fset(schema, resource, new_id, request)``
    :arg str doc:
        The documentation of this property.
    :arg bool writable:
        If ``True``, the id can be changed.
    """

    def __init__(self, *, fget=None, fset=None, doc="", writable=False):
        super().__init__(
            fget=fget, fset=fset, doc=doc, name="id", writable=writable
        )
        return None

    def default_set(self, schema, resource, new_id, request):
        if not self.writable:
            raise Forbidden(details="The 'id' is read-only.")
        if self.fget:
            LOG.warning(
                "The id of '%s' has a *getter*, but no *setter*. "\
                "You should either define a *setter* or mark it as not "\
                "*writable*.", schema.typename
            )
        setattr(resource, self.key, new_id)
        return None

    def default_get(self, schema, resource):
        return str(getattr(resource, self.key))
