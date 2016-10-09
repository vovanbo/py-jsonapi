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
jsonapi.schema.link
========================
"""

# local
from .base_property import ReadableProperty, BoundReadableProperty


__all__ = [
    "Link",
    "BoundLink"
]


class Link(ReadableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-attributes

    This descriptor can be used to mark a link on a resource level.

    **fget**

    The *fget* method receives a *resource* object and the current
    *request context* as arguments::

        class Article(Type):

            @Link()
            def image(self, resource, request):
                return get_static_url("Article:Image:" + resource.id)

    :arg str href:
        If given, this URL is returned if no *getter* is defined.
    """

    def __init__(self, href="", *, fget=None, name="", doc=""):
        super().__init__(fget=fget, name=name, doc=doc)

        #:
        self.href = href
        return None

    def bind(self, type_):
        return BoundLink(self, type_)


class BoundLink(BoundReadableProperty):
    """
    An Link bounded to a specific Type instance.
    """

    def __init__(self, link, type_):
        super().__init__(link, type_)
        self.href = link.href
        return None

    def default_get(self, resource):
        """
        Called, if no *getter* has been defined.

        The default implementation returns :attr:`Link.href`, if it is defined
        and raises a :exc:`NotImplementedError` exception otherwise.
        """
        if self.href:
            return self.href
        raise NotImplementedError()
