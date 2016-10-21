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
jsonapi.core.api
================

The API knows all supported types and is able to handle a JSON API request.
By overriding the :meth:`API.handle_request` method, it can be easily integrated
in other web frameworks.
"""

# std
from collections import defaultdict
import json
import logging
import re
import urllib.parse

# thid party
try:
    import bson
    import bson.json_util
except ImportError:
    bson = None

# local
from .. import version
from . import errors
from . import handler


__all__ = [
    "API"
]


LOG = logging.getLogger(__file__)


# We only need the id of this list.
ARG_DEFAULT = []


class API(object):
    """
    This class is responsible for the request dispatching. It knows all
    resource classes, schemas and api endpoints.

    :arg str uri:
        The root uri of the whole API.
    :arg bool debug:
        If true, exceptions are not catched and the API is more verbose.
    :arg dict settings:
        A dictionary containing settings, which can be used by extensions.
    """

    def __init__(self, uri, debug=True, settings=None):
        """
        """
        # True, if in debug mode.
        self._debug = debug

        self._uri = uri.rstrip("/")
        self._parsed_uri = urllib.parse.urlparse(self._uri)

        #: A dictionary, which can be used to store configuration values
        #: or data for extensions.
        self.settings = settings or dict()
        assert isinstance(self.settings, dict)

        # typename -> type
        self._types = dict()

        # resource class -> type
        self._resource_class_to_type = dict()

        # Typename to handler
        #
        # TODO: Make the routing more efficient by using the url structure.
        self._routes = list()

        #: The global jsonapi object, which is added to each response.
        #:
        #: You can add meta information to the ``jsonapi_object["meta"]``
        #: dictionary if you want.
        #:
        #: :seealso: http://jsonapi.org/format/#document-jsonapi-object
        self.jsonapi_object = dict()
        self.jsonapi_object["version"] = version.jsonapi_version
        self.jsonapi_object["meta"] = dict()
        self.jsonapi_object["meta"]["py-jsonapi-version"] = version.version
        return None

    @property
    def debug(self):
        """
        When *debug* is *True*, the api is more verbose and exceptions are
        not catched.

        This property *can be overridden* in subclasses to mimic the settings
        of the parent framework.
        """
        return self._debug

    @debug.setter
    def debug(self, debug):
        self.debug = bool(debug)
        return None

    def dump_json(self, obj):
        """
        Serializes the Python object *obj* to a JSON string.

        The default implementation uses Python's :mod:`json` module with some
        features from :mod:`bson` (if it is available).

        You *can* override this method.
        """
        indent = 4 if self.debug else None
        default = bson.json_util.default if bson else None
        sort_keys = self.debug
        return json.dumps(obj, indent=indent, default=default, sort_keys=sort_keys)

    def load_json(self, obj):
        """
        Decodes the JSON string *obj* and returns a corresponding Python object.

        The default implementation uses Python's :mod:`json` module with some
        features from :mod:`bson` (if available).

        You *can* override this method.
        """
        default = bson.json_util.object_hook if bson else None
        return json.loads(obj, object_hook=default)

    def get_type(self, o, default=ARG_DEFAULT):
        """
        Returns the :class:`~jsonapi.core.schema.type.Type` associated with *o*.
        *o* must be either a typename, a resource class or resource object.

        :arg o:
            A typename, resource object or a resource class
        :arg default:
            A fallback value, if the *Type* for *o* can not be determined.
        :raises KeyError:
            If the typename is not associated with a *Type* and no default
            argument is given.
        :rtype: jsonapi.core.schema.type.Type
        """
        type_ = self._types.get(o)\
            or self._resource_class_to_type.get(o)\
            or self._resource_class_to_type.get(type(o))
        if type_ is not None:
            return type_
        if default is not ARG_DEFAULT:
            return default
        raise KeyError()

    def get_typenames(self):
        """
        :rtype: list
        :returns: A list with all typenames known to the API.
        """
        return list(self._types.keys())

    def has_type(self, typename):
        """
        :arg str typename:
        :rtype: bool
        :returns:
            True, if the API has a type with the name *typename* and False
            otherwise.
        """
        return typename in self._types

    def add_type(self, type, **kargs):
        """
        Adds the *type* to the API. This method will call
        :meth:`~jsonapi.core.schema.type.Type.init_api` to bind the *type*
        to the API.

        :type type: ~jsonapi.core.schema.type.Type
        :arg type: A *Type* instance
        """
        # Our default request handler.
        kargs.setdefault("CollectionHandler", handler.CollectionHandler)
        kargs.setdefault("ResourceHandler", handler.ResourceHandler)
        kargs.setdefault("ToOneRelationshipHandler", handler.ToOneRelationshipHandler)
        kargs.setdefault("ToManyRelationshipHandler", handler.ToManyRelationshipHandler)
        kargs.setdefault("ToOneRelatedHandler", handler.ToOneRelatedHandler)
        kargs.setdefault("ToManyRelatedHandler", handler.ToManyRelatedHandler)

        assert type.typename not in self._types

        uri = self.uri + "/" + type.typename
        type.init_api(self, uri)
        self._types[type.typename] = type
        self._resource_class_to_type[type.resource_class] = type

        # Add the routes
        # collection endpoint
        collection_re = re.compile(uri + "/?")
        collection_handler = kargs["CollectionHandler"](self, type)
        self._routes.append((collection_re, collection_handler))

        # resource endpoint
        resource_re = re.compile(uri + "/(?P<id>[A-z0-9]+)/?")
        resource_handler = kargs["ResourceHandler"](self, type)
        self._routes.append((resource_re, resource_handler))

        for relname, rel in type.relationships.items():
            # relationship endpoint
            if rel.to_one:
                relationship_handler = kargs["ToOneRelationshipHandler"](self, type, relname)
            else:
                relationship_handler = kargs["ToManyRelationshipHandler"](self, type, relname)
            relationship_re = re.compile(uri + "/(?P<id>[A-z0-9]+)/relationships/" + relname + "/?")
            self._routes.append((relationship_re, relationship_handler))

            # related endpoint
            if rel.to_one:
                related_handler = kargs["ToOneRelatedHandler"](self, type, relname)
            else:
                related_handler = kargs["ToManyRelatedHandler"](self, type, relname)
            related_re = re.compile(uri + "/(?P<id>[A-z0-9]+)/" + relname + "/?")
            self._routes.append((related_re, related_handler))
        return None

    def get_includer(self, o):
        return None

    def get_encoder(self, o):
        return None

    # Utilities

    def ensure_identifier_object(self, obj):
        """
        Converts *obj* into an identifier object:

        .. code-block:: python3

            {
                "type": "people",
                "id": "42"
            }

        :arg obj:
            A two tuple ``(typename, id)``, a resource object or a resource
            document, which contains the *id* and *type* key
            ``{"type": ..., "id": ...}``.

        :seealso: http://jsonapi.org/format/#document-resource-identifier-objects
        """
        # Identifier tuple
        if isinstance(obj, tuple):
            return {"type": obj[0], "id": obj[1]}
        # JSONapi identifier object
        elif isinstance(obj, dict):
            # The dictionary may contain more keys than only *id* and *type*. So
            # we extract only these two keys.
            return {"type": obj["type"], "id": obj["id"]}
        # obj is a resource
        else:
            type_ = self.get_type(obj)
            return {"typename": type_.typename, "id": type_.id.get(obj)}

    def ensure_identifier(self, obj):
        """
        Does the same as :meth:`ensure_identifier_object`, but returns the two
        tuple identifier object instead of the document:

        .. code-block:: python3

            # (typename, id)
            ("people", "42")

        :arg obj:
            A two tuple ``(typename, id)``, a resource object or a resource
            document, which contains the *id* and *type* key
            ``{"type": ..., "id": ...}``.
        """
        if isinstance(obj, tuple):
            assert len(obj) == 2
            return obj
        elif isinstance(obj, dict):
            return (obj["type"], obj["id"])
        else:
            type_ = self.get_type(obj)
            return (type_.typename, type_.id.get(obj))

    # Handler

    def _get_handler(self, request):
        """
        Returns the handler, which is responsible for the request's endpoint.
        """
        for uri_pattern, handler in self._routes:
            match = uri_pattern.fullmatch(request.parsed_uri.path)
            if match:
                request.japi_uri_arguments.update(match.groupdict())
                return handler
        raise errors.NotFound()

    def prepare_request(self, request):
        """
        Called, before the :meth:`~jsonapi.core.handler.Handler.handle`
        of the request handler is called.

        You *can* overridde this method to modify the request. (Add some
        settings, headers, ...).
        """
        return None

    def handle_request(self, request):
        """
        Handles a request and returns a response object.

        This method should be overridden for integration in other frameworks.
        It is the **entry point** for all requests handled by this library.

        :type request: ~jsonapi.core.request.Request
        :arg request: The request, which should be handled.

        :rtype: ~jsonapi.core.request.Response
        """
        assert request.api is None or request.api is self
        request.api = self

        try:
            self.prepare_request(request)
            handler = self._get_handler(request)
            resp = handler.handle(request)
        except errors.Error as err:
            if self.debug:
                raise
            resp = errors.error_to_response(err, dump_json=self.dump_json)
        return resp

    # URLs

    @property
    def uri(self):
        """
        The root uri of the api, which has been provided in the constructor.
        """
        return self._uri

    def collection_uri(self, resource):
        """
        :rtype: str
        :returns: The uri for the resource's collection
        """
        type_ = self.get_type(resource)
        return type_.uri

    def resource_uri(self, resource):
        """
        :rtype: str
        :returns: The uri for the resource
        """
        type_ = self.get_type(resource)
        resource_id = type_.id.get(resource)
        return type_.uri + "/" + resource_id

    def relationship_uri(self, resource, relname):
        """
        :rtype: str
        :returns: The uri for the relationship *relname* of the resource
        """
        type_ = self.get_type(resource)
        assert relname in type_.relationships
        resource_id = type_.id.get(resource)
        return type_.uri + "/" + resource_id + "/relationships/" + relname

    def related_uri(self, resource, relname):
        """
        :rtype: str
        :returns:
            The uri for fetching all related resources in the relationship
            *relname* with the resource.
        """
        type_ = self.get_type(resource)
        assert relname in type_.relationships
        resource_id = type_.id.get(resource)
        return type_.uri + "/" + resource_id + "/" + relname

    # Resource serializer

    def serialize(self, resource, request):
        """
        Chooses the correct serializer for the *resource* and returns the
        serialized version of the resource.

        :arg resource:
            A resource instance, whichs type is known to the API.
        :arg ~jsonapi.core.request.Request request:
            The current request context

        :rtype: dict
        :returns:
            The serialized version of the *resource*.
        """
        type_ = self.get_type(resource)
        return type_.serialize_resource(resource, request)

    def serialize_many(self, resources, request):
        """
        The same as :meth:`serialize`, but for many resources.

        :rtype: list
        :returns:
            A list with the serialized versions of all *resources*.
        """
        return [self.serialize(resource, request) for resource in resources]

    # Fetching resources

    def get_resources(self, ids, request):
        """
        Fetches the resources with the given ids from the database and returns
        a dictionary, which maps the ids to the actual resource.

        You *can* override this method.

        :arg list ids:
            A list of identifier tuples
        :arg ~jsonapi.core.request.Request:
            The request context

        :rtype: dict
        :returns:
            A dictionary, which maps the ids to the resource object.
        """
        # Group the ids by their typename.
        ids_by_typename = defaultdict(set)
        for typename, id_ in ids:
            ids_by_typename[typename].add(id_)

        # Load the ids.
        all_resources = dict()
        for (typename, ids) in ids_by_typename.items():
            type_ = self._types[typename]
            resources = type_.get_resources(ids, include=None, request=request)
            all_resources.update(resources)
        return all_resources
