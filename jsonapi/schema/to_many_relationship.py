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
jsonapi.schema.to_many_relationship
========================================
"""

# local
from .relationship import (
    Relationship, BoundRelationship, RelationshipNotLoaded
)
from jsonapi.core.errors import BadRequest


__all__ = [
    "ToManyRelationship",
    "BoundToManyRelationship"
]


class ToManyRelationship(Relationship):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-linkage

    This descriptor can be used to mark the methods for getting and changing
    the value of a *to-many* relationship.

    **fget**

    The *fget* method receives a *resource* object and the current
    *request context* as arguments. It must return a list with the *id tuples*
    or *resource objects* of all related resources.

    If the *required* argument is *False*, the getter may also return
    :data:`RelationshipNotLoaded` to indicate, that the foreign keys are not
    available and a database request is necessairy to get it.

    .. code-block:: python3

        class Article(Type):

            comments = ToManyRelationship("Comment", preload_new_children=True)

            @comments.getter
            def comments(self, article, request, required=False):
                if required:
                    return article.get_comments()
                else:
                    return RelationshipNotLoaded

    You **must** implement a *getter*.

    **frelated**

    The *frelated* method receives a *resource* object, the *query parameters*
    for a collection type endpoint and the current *request* context as
    arguments. It returns a list with the related *resource objects* and the
    *total number* of related resources.

    The *query_params* dictionary contains filters, include and pagination
    parameters. If you ignore them, you must raise a
    :exc:`~jsonapi.core.errors.BadRequest` exception or something similar.

    .. code-block:: python3

            @comments.related
            def comments(self, article, query_params, request):
                if query_params.get("filter"):
                    raise BadRequest()

                offset = query_params.get("offset", 0)
                limit = query_params.get("limit", None)

                start = offset
                end = offset + limit if limit is not None else -1

                comments = article.get_comments()
                return (comments[start:end], len(comments))

    If no *frelated* method is implemented, we use the *getter* and
    *remote schema* to fetch all related resources.

    **fset**

    The *fset* method receives a *resource object*, a JSON API
    *relationships object* with the ids of the new relatives, the
    *new relatives* and the current *request context* as arguments.

    The *new relatives* are only given, if :attr:`preload_new_children` is
    *True* and :data:`RelationshipNotLoaded` otherwise.

    .. code-block:: python3

            @comments.setter
            def comments(self, article, data, new_comments, request):
                if not request.settings["user"].is_admin:
                    raise Forbidden()
                article.set_comments(new_comments)
                return None

    If no *setter* is implemented, the *relationship* is *read-only*.
    If you implemented a *setter*, make sure to also implement *fextend*.

    **fextend**

    The *fextend* method receives a *resource object*, a JSON API
    *relationship object* with the ids of the new relatives, the *new relatives*
    and the current *request context* as arguments.

    The *new relatives* are only given, if :attr:`preload_new_children` is
    *True* and :data:`RelationshipNotLoaded` otherwise.

    This method adds the new relatives to the relationship:

    .. code-block:: python3

            @comments.extender
            def comments(self, article, data, new_comments, request):
                if not request.settings["user"].is_admin:
                    raise Forbidden()
                old_comments = article.get_comments()
                article.set_comments(old_comments + new_comments)
                return None

    If you implemented a *setter*, you **must** implement *fextend*.

    **fremove**

    The *fremove* method receives a *resource object*, a JSON API
    *relationship object* with the ids of the obsolete relatives,
    the *obsolete relatives* and the current *request context* as parameters.

    The *obsolete relatives* are only given, if :attr:`preload_new_children`
    is *True* and :data:`RelationshipNotLoaded` otherwise.

    This method removes the obsolete relatives from the relationship:

    .. code-block:: python3

            @comments.remover
            def comments(self, article, data, removed_comments, request):
                if not request.settings["user"].is_admin:
                    raise Forbidden()
                article.set_comments([])
                return None

    If you implemented a *setter*, you **must** implement *fremove*.
    """

    to_one = False
    to_many = True

    def __init__(
        self, remote_type=None, *, fget=None, fset=None, fextend=None,
        fremove=None, frelated=None, name="", doc="", preload_new_children=True
        ):
        super().__init__(
            remote_type=remote_type, fget=fget, fset=fset, doc=doc, name=name,
            preload_new_children=preload_new_children
        )

        #: Called, when new relatives should be *added* to the relationship.
        self.fextend = None
        if fextend:
            self.extend(fextend)

        #: Called, when some relatives should be *removed* from the relationship.
        self.fremove = None
        if fremove:
            self.remover(fremove)
        return None

    def bind(self, type_):
        return BoundToManyRelationship(self, type_)

    def extend(self, fextend):
        """
        Descriptor for the :attr:`fextend` method.
        """
        self.fextend = fextend
        return self

    def remover(self, fremove):
        """
        Descriptor for the :attr:`fremove` method.
        """
        self.fremove = fremove
        return self


class BoundToManyRelationship(BoundRelationship):
    """
    A ToManyRelationship, but bound to a specific type.
    """

    def __init__(self, rel, type_):
        super().__init__(rel=rel, type_=type_)

        # Bind the extend function
        self.extend = MethodType(self.prop.fextend, self.type)\
            if self.prop.fextend else self.default_extend

        # Bind the remove function
        self.remove = MethodType(self.prop.fremove, self.type)\
            if self.prop.fremove else self.default_remove
        return None

    def default_related(self, resource, query_params, request):
        """
        Called, if no *related* method has been defined.

        The default implementation uses the *getter* and the remote *Type*
        to load the related resources. It does not support sorting or filtering.
        """
        if query_params.get("filter"):
            raise BadRequest(
                detail="The {}.{} collection can not be filtered."\
                    .format(self.type.typename, self.prop.name)
            )
        if query_params.get("order"):
            raise BadRequest(
                detail="The {}.{} collection can not be sorted."\
                    .format(self.type.typename, self.prop.name)
            )

        # Get the ids (or resource instances) of all relatives
        relatives = self.get(resource, request, required=True)
        assert relatives != RelationshipNotLoaded

        # Apply the limit and order.
        offset = query_params.get("offset", 0)

        limit = query_params.get("limit")
        limit = limit + offset if limit is not None else len(relatives)

        total_number = len(relatives)
        relatives = relatives[offset:limit]

        # Load the resources, if we only got a list of identifiers.
        if relatives and isinstance(relatives[0], tuple):
            relatives = self.remote_type.get_resources(
                relatives, query_params.get("include"), request
            )
        return (relatives, total_number)

    def default_extend(self, resource, data, new_relatives, request):
        """
        Called, if no *extend* method has been defined.

        The default implementation raises a :exc:`NotImplementedError` error.
        """
        raise NotImplementedError()

    def default_remove(self, resource, data, removed_relatives, request):
        """
        Called, if no *remove* method has been defined.

        The default implementation raises a :exc:`NotImplementedError` error.
        """
        raise NotImplementedError()
