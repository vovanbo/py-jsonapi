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
jsonapi.base.schema.to_one_relationship
=======================================
"""

# local
from .relationship import Relationship, BoundRelationship, RelationshipNotLoaded


__all__ = [
    "ToOneRelationship",
    "BoundToOneRelationship"
]


class ToOneRelationship(Relationship):
    """
    :seealso: http://jsonapi.org/format/#document-resource-object-linkage

    This descriptor can be used to mark the methods for getting and changing
    the value of a *to-one* relationship.

    **fget**

    The *fget* method receives a *resource* object and the current
    *request context* as arguments. The method must return the *id tuple*
    ``(typename, id)`` of the related resource or the related resource itself.
    If the relationship is *NULL* the getter must return ``None``.

    If the *required* argument is *False*, the getter may also return
    :data:`RelationshipNotLoaded` to indicate, that the foreign key is not
    available and a database request is necessairy to get it.

    .. code-block:: python3

        class Article(Type):

            author = ToOneRelationship("User")

            @author.getter
            def author(self, article, request, required=False):
                return ("User", article.get_author_id())

    You *must* implement a *getter*.

    **fset**

    The *fset* method receives a *resource object*, a JSON API
    *relationships object* with the id of the new relative, the
    *new relative* and the current *request context* as arguments.

    The *new relative* is only given, if :attr:`preload_new_children` is
    *True* and :data:`RelationshipNotLoaded` otherwise.

    .. code-block:: python3

            @author.setter
            def author(self, article, data, new_author, request):
                if not request.settings["user"].is_admin:
                    raise Forbidden()
                if not data["data"]["type"] == "User":
                    raise BadRequest()
                article.set_author_id(data["data"]["id"])
                return None

    If not *setter* is defined, the relationship is *read-only*.

    **frelated**

    The *frelated* method receives a *resource* object, some *include paths*
    and the current *request context* as arguments. It returns the
    *related resource object*.

    If *include paths* are given, the method should try to preload these
    relationships of the related resource to avoid future database requests.

    .. code-block:: python3

            @author.related
            def author(self, article, include, request):
                return article.get_author()

    If no *frelated* function is implemented, we use the *fget* function and
    the *remote schema* to fetch the related resource.
    """

    to_one = True
    to_many = False

    def bind(self, type_):
        return BoundToOneRelationship(self, type_)


class BoundToOneRelationship(BoundRelationship):
    """
    A :class:`ToOneRelationship` bound to a specific Type instance.
    """

    def default_related(self, resource, include, request):
        """
        Called, if no *related* method has been defined.

        The default implementation uses the *getter* and the remote schema to
        load the related resource.
        """
        remote_id = self.get(resource, request, required=True)
        assert remote_id != RelationshipNotLoaded

        # The relationship is NULL
        if remote_id is None:
            remote_resource = None

        # remote_id is an ID tuple
        elif isinstance(remote_id, tuple):
            remote_typename, remote_id = remote_id
            remote_type = self.api.get_type(remote_typename)
            remote_resource = remote_type.get_resource(
                remote_id, include, request
            )

        # remote_id is a resource
        else:
            remote_resource = remote_id
        return remote_resource
