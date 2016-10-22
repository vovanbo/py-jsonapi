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
jsonapi.schema.descriptors.base_property
========================================

These base property classes wrap a *getter* and a *setter* method defined on
a :class:`~jsonapi.schema.schema.Schema`. They are used to get and change
the value of a property, like a JSON API field, link or meta data.
"""

# std
import logging


__all__ = [
    "ReadableProperty",
    "WriteableProperty"
]


LOG = logging.getLogger(__file__)


class ReadableProperty(object):
    """
    Defines a descriptor for a property, which can only be read.
    """

    def __init__(self, *, fget=None, name="", doc=""):
        """
        """
        #: A method defined on a :class:`~jsonapi.schema.schema.Schema`.
        self.fget = None

        #: The name of this property in a JSON API document.
        #: If not explicitly given, we will use the name of :attr:`fget` or
        #: the :attr:`key`.
        self.name = name

        self.__doc__ = doc

        #: The name of the class attribute, which points to the property::
        #:
        #:    foo = ReadableProperty(name="bar")
        #:    assert foo.name == "bar"
        #:    assert foo.key == "foo"
        #:
        #: If no *name* is explicitly given, then *key* and *name* are the same.
        self.key = None

        if fget:
            self.getter(fget)
        return None

    def getter(self, fget):
        """
        Descriptor for the :attr:`fget` method.
        """
        self.fget = fget
        self.name = self.name or fget.__name__
        self.__doc__ = self.__doc__ or fget.__doc__
        return self

    def __call__(self, fget):
        """
        The same as :meth:`getter`.
        """
        return self.getter(fget)

    def default_get(self, schema, *args, **kargs):
        """
        Fallback for :meth:`get`, if no :attr:`fget` has been defined.
        """
        raise NotImplementedError()

    def get(self, schema, *args, **kargs):
        """
        Calls the getter with the given arguments.
        """
        if self.fget:
            return self.fget(schema, *args, **kargs)
        else:
            return self.default_get(schema, *args, **kargs)


class WriteableProperty(ReadableProperty):
    """
    The same as :class:`ReadableProperty`, but allows to define a *setter*
    to change the value of the property.
    """

    def __init__(
        self, *, fget=None, fset=None, name="", doc="", writable=False
        ):
        super().__init__(fget=fget, name=name, doc=doc)

        #: If false, the :meth:`default_set` method should throw an exception,
        #: if the property's value should be changed.
        self.writable = writable

        #: A method defined on a :class:`~jsonapi.schema.schema.Schema`.
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

    def default_set(self, schema, *args, **kargs):
        """
        Fallback for :meth:`set`, if not :attr:`fset` has been defined.
        """
        raise NotImplementedError()

    def set(self, schema, *args, **kargs):
        """
        Calls the setter with the given arguments.
        """
        if self.fset:
            return self.fset(schema, *args, **kargs)
        else:
            return self.default_set(schema, *args, **kargs)
