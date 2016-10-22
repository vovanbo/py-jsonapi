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
jsonapi.schema.descriptors.meta
===============================
"""

# std
import logging

# local
from .base_property import WriteableProperty
from jsonapi.core.errors import Forbidden

__all__ = [
    "Meta"
]


LOG = logging.getLogger(__file__)


# We only need the ID of this list.
NotSet = list()


class Meta(WriteableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-attributes

    This descriptor can be used to mark a member of the JSONAPI meta
    object on a resource level.

    :arg value:
        If given, this value is returned per default by the getter.
    :arg callable fget:
        ``fget(schema, resource, request)``
    :arg callable fset:
        ``fset(schema, resource, new_value, request)``
    """

    def __init__(
        self, value=NotSet, *, fget=None, fset=None, name="", doc="",
        writable=False
        ):
        super().__init__(
            fget=fget, fset=fset, name=name, doc=doc, writable=writable
        )

        #: A static value (must be JSON serializable), which is returned per
        #: default.
        self.value = value
        return None

    def default_get(self, schema, resource, request):
        if self.value is not NotSet:
            return self.value
        else:
            return getattr(resource, self.key)

    def default_set(self, schema, resource, new_value, request):
        if not self.writable:
            raise Forbidden(
                details="The meta value '{}.{}' is not writable."\
                    .format(schema.typename, self.name)
            )
        if self.fget:
            LOG.warning(
                "The meta '%s.%s' has a *getter*, but no *setter*. "\
                "You should either define a *setter* or mark it as not "\
                "*writable*.", schema.typename, self.name
            )
        setattr(resource, self.key, new_value)
        return None
