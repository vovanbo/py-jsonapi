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
jsonapi.schema.descriptors.to_many_relationship
===============================================
"""

# local
from .relationship import Relationship
from jsonapi.core.errors import BadRequest


__all__ = [
    "ToManyRelationship"
]


class ToManyRelationship(Relationship):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-linkage

    This descriptor can be used to mark the methods for getting and changing
    the value of a *to-many* relationship.

    :arg list remote_types:
        A list with the JSON API typenames of the related resources.
    :arg callable fget:
        ``fget(schema, resource, request)`` returning a list with all relatives.
    :arg callable fset:
        ``fset(schema, resource, d, new_relatives, request)``
    :arg callable fadd:
        ``fadd(schema, resource, d, new_relatives, request)``
    :arg callable fdelete:
        ``fadd(schema, resource, d, deleted_relatives, request)``
    :arg str name:
        The JSON API name of the relationship
    :arg str doc:
        The docstring of this property
    :arg bool writable:
        If true, the default setter allows to change the value of the
        relationship.
    """

    to_one = False
    to_many = True

    def __init__(
        self, remote_types=None, *, fget=None, fset=None, fadd=None,
        fdelete=None, name="", doc="", writable=False
        ):
        super().__init__(
            remote_types=remote_types, fget=fget, fset=fset, doc=doc, name=name,
            writable=writable
        )

        #: Called, when new relatives should be *added* to the relationship.
        self.fadd = None
        if fadd:
            self.adder(fadd)

        #: Called, when relatives should be *removed* from the relationship.
        self.fdelete = None
        if fdelete:
            self.deleter(fdelete)
        return None

    def adder(self, fadd):
        """
        Descriptor for the :attr:`fadd` method.
        """
        self.fadd = fadd
        return self

    def deleter(self, fremove):
        """
        Descriptor for the :attr:`fdelete` method.
        """
        self.fdelete = fdelete
        return self

    def default_get(self, schema, resource, request):
        return getattr(resource, self.key)

    def default_set(self, schema, resource, data, new_relatives, request):
        if not self.writable:
            raise ReadOnlyField(schema.typename, self.name)
        if self.fget:
            LOG.warning(
                "The relationship '%s.%s' has a *getter*, but no *setter*. "\
                "You should either define a *setter* or mark it as not "\
                "*writable*.", schema.typename, self.name
            )
        return setattr(resource, self.key, new_relatives)

    def default_add(self, schema, resource, data, new_relatives, request):
        # TODO: ...
        raise NotImplementedError()

    def default_remove(self, schema, resource, data, deleted_relatives, request):
        # TODO: ...
        raise NotImplementedError()
