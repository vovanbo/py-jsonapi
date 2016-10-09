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
jsonapi.base.schema.attribute
=============================
"""

# local
from .base_property import WriteableProperty, BoundWriteableProperty
from jsonapi.core.errors import ReadOnlyField


__all__ = [
    "Attribute",
    "BoundAttribute"
]


class Attribute(WriteableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-attributes

    This descriptor can be used to mark methods for getting and changing the
    value of an attribute.

    **fget**

    The *fget* method receives a *resource* object and the current
    *request context* as arguments::

        class Article(Type):

            title = Attribute()

            @title.getter
            def title(self, article, request):
                return article.get_title()

    You **must** implement a getter.

    **fset**

    The *fset* method receives a *resource* object, the *new value* of the
    attribute and the current *request* context as arguments::

            @title.setter
            def title(self, article, new_title, request):
                user = request.settings["user"]
                if not (user.is_admin or user == article.get_author()):
                    raise Forbidden()
                return article.set_title(title)

    If you don't implement a *setter*, the attribute is *read-only* and each
    attempt to change its value will result in a
    :exc:`~jsonapi.base.errors.ReadOnlyField` exception.
    """

    def __init__(self, *, fget=None, fset=None, name="", doc=""):
        super().__init__(fget=fget, fset=fset, name=name, doc=doc)
        return None

    def bind(self, type_):
        return BoundAttribute(self, type_)


class BoundAttribute(BoundWriteableProperty):
    """
    An Attribute bound to a specific Type instance.
    """

    def default_set(self, resource, new_value, request):
        """
        Called, if no *setter* has been defined.

        The default implementation raises :exc:`ReadOnlyField` exception.
        """
        raise ReadOnlyField(self.type.typename, self.prop.name)
