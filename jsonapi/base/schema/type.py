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
jsonapi.base.schema.type
========================
"""

# std
import logging
from collections import OrderedDict

# local
from .attribute import Attribute
from .id import ID
from .link import Link
from .meta import Meta
from .relationship import RelationshipNotLoaded
from .to_one_relationship import ToOneRelationship
from .to_many_relationship import ToManyRelationship
from .. import errors
from .. import utilities


LOG = logging.getLogger(__file__)


class TypeMeta(type):
    """
    The metaclass for a JSON API :class:`Type`. This meta class
    detects all fields (descriptors) defined on a Type and binds them to
    new Type instances.

    :todo: Support Mixins?
    """

    def __new__(cls_meta, cls_name, cls_bases, cls_attributes):
        """
        Alter the *attributes* dict of a Type class before it is created.
        """
        # We search for the descriptors, put them in a container and add
        # the container as classattribute.
        # The resource class can be None. In this case, the new Type
        # is abstract.
        resource_class = cls_attributes.get("resource_class")

        # Get the typename.
        # 1.) Check if explicitly given on the schema
        # 2.) Use the name of the resource class, if a resource class is given.
        #
        # If no resource class is given, this Type is abstract and therefore,
        # we need no typename.
        typename = cls_attributes.get("typename")
        if (not typename) and resource_class:
            typename = resource_class.__name__

        # Find all descriptors.
        id_ = None             # id descriptor
        fields = dict()        # field name -> descriptor
        attributes = dict()    # attr name  -> descriptor
        relationships = dict() # rel name   -> descriptor
        links = dict()         # link name  -> descriptor
        meta = dict()          # meta name  -> descriptor

        # Don't forget the fields defined on the base classes.
        for base in reversed(cls_bases):
            if not issubclass(base, Type):
                continue

            id_ = base.id or id_
            fields.update(base.fields)
            attributes.update(base.attributes)
            relationships.update(base.relationships)
            links.update(base.links)
            meta.update(base.meta)

        # Find the fields (id, attributes, relationships)
        #
        # If the fields have no name, we set the name to the name of the
        # descriptor, which is defined on the Type.
        for key, prop in cls_attributes.items():
            if isinstance(prop, ID):
                id_ = prop

            elif isinstance(prop, Attribute):
                if not prop.name:
                    prop.name = key
                prop.key = key
                attributes[prop.name] = prop
                fields[prop.name] = prop

            elif isinstance(prop, ToOneRelationship):
                if not prop.name:
                    prop.name = key
                prop.key = key
                relationships[prop.name] = prop
                fields[prop.name] = prop

            elif isinstance(prop, ToManyRelationship):
                if not prop.name:
                    prop.name = key
                prop.key = key
                relationships[prop.name] = prop
                fields[prop.name] = prop

            elif isinstance(prop, Link):
                if not prop.name:
                    prop.name = key
                prop.key = key
                links[prop.name] = prop

            elif isinstance(prop, Meta):
                if not prop.name:
                    prop.name = key
                prop.key = key
                meta[prop.name] = prop

        # Add the new class attributes
        cls_attributes["resource_class"] = resource_class
        cls_attributes["typename"] = typename
        cls_attributes["id"] = id_
        cls_attributes["fields"] = fields
        cls_attributes["attributes"] = attributes
        cls_attributes["relationships"] = relationships
        cls_attributes["links"] = links
        cls_attributes["meta"] = meta
        return super().__new__(cls_meta, cls_name, cls_bases, cls_attributes)

    def __init__(cls, name, bases, attributes):
        """
        The Type class already exists.
        """
        return super().__init__(name, bases, attributes)

    def __call__(cls, *args, **kargs):
        """
        Initialise a new instance of a Type class *cls*. The fields
        (attributes, relationships, id, ...) are bound to the new instance.

        :arg cls: The schema class
        """
        instance = object.__new__(cls)

        # Bind the descriptors to the new instance.
        instance.id = cls.id.bind(instance) if cls.id else None

        instance.attributes = dict()
        for name, attr in cls.attributes.items():
            bound = attr.bind(instance)
            instance.attributes[name] = bound
            setattr(instance, attr.key, bound)

        instance.relationships = dict()
        for name, rel in cls.relationships.items():
            bound = rel.bind(instance)
            instance.relationships[name] = bound
            setattr(instance, rel.key, bound)

        instance.links = dict()
        for name, link in cls.links.items():
            bound = link.bind(instance)
            instance.links[name] = bound
            setattr(instance, link.key, bound)

        instance.meta = dict()
        for name, meta in cls.meta.items():
            bound = meta.bind(instance)
            instance.meta[name] = bound
            setattr(instance, meta.key, bound)

        instance.fields = dict()
        instance.fields.update(instance.attributes)
        instance.fields.update(instance.relationships)

        # Call the constructor.
        instance.__init__(*args, **kargs)
        return instance


class Type(metaclass=TypeMeta):
    """
    Defines the base class for a JSON API type.

    You must or should overridde the following methods:

    *   :meth:`create_resource`
    *   :meth:`update_resource`
    *   :meth:`delete_resource`
    *   :meth:`update_relationship`
    *   :meth:`extend_relationship`
    *   :meth:`clear_relationship`
    *   :meth:`get_collection`
    *   :meth:`get_resources`

    Everything else (the fields) must be implemented using the descriptors:

    *   :class:`~jsonapi.base.schema.id.ID`
    *   :class:`~jsonapi.base.schema.attribute.Attribute`
    *   :class:`~jsonapi.base.schema.to_one_relationship.ToOneRelationship`
    *   :class:`~jsonapi.base.schema.to_many_relationship.ToManyRelationship`
    *   :class:`~jsonapi.base.schema.meta.Meta`
    *   :class:`~jsonapi.base.schema.link.Link`
    """

    def __init__(self):
        self.api = None
        self.uri = None
        return None

    def init_api(self, api, uri):
        """
        Called, when the *Type* instance is registered on an API.

        :seealso: :meth:`~jsonapi.base.api.API.add_type`
        """
        self.api = api
        self.uri = uri
        return None

    # Serialization
    # ~~~~~~~~~~~~~

    def serialize_resource(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-objects

        Creates the JSON API resource object.

        :arg resource:
        :arg ~jsonapi.base.request.Request request:
        """
        d = OrderedDict()
        d.update(self.serialize_id(resource))

        attributes = self.serialize_attributes(resource, request)
        if attributes:
            d["attributes"] = attributes

        relationships = self.serialize_relationships(resource, request)
        if relationships:
            d["relationships"] = relationships

        meta = self.serialize_meta(resource, request)
        if meta:
            d["meta"] = meta

        links = self.serialize_links(resource, request)
        if links:
            d["links"] = links
        return d

    def serialize_id(self, resource):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-identifier-objects

        Creates the JSON API resource identifier object.

        :arg resource:
        """
        d = OrderedDict([
            ("type", self.typename),
            ("id", self.id.get(resource))
        ])
        return d

    def serialize_attributes(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-object-attributes

        Creates the JSON API attributes object.

        :arg resource:
        :arg ~jsonapi.base.request.Request request:
        """
        fields = request.japi_fields.get(self.typename)

        d = OrderedDict()
        for name, attr in self.attributes.items():
            if fields is None or name in fields:
                d[name] = attr.get(resource, request)
        return d

    def serialize_relationships(self, resource, request, *, require_data=None):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-object-relationships

        Creates the JSON API relationships object.

        :arg resource:
        :arg ~jsonapi.base.request.Request request:
        :arg require_data:
            A list with the names of all relationships, for which the resource
            linkage (*data* member) *must* be included.
        """
        fields = request.japi_fields.get(self.typename)

        d = OrderedDict()
        for name in self.relationships:
            if fields is None or name in fields:
                is_required = require_data is not None and name in require_data
                d[name] = self.serialize_relationship(
                    name, resource, require_data=is_required, request=request
                )
        return d

    def serialize_relationship(self, relname, resource, request, *, require_data=False):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-object-relationships

        Creates the JSON API relationship object of the relationship with the
        name *name*.

        :arg str relname:
            The name of the relationship
        :arg resource:
        :arg ~jsonapi.base.request.Request request:
        :arg bool require_data:
            If true, the resource linkage (the related ids) are included.
        """
        rel = self.relationships.get(relname)
        if rel is None:
            raise errors.RelationshipNotFound(self.typename, relname)

        resource_id = self.id.get(resource)
        d = OrderedDict()

        # links
        links = OrderedDict()
        for name, link in rel.links.items():
            links[name] = link(resource, request)
        d["links"] = links
        assert "self" in links or "related" in links

        # meta
        meta = OrderedDict()
        for name, meta_func in rel.meta.items():
            meta[name] = meta_func(resource, request)
        if meta:
            d["meta"] = meta

        # data
        if rel.to_one:
            # *data* can be None, a resource, a resource identifier or
            # RelationshipNotLoaded
            data = rel.get(resource, request, required=require_data)
            assert (not require_data) or (data != RelationshipNotLoaded)
            if data is None:
                d["data"] = None
            elif data != RelationshipNotLoaded:
                d["data"] = self.api.ensure_identifier_object(data)
        else:
            # *data* is either RelationshipNotLoaded, a list of resources
            # or a list of resource identifiers
            data = rel.get(resource, request, required=require_data)
            assert (not require_data) or (data != RelationshipNotLoaded)
            if data != RelationshipNotLoaded:
                d["data"] = [
                    self.api.ensure_identifier_object(item) for item in data
                ]
        return d

    def serialize_links(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-links

        Creates the JSON API links object of the resource *resource*.

        :arg request: The request context
        :arg ~jsonapi.base.request.Request request:
        """
        d = OrderedDict([])
        for name, link in self.links.items():
            d[name] = link.get(resource, request)
        return d

    def serialize_meta(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-meta

        Creates the JSON API meta object of the resource *resource*.

        :arg resource:
        :arg request: The request context
        """
        d = OrderedDict([])
        for name, meta in self.meta.items():
            d[name] = meta.get(resource, request)
        return d

    # Resource Manipulation
    # ~~~~~~~~~~~~~~~~~~~~~

    # All the patching methods are directly associated with a specific
    # API request endpoint and method.

    def create_resource(self, data, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-objects
            * http://jsonapi.org/format/#crud-creating

        ``POST /api/Article/``

        Creates a new resource using the JSON API resource object *data*.

        The default implementation loads all related resources in
        ``data["relationships"]`` and passes them together with
        ``data["attributes"]`` to the constructor of the resource class.
        If ``data["id"]`` is given, the id is also passed to the constructor.

        For security reasons, fields in *data*, which do not exist on this
        schema are filtered out.

        You **should override** this method.

        :arg dict data:
            The JSON API resource object
        :arg ~jsonapi.base.request.Request request:
        :returns:
            The new resource
        """
        if data["type"] != self.typename:
            detail = "The type '{}' is not part of this collection."
            raise errors.Conflict(detail=detail)

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
            relationships, self.api, request
        )

        # Pass the relatives and the attributes to the constructor.
        init_args = dict()
        init_args.update(attributes)
        init_args.update(relatives)
        if data.get("id"):
            init_args["id"] = data["id"]

        resource = self.resource_class(**init_args)
        return resource

    def update_resource(self, resource, data, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-objects
            * http://jsonapi.org/format/#crud-updating

        ``PATCH /api/Article/42``

        Updates an existing resource using the JSON API resource object *data*.

        The default implementation uses the *setter* of all attributes
        and *relationships*.

        :arg resource:
            The resource **object** or the **id** of the resource object,
            which should be updated.
        :arg ~jsonapi.base.request.Request request:
        :arg dict data:
            JSON API resource object

        :returns:
            The updated resource
        """
        # *resource* is an id, but it does not match the id in *data*.
        if isinstance(resource, str) and resource != data["id"]:
            detail = "The 'id' does not match the endpoint."
            raise errors.Conflict(detail=detail)
        if self.typename != data["type"]:
            detail = "The 'type' does not match the endpoint."
            raise errors.Conflict(detail=detail)

        # *resource* is an id, so we have to load the resource object first.
        if isinstance(resource, str):
            if data.get("relationships"):
                include = [[name] for name in data.get("relationships").keys()]
            else:
                include = None
            resource = self.get_resource(resource, include, request)

        assert self.id.get(resource) == data["id"]

        # Update all attributes of the resource using the descriptors.
        if "attributes" in data:
            # We simply ignore attributes that do not exist.
            for name, value in data["attributes"].items():
                attr = self.attributes.get(name)
                if attr is None:
                    continue
                attr.set(resource, value, request)

        # Update all relationships of the resource using the descriptors.
        if "relationships" in data:
            relationships = data["relationships"]

            # Load all resources, for which *autoload* is True.
            relatives = {
                k: v for k, v in relationships.items()\
                if k in self.relationships and self.relationships[k].preload_new_children
            }
            relatives = utilities.load_relationships_object(
                relatives, self.api, request
            )

            # Update the relationships using the descriptors.
            for name, value in relationships.items():
                rel = self.relationships.get(name)
                if rel is None:
                    continue
                new_relatives = relatives.get(name, RelationshipNotLoaded)
                rel.set(resource, value, new_relatives, request)
        return resource

    def delete_resource(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#crud-deleting

        ``DELETE /api/Article/42``

        Deletes an existing resource.

        **Must** be overridden.

        :arg resource:
            The **id** of the resource or the **resource** object, which
            should be deleted.
        :arg request:
            The request context
        """
        raise NotImplementedError()

    def get_related(self, relname, resource, query_params, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#fetching-relationships
            * http://jsonapi.org/format/#fetching-includes
            * http://jsonapi.org/format/#fetching-sorting
            * http://jsonapi.org/format/#fetching-pagination
            * http://jsonapi.org/format/#fetching-filtering

        ``GET /api/Article/42/author``

        ``GET /api/Article/42/comments``

        Loads the related resources in the relationship *relname*.

        The default implementation is basically a wrapper around the
        relationships :meth:`~Relationship.related` function.

        :arg relname:
            The name of the relationship
        :arg resource:
            The resource **object** or the **id** of the resource, whose
            relative we want to know.
        :arg dict query_params:
            A dictionary, containing filters, sort criterions, limit, offset
            and other parameters.
        :arg request:
            The request context

        :rtype:
            A tuple ``(related, total_number)`` with the related resources
            and the total number of related resources in the relationship.
        """
        rel = self.relationships.get(relname)
        assert rel is not None

        if rel.to_one:
            # Get the query parameters.
            include = query_params.get("include")

            # If *resource* is only an id, we need to load the resource object
            # first.
            if isinstance(resource, str):
                rebased_include = utilities.rebase_include(relname, include)
                resource = self.get_resource(resource, rebased_include, request)

            related = rel.related(resource, include, request)
            total_number = 1 if related else 0
        else:
            # If resource is only an id, we have to load the resource object
            # first.
            if isinstance(resource, str):
                include = query_params.get("include")
                filters = query_params.get("filters")
                limit = query_params.get("limit")

                # We rebase the include path only, if the related resources
                # should not be filtered or limited. (In these cases, we
                # could preload more resources than necessairy.)
                if filters or limit:
                    rebased_include = None
                else:
                    rebased_include = utilities.rebase_include(relname, include)

                resource = self.get_resource(resource, rebased_include, request)

            related, total_number = rel.related(resource, query_params, request)
        return (related, total_number)

    def update_relationship(self, relname, resource, data, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-object-relationships
            * http://jsonapi.org/format/#crud-updating-relationships

        ``PATCH /api/Article/42/author``

        Updates the relationship with the name *relname*.

        The default implementation uses the *setter* of the relationship.

        :arg str relname:
            The name of the relationship, which should be updated.
        :arg resource:
            The resource **object** or the **id** of the resource, whose
            relationship should be updated.
        :arg dict data:
            A JSON API relationships object
        :arg request:
            The request context
        """
        rel = self.relationships[relname]

        # If *resource* is only an id, we need to load the resource object
        # first.
        if isinstance(resource, str):
            resource = self.get_resource(resource, None, request)

        if rel.preload_new_children:
            new_relatives = utilities.collect_identifiers(data)
            new_relatives = self.api.get_resources(new_relatives, request)
            new_relatives = list(new_relatives.values())
        else:
            new_relatives = RelationshipNotLoaded

        rel.set(resource, data, new_relatives, request)
        return resource

    def extend_relationship(self, relname, resource, data, request):
        """
        .. seealso::

            * http://jsonapi.org/format/#document-resource-object-relationships
            * http://jsonapi.org/format/#crud-updating-relationships (POST)

        ``POST /api/Article/42/comments``

        Adds new relatives to a *to-many* relationship.

        The default implementation uses the *extend* function of the
        relationship.

        :arg str relname:
            The name of the relationship, which should be extended.
        :arg resource:
            The resource **object** or the **id** of the resource, whose
            relationship should be extended.
        :arg data:
            A JSON API relationships object with the new relatives
        :arg request:
            The request context
        """
        rel = self.relationships[relname]
        assert rel.to_many

        # If *resource* is only an id, we need to load the resource object
        # first.
        if isinstance(resource, str):
            resource = self.get_resource(resource, None, request)

        if rel.preload_new_children:
            new_relatives = utilities.collect_identifiers(data)
            new_relatives = self.api.get_resources(new_relatives, request)
            new_relatives = list(new_relatives.values())
        else:
            new_relatives = RelationshipNotLoaded

        rel.extend(resource, data, new_relatives, request)
        return resource

    def clear_relationship(self, relname, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#crud-updating-relationships (DELETE)

        ``DELETE /api/Article/42/comments``

        Removes all relatives from a *to-many* relationship.

        The default implementation uses the *clear* function of the
        relationship.

        :arg str resource:
            The name of the relationship, which should be updated.
        :arg resource_id:
            The resource **object** or the **id** of the resource, whose
            relationship should be updated.
        :arg request:
            The request context
        """
        rel = self.relationships[relname]
        assert rel.to_many

        # If *resource* is only an id, we need to load the resource object
        # first.
        if isinstance(resource, str):
            resource = self.get_resource(resource, None, request)

        rel.clear(resource, request)
        return resource

    #: Provider
    #: ~~~~~~~~

    def get_collection(self, query_params, request):
        """
        .. seealso::

            http://jsonapi.org/format/#fetching-resources

        ``GET /api/Article/``

        Returns a list of resources, which are part of the collection and
        the total number of resources in the collection.

        The returned resources can be filtered and limited using the
        query parameters in *query_params*::

            # 1.) Only load users, which are older than 20 years
            # 2.) Order them by their age and name
            # 3.) Limit the number of returned resources to 10
            # 4.) Apply an offset of 20
            # 5.) Preload the related comments and articles
            query_params = {
                "filters": [("age", "gt", "20")],
                "order": [("+", "age"), ("-", "name")],
                "limit": 10,
                "offset": 20,
                "include": [["comments"], ["articles"]],
            }
            resources, total_number = user_schema.get_collection(query_params, request)

        This method **must** be overridden.

        :arg dict query_params:
            A dictionary with the query parameters (*filters*, *limit*,
            *offset*, ...)
        :arg ~jsonapi.base.request.Request request:
            The request context

        :returns:
            A two tuple: ``(resources, collection_size)``
        """
        raise NotImplementedError()

    def get_resources(self, ids, include, request):
        """
        Returns a dictionary, mapping the resource id tuple to the resource.

        If *include* is specified, the relatives in the include path should
        also be loaded from the database.

        .. code-block:: python3

            resources = user_schema.get_resources(
                ids=["2", "42", "10"], include=[["articles"]], request=request
            )

        This method **must** be overridden.

        :arg list ids:
            A list of ids (only the id, not a tuple or object). Each id
            must be a string.
        :arg list include:
            A list of include paths
        :arg request:
            The request context

        :rtype: dict
        """
        raise NotImplementedError()

    def get_resource(self, id_, include, request):
        """
        .. seealso::

            http://jsonapi.org/format/#fetching-resources

        ``GET /api/Article/42``

        The same as :meth:`get_resource`, but for only one resource.

        The default implementation uses :meth:`get_resources` to fetch one
        resource.

        This method **should** be overridden.
        """
        resources = self.get_resources([id_], include, request)
        assert len(resources) == 1

        resource_id, resource = resources.popitem()
        assert len(resource_id) == 2
        assert resource_id[1] == id_
        return resource
