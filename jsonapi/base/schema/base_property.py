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
jsonapi.base.schema.base_property
=================================
"""

# std
from types import MethodType


__all__ = [
    "ReadableProperty",
    "BoundReadableProperty",
    "WriteableProperty",
    "BoundWriteableProperty"
]


class ReadableProperty(object):
    """
    Defines a descriptor for a property, which can only be read.
    """

    def __init__(self, *, fget=None, name="", doc=""):
        self.fget = None
        self.name = name
        self.__doc__ = doc

        #: The name of the class attribute, which points to the property::
        #:
        #:    foo = ReadableProperty(fget=lambda self: None, name="bar")
        #:    assert foo.name == "bar"
        #:    assert foo.key == "foo"
        #:
        #: If no *name* is explicitly given, then *key* and *name* are the same.
        self.key = None

        if fget:
            self.getter(fget)
        return None

    def bind(self, type_):
        """
        Creates a version of this property, which is bound to the *Type*
        *type_*.

        **Must** be overridden in subclasses.

        :arg Type type_:
        """
        raise NotImplementedError()

    def getter(self, fget):
        """
        Descriptor for the :attr:`fget` method.
        """
        self.fget = fget
        if not self.name:
            self.name = fget.__name__
        if not self.__doc__:
            self.__doc__ = fget.__doc__
        return self

    def __call__(self, fget):
        """
        The same as :meth:`getter`.
        """
        return self.getter(fget)


class BoundReadableProperty(object):
    """
    A readable property, but bound to a Type.
    """

    def __init__(self, prop, type_):
        self.prop = prop
        self.type = type_

        self.name = prop.name
        self.key = prop.key

        # Bind the getter
        self.get = MethodType(self.prop.fget, self.type)\
            if self.prop.fget else self.default_get
        return None

    def default_get(self, *args, **kargs):
        """
        Called, if no *getter* has been defined.

        The default implementation raises a :exc:`NotImplementedError`.
        """
        raise NotImplementedError()


class WriteableProperty(ReadableProperty):
    """
    The same as :class:`ReadableProperty`, but allows to define a *setter*
    to change the value of the property.

    :seealso: http://jsonapi.org/format/#document-resource-object-fields
    """

    def __init__(self, *, fget=None, fset=None, name="", doc=""):
        super().__init__(fget=fget, name=name, doc=doc)

        self.fset = None
        if fset:
            self.setter(fset)
        return None

    def setter(self, fset):
        """
        Descriptor for the :attr:`fset` method.
        """
        self.fset = fset
        return self


class BoundWriteableProperty(BoundReadableProperty):
    """
    A writeable property, but bound to a specific Type instance.
    """

    def __init__(self, prop, type_):
        super().__init__(prop=prop, type_=type_)

        # Bind the setter
        self.set = MethodType(self.prop.fset, self.type)\
            if self.prop.fset else self.default_set
        return None

    def default_set(self, *args, **kargs):
        """
        Called, if no *setter* has been defined.

        The default implementation raises :exc:`NotImplementedError`.
        """
        raise NotImplementedError()
