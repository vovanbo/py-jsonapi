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
jsonapi.schema.meta
========================
"""

# local
from .base_property import ReadableProperty, BoundReadableProperty


__all__ = [
    "Meta",
    "BoundMeta"
]


class Meta(ReadableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-attributes

    This descriptor can be used to mark a member of the JSONAPI meta
    object on a resource level.

    **fget**

    The *fget* method receives a *resource* object and the current
    *request context* as arguments::

        class Article(Type):

            @Meta()
            def foo(self, resource, request):
                return {"bar": [1, 2, 3, 4]}

    **value**

    If you don't have to compute the value, you can simply pass it to
    the constructor::

        class Article(Type):

            foo = Meta({"bar": [1, 2, 3, 4]})

    :arg value:
    """

    def __init__(self, value=None, *, fget=None, name="", doc=""):
        super().__init__(fget=fget, name=name, doc=doc)

        #:
        self.value = value
        return None

    def bind(self, type_):
        return BoundMeta(self, type_)


class BoundMeta(BoundReadableProperty):
    """
    An Meta descriptor, bounded to a specific Type instance.
    """

    def __init__(self, meta, type_):
        super().__init__(meta, type_)
        self.value = value
        return None

    def default_get(self, resource, request):
        """
        Returns the :attr:`Meta.value`.
        """
        return self.value
