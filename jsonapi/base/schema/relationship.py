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
jsonapi.base.schema.relationship
================================
"""

# std
from types import MethodType

# third party
from cached_property import cached_property
import warnings

# local
from .base_property import WriteableProperty, BoundWriteableProperty
from ..errors import ReadOnlyField
from ..utilities import Symbol


__all__ = [
    "RelationshipNotLoaded",
    "Relationship",
    "BoundRelationship"
]


#: Can be returned from the getter of a relationship to indicate, that the
#: foreign keys are currently not available.
RelationshipNotLoaded = Symbol("RelationshipNotLoaded")


class Relationship(WriteableProperty):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-linkage

    This is the base descriptor for marking a *ToOneRelationship* or a
    *ToManyRelationship*.

    It extends the *WriteableProperty* property by allowing to define a
    method for fetching all related resources.

    :arg remote_type:
        The JSON API typename, schema or resource class of the remote side
        of the relationship. This can also be a function, which returns
        one of the mentioned objects.
    :arg bool preload_new_children:
        When the relationship is patched (*set*, *extend*, ...), the new
        relatives are loaded from the database and passed to the setter.
    """

    #: True, if this is a ToOneRelationship
    to_one = None

    #: True, if this a ToManyRelationship
    to_many = None

    def __init__(
        self, remote_type=None, *, fget=None, fset=None, frelated=None, name="",
        doc="", preload_new_children=True
        ):
        super().__init__(fget=fget, fset=fset, name=name, doc=doc)

        #: Returns all related resources. (The *getter* must only return the
        #: ids, so we need this method too.)
        self.frelated = None
        if frelated:
            self.related(frelated)

        # Since remote_type can be a typename, schema or resource class,
        # we make it protected and define the properties remote_schma,
        # remote_typename and remote_class below.
        self._remote_type = remote_type

        #: If true, *py-jsonapi* will load new relatives and pass them to the
        #: setter function.
        #:
        #: :todo: Find a shorter and better name.
        self.preload_new_children = preload_new_children

        #: All link objects.
        #:
        #: A new link can be added with the :meth:`link` decorator.
        self.links = dict()

        #: All member of the relationship *meta* object.
        #:
        #: A new member can be added with the :meth:`meta` decorator.
        self.meta_ = dict()
        return None

    def related(self, frelated):
        """
        Descriptor for the :attr:`frelated` function.
        """
        self.frelated = frelated
        return self

    def link(self, flink):
        """
        Adds a new :class:`Link` to the relationship.
        """
        warnings.warn(
            "The behaviour for adding links to a relationship may change in "\
            "the future.", FutureWarning
        )
        self.links[flink.__name__] = flink
        return flink

    def meta(self, fmeta):
        """
        Adds a member to the *meta* object of the relationship.
        """
        warnings.warn(
            "The behaviour for adding meta information to a relationship may "\
            "change in the future.", FutureWarning
        )
        self.meta_[fmeta.__name__] = fmeta
        return fmeta


class BoundRelationship(BoundWriteableProperty):
    """
    A Relationship bound to a specific Type instance.
    """

    def __init__(self, rel, type_):
        super().__init__(prop=rel, type_=type_)

        #: True, if this is a *to-one* relationship.
        self.to_one = self.prop.to_one

        #: True, if this is a *to-many* relationship.
        self.to_many = self.prop.to_many

        #:
        self.preload_new_children = self.prop.preload_new_children

        # Bind the related function
        self.related = MethodType(self.prop.frelated, self.type)\
            if self.prop.frelated else self.default_related

        # Bind the links and add the links, which are defined by the JSON API
        # specification.
        self.links = {
            name: MethodType(link, self.type)\
            for name, link in self.prop.links.items()
        }
        self.links["self"] = self._link_self
        self.links["related"] = self._link_related

        # Bind the meta members
        self.meta = {
            name: MethodType(meta, self.type)\
            for name, meta in self.prop.meta_.items()
        }
        return None

    def _link_self(self, resource, request):
        """
        The link for the relationship itself. This links allos the client to
        manipulate the relationship directly.

        :seealso: http://jsonapi.org/format/#document-resource-object-relationships
        """

        resource_id = self.type.id.get(resource)
        return self.type.uri + "/" + resource_id + "/relationships/" + self.prop.name

    def _link_related(self, resource, request):
        """
        The link provides access to the resource objects linked in the
        relationship.

        :seealso: http://jsonapi.org/format/#document-resource-object-related-resource-links
        """
        resource_id = self.type.id.get(resource)
        return self.type.uri + "/" + resource_id + "/" + self.prop.name

    @property
    def remote_type(self):
        """
        The :class:`~jsonapi.base.schema.type.Type` of the remote class.
        """
        from .type import Type

        # We allow the *remote_type* on property to be a callable, which returns
        # the remote typename, type or resource class.
        if callable(self.prop._remote_type):
            remote_type = self.prop._remote_type()
        else:
            remote_type = self.prop._remote_type
        return self.type.api.get_type(remote_type, None)

    @property
    def remote_typename(self):
        """
        The JSON API typename of the remote side.
        """
        return self.remote_type.typename if self.remote_type else None

    @property
    def remote_class(self):
        """
        The resource class on the other side of the relationship.
        """
        return self.remote_type.resource_class if self.remote_type else None

    def default_set(self, *args, **kargs):
        """
        Called, if no *setter* has been defined.

        The default implementation raises a :exc:`ReadOnlyField` exception.
        """
        raise ReadOnlyField(self.type.typename, self.prop.name)

    def default_related(self, *args, **kargs):
        """
        Called, if no *related* method has been defined.

        The default implementation raises a :exc:`NotImplementedError`.
        """
        raise NotImplementedError()
