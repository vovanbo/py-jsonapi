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
jsonapi.schema.descriptors.relationship
=======================================
"""

# local
from .base_property import WriteableProperty
from jsonapi.core.errors import ReadOnlyField


__all__ = [
    "Relationship"
]


class Relationship(WriteableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-linkage

    This is the base for the
    :class:`~jsonapi.schema.descriptors.to_one_relationship.ToOneRelationship`
    and
    :class:`~jsonapi.schema.descriptors.to_many_relationship.ToManyRelationship`
    descriptors.

    :arg list remote_types:
        A list of JSON API typenames of the related resources.
    """

    #: True, if this is a :class:`ToOneRelationship`
    to_one = None

    #: True, if this a :class:`ToManyRelationship`
    to_many = None

    def __init__(
        self, remote_types=None, *, fget=None, fset=None, name="", doc="",
        writable=False
        ):
        super().__init__(
            fget=fget, fset=fset, name=name, doc=doc, writable=writable
        )

        #: A list with the names of all remote types.
        self.remote_types = remote_types
        return None
