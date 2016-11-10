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
jsonapi.schema.schema
=====================
"""

# std
import logging

# local
from .descriptors import (
    Attribute, ID, Link, Meta, ToOneRelationship, ToManyRelationship
)
from jsonapi.core import errors
from jsonapi.core import utilities


LOG = logging.getLogger(__file__)


class Schema(object):
    """
    Defines the base class for a JSON API schema.

    You must or should override these methods to save the changes in the
    database:

    *   :meth:`create_resource`
    *   :meth:`update_resource`
    *   :meth:`delete_resource`
    *   :meth:`update_relationship`
    *   :meth:`add_relationship`
    *   :meth:`delete_relationship`
    *   :meth:`get_collection`
    *   :meth:`get_resources`

    Everything else (the fields) can be implemented using the descriptors:

    *   :class:`~jsonapi.schema.descriptors.id.ID`
    *   :class:`~jsonapi.schema.descriptors.attribute.Attribute`
    *   :class:`~jsonapi.schema.descriptors.to_one_relationship.ToOneRelationship`
    *   :class:`~jsonapi.schema.descriptors.to_many_relationship.ToManyRelationship`
    *   :class:`~jsonapi.schema.descriptors.meta.Meta`
    *   :class:`~jsonapi.schema.descriptors.link.Link`
    """

    #: The resource class, which is associated with this schema.
    resource_class = None

    #: The typename of the resource class in the JSON API. If not given, we will
    #: use the name of the :attr:`resource_class`.
    typename = None

    def __init__(self):
        """
        """
        #: The :class:`~jsonapi.core.api.API`, which owns this schema.
        self.api = None

        self.id = getattr(self, "id", None)
        self.attributes = dict()
        self.relationships = dict()
        self.meta = dict()
        self.links = dict()
        self._find_descriptors()
        return None

    def init_api(self, api):
        """
        Called, when the *Schema* is added to an API.

        :seealso: :meth:`~jsonapi.core.api.API.add_schema`
        """
        assert self.api is None or self.api is api

        self.api = api
        return None

    def add_descriptor(self, key, prop):
        """
        Adds a descriptor to the schema.

        :arg str key:
            The name of the class variable pointing to the descriptor
        :arg ReadableProperty prop:
            The descriptor
        """
        prop.name = prop.name or key
        prop.key = key

        if isinstance(prop, Attribute):
            self.attributes[prop.name] = prop
        elif isinstance(prop, (ToOneRelationship, ToManyRelationship)):
            self.relationships[prop.name] = prop
        elif isinstance(prop, Link):
            self.links[prop.name] = prop
        elif isinstance(prop, Meta):
            self.meta[prop.name] = prop
        elif isinstance(prop, ID):
            self.id = prop
        return None

    def _find_descriptors(self):
        """
        """
        types = (
            Attribute, ToOneRelationship, ToManyRelationship, Link, Meta, ID
        )

        cls = type(self)
        for key in dir(cls):
            prop = getattr(cls, key)
            if not isinstance(prop, types):
                continue
            self.add_descriptor(key, prop)
        return None

    def create_resource(self, data, *, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-objects
            * http://jsonapi.org/format/#crud-creating

        ``POST /api/Article/``

        Creates a new resource using the JSON API resource object *data*.

        The default implementation passes all attributes and relatives
        mentioned in the JSON API resource object *data* to the constructor
        of the :attr:`resource_class` and returns the new resource instance.
        If *data* contains an *id*, it is also passed to the constructor.

        You **should override** this method.

        :arg dict data:
            A JSON API resource object
        :arg ~jsonapi.core.request.Request request:
            The current request
        :returns:
            The new resource
        """
        # Get all attributes, for which a descriptor exists.
        attributes = data.get("attributes", dict())
        attributes = {
            k: v for k, v in attributes.items() if k in self.attributes
        }

        # Get all relationships, for which a descriptor exists.
        relationships = data.get("relationships", dict())
        relationships = {
            k: v for k, v in relationships.items() if k in self.relationships
        }

        # Load the relatives.
        relatives = utilities.load_relationships_object(
            relationships, request=request
        )

        # Pass the relatives and the attributes to the constructor.
        init_args = dict()
        init_args.update(attributes)
        init_args.update(relatives)
        if data.get("id"):
            init_args["id"] = data["id"]

        resource = self.resource_class(**init_args)
        return resource


    def update_resource(self, resource, data, *, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-objects
            * http://jsonapi.org/format/#crud-updating

        ``PATCH /api/Article/42``

        Updates an existing resource using the JSON API resource object *data*.

        :arg resource:
            The resource **object** or the **id** of the resource object,
            which should be updated.
        :arg ~jsonapi.core.request.Request request:
            The current request
        :arg dict data:
            A JSON API resource object

        :returns:
            The updated resource
        """
        if isinstance(resource, str):
            resource = self.get_resource(resource, request=request)

        if "attributes" in data:
            self._update_attributes(
                resource, data["attributes"], request=request
            )
        if "relationships" in data:
            self._update_relationships(
                resource, data["relationships"], request=request
            )
        return resource

    def _update_attributes(self, resource, data, *, request):
        """
        Updates the resource *resource* with the values in the JSON API
        attributes object *data*.
        """
        for name, value in data.items():
            attr = self.attributes.get(name)
            if attr is None:
                continue
            attr.set(self, resource, value, request)
        return None

    def _update_relationships(self, resource, data, *, request):
        """
        Updates the resource's relationships using the JSON API relationships
        object *data*.
        """
        relatives = utilities.load_relationships_object(data, request=request)

        # Update the relationships using the descriptors.
        for name, value in data.items():
            rel = self.relationships.get(name)
            if rel is None:
                continue
            rel.set(self, resource, value, relatives[name], request)
        return None


    def delete_resource(self, resource, *, request):
        """
        .. seealso::

            http://jsonapi.org/format/#crud-deleting

        **Must be overridden.**

        ``DELETE /api/Article/42``

        Deletes an existing resource.

        :arg resource:
            The **id** of the resource or the **resource** object, which
            should be deleted.
        :arg request:
            The request context
        """
        raise NotImplementedError()


    def get_related(self, relname, resource, *, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#fetching-relationships
            * http://jsonapi.org/format/#fetching-includes
            * http://jsonapi.org/format/#fetching-sorting
            * http://jsonapi.org/format/#fetching-pagination
            * http://jsonapi.org/format/#fetching-filtering

        ``GET /api/Article/42/author``, ``GET /api/Article/42/comments``

        Loads the related resources in the relationship *relname*.

        :arg relname:
            The name of the relationship
        :arg resource:
            The resource **object** or the **id** of the resource, whose
            relative we want to know.
        :arg request:
            The current request

        :rtype:
            A list with all related resources.
        """
        rel = self.relationships.get(relname)
        assert rel is not None

        if isinstance(resource, str):
            resource = self.get_resource(resource, request=request)

        relatives = rel.get(self, resource, request=request)
        if rel.to_one:
            relatives = [relatives] if relatives is not None else []
        return relatives

    def update_relationship(self, relname, resource, data, *, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-object-relationships
            * http://jsonapi.org/format/#crud-updating-relationships

        ``PATCH /api/Article/42/author``

        Updates the relationship with the name *relname*.

        :arg str relname:
            The name of the relationship, which should be updated.
        :arg resource:
            The resource **object** or the **id** of the resource, whose
            relationship should be updated.
        :arg dict data:
            A JSON API relationships object
        :arg request:
            The current request
        """
        rel = self.relationships[relname]

        if isinstance(resource, str):
            resource = self.get_resource(resource, request=request)

        new_relatives = utilities.load_relationship_object(
            data, request=request
        )
        rel.set(self, resource, data, new_relatives, request)
        return resource

    def add_relationship(self, relname, resource, data, *, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-object-relationships
            * http://jsonapi.org/format/#crud-updating-relationships (POST)

        ``POST /api/Article/42/comments``

        Adds new relatives to a *to-many* relationship.

        :arg str relname:
            The name of the relationship, which should be extended.
        :arg resource:
            The resource **object** or the **id** of the resource, whose
            relationship should be extended.
        :arg data:
            A JSON API relationships object with the new relatives
        :arg request:
            The current request
        """
        rel = self.relationships[relname]
        assert rel.to_many

        if isinstance(resource, str):
            resource = self.get_resource(resource, request=request)

        new_relatives = utilities.load_relationship_object(data, request)
        rel.add(self, resource, data, new_relatives, request)
        return resource

    def delete_relationship(self, relname, resource, data, *, request):
        """
        .. seealso::

            http://jsonapi.org/format/#crud-updating-relationships (DELETE)

        ``DELETE /api/Article/42/comments``

        Removes some relatives from a *to-many* relationship.

        :arg str relname:
            The name of the relationship, which should be updated.
        :arg resource:
            The resource **object** or the **id** of the resource, whose
            relationship should be updated.
        :arg dict data:
            A JSON API relationships object, whichs *data* member contains
            the ids of the relatives, which will be removed from this
            relationship.
        :arg request:
            The current request
        """
        rel = self.relationships[relname]
        assert rel.to_many

        if isinstance(resource, str):
            resource = self.get_resource(resource, request=request)

        deleted_relatives = utilities.load_relationship_object(data, request)
        rel.delete(self, resource, data, deleted_relatives, request)
        return resource


    def get_collection(self, *, request):
        """
        .. warning::

            The signature of this function may change in the future.
            It is possible, that the query parameters will be given as
            parameters too and not implicitly by the request.

        .. seealso::

            http://jsonapi.org/format/#fetching-resources

        ``GET /api/Article/``

        Returns a list of resources, which are part of the collection and
        a :class:`pagination <jsonapi.core.pagination.BasePagination>` instance.

        :arg ~jsonapi.core.request.Request request:
            The current request, with all query parameters (include, filter,
            pagination, fields, ...)

        :returns:
            A two tuple: ``(resources, pagination)``
        """
        raise NotImplementedError()

    def get_resources(self, ids, *, request, include=None):
        """
        **This method must be overridden.**

        Returns a dictionary, mapping the resource id tuple to the resource.

        If *include* is specified, the relatives in the include path should
        also be loaded from the database.

        :arg list ids:
            A list of ids (only the id, not a tuple or object). Each id
            must be a string.
        :arg list include:
            A list of include paths
        :arg request:
            The current request

        :rtype: dict
        """
        raise NotImplementedError()

    def get_resource(self, id_, *, request, include=None):
        """
        .. seealso::

            http://jsonapi.org/format/#fetching-resources

        ``GET /api/Article/42``

        The same as :meth:`get_resources`, but for only one resource.

        The default implementation uses :meth:`get_resources` to fetch one
        resource.
        """
        resources = self.get_resources([id_], include=include, request=request)
        assert len(resources) == 1

        resource_id, resource = resources.popitem()
        assert len(resource_id) == 2
        assert resource_id[1] == id_
        return resource
