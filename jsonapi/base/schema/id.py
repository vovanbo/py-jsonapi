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
jsonapi.base.schema.id
======================
"""

# local
from .base_property import WriteableProperty, BoundWriteableProperty
from ..errors import Forbidden


__all__ = [
    "ID",
    "BoundID"
]


class ID(WriteableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-identification

    This descriptor marks the methods on a *Type* used to get and change the
    value of a resource's id. The ID descriptor must be defined at least
    *once* for each type.

    **fget**

    The *fget* method receives a *resource* as argument and returns its *id* as
    *string*::

        class Article(Type):

            id = Id()

            @id.getter
            def id(self, article):
                return str(article.get_id())

    You **must** implement a getter.

    **fset**

    The *fset* method receives a *resource*, the *new id* and the current
    *request context* as arguments::

            @id.setter
            def id(self, article, new_id, request):
                if not request.settings["user"].is_admin:
                    raise Forbidden()
                article.set_id(new_id)
                return None

    Unless you really have to, you should not allow anyone to change the id
    of a resource. The default behaviour for the *setter* is to raise a
    *Forbidden* exception.

    :arg str regex:
        A regular expression, which describes an arbitrary ID string.
    :arg fget:
    :arg fset:
    :arg doc:
    """

    def __init__(self, *, regex=".*", fget=None, fset=None, doc=""):
        super().__init__(fget=fget, fset=fset, doc=doc, name="id")

        # We can use the regex to validate a URL for a resource and
        # a JSON API resource object.
        self.regex = regex
        return None

    def bind(self, type_):
        return BoundID(self, type_)


class BoundID(BoundWriteableProperty):
    """
    An ID bound to a specific Type instance.
    """

    def __init__(self, id_, type_):
        super().__init__(id_, type_)
        self.regex = id_.regex
        return None

    def default_set(self, resource, new_id):
        """
        Called, if no *setter* has been defined.

        The default implementation raises :exc:`Forbidden`.
        """
        detail = "The id of a '{}' is not writeable.".format(self.type.typename)
        raise Forbidden(detail=detail)
