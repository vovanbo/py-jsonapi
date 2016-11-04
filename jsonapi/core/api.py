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
import enum
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


class EndpointTypes(enum.Enum):
    """
    The different endpoint types known to the API.
    """

    Collection = 0
    Resource = 1
    Relationship = 2
    Related = 3


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

        # typename to encoder, includer, ... and vice versa
        self._encoder = dict()
        self._resource_class_to_encoder = dict()

        self._includer = dict()
        self._resource_class_to_includer = dict()

        # Maps an endpoint name to the handler.
        #
        # ("User", "collection")
        # ("User", "resource")
        # ("User", "related", "posts")
        # ("User", "relationship", "posts")
        #
        # TODO: Note, that the routing and request handling is still open for
        #       discussion.
        self._handler = dict()

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


    def get_encoder(self, o, default=ARG_DEFAULT):
        """
        Returns the :class:`~jsonapi.core.encoder.Encoder` associated with *o*.
        *o* must be either a typename, a resource class or resource object.

        :arg o:
            A typename, resource object or a resource class
        :arg default:
            Returned if no encoder for *o* is found.
        :raises KeyError:
            If no encoder for *o* is found and no *default* value is given.
        :rtype: jsonapi.core.encoder.Encoder:
        """
        encoder = self._encoder.get(o)\
            or self._resource_class_to_encoder.get(o)\
            or self._resource_class_to_encoder.get(type(o))
        if encoder is not None:
            return encoder
        if default is not ARG_DEFAULT:
            return default
        raise KeyError()

    def get_includer(self, o, default=ARG_DEFAULT):
        """
        Returns the :class:`~jsonapi.core.includer.Includer` associated with *o*.
        *o* must be either a typename, a resource class or resource object.

        :arg o:
            A typename, resource object or a resource class
        :arg default:
            Returned if no includer for *o* is found.
        :raises KeyError:
            If no includer for *o* is found and no *default* value is given.
        :rtype: jsonapi.core.includer.Includer:
        """
        includer = self._includer.get(o)\
            or self._resource_class_to_includer.get(o)\
            or self._resource_class_to_includer.get(type(o))
        if includer is not None:
            return includer
        if default is not ARG_DEFAULT:
            return default
        raise KeyError()

    def get_typenames(self):
        """
        :rtype: list
        :returns: A list with all typenames known to the API.
        """
        return list(self._encoder.keys())

    def add_type(self, encoder, includer=None):
        """
        Adds an encoder to the API. This method will call
        :meth:`~jsonapi.core.encoder.Encoder.init_api` to bind the encoder to
        the API.

        :arg ~jsonapi.core.encoder.Encoder encoder:
        :arg ~jsonapi.core.includer.Includer includer:
        """
        resource_class = encoder.resource_class
        typename = encoder.typename

        # Add the encoder to the API.
        encoder.init_api(self)
        self._encoder[typename] = encoder
        if resource_class is not None:
            self._resource_class_to_encoder[resource_class] = encoder

        # Add the includer to the API.
        if includer is not None:
            includer.init_api(self)
            self._includer[typename] = includer
            self._resource_class_to_includer[resource_class] = includer
        return None

    def add_handler(self, handler, typename, endpoint_type, relname=None):
        """
        .. warning::

            The final routing mechanisms and URL patterns are still open for
            discussion.

        Adds a new :class:`~jsonapi.core.handler.Handler` to the API.

        :arg ~jsonapi.core.handler.Handler handler:
            A request handler
        :arg str typename:
        :arg ~jsonapi.core.api.EndpointTypes endpoint_type:
        :arg str relname:
            The name of the relationship, if the *endpoint_type* is
            :attr:`EndpointTypes.relationship` or :attr:`EndpointTypes.Related`.
        """
        if endpoint_type == "collection":
            self._handler[(typename, endpoint_type)] = handler
            handler.init_api(self)
        elif endpoint_type == "resource":
            self._handler[(typename, endpoint_type)] = handler
            handler.init_api(self)
        elif endpoint_type == "relationship":
            assert relname
            self._handler[(typename, endpoint_type, relname)] = handler
            handler.init_api(self)
        elif endpoint_type == "related":
            assert relname
            self._handler[(typename, endpoint_type, relname)] = handler
            handler.init_api(self)
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
            encoder = self.get_encoder(obj)
            return {"typename": encoder.typename, "id": encoder.id(obj)}

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
            encoder = self.get_encoder(obj)
            return (encoder.typename, encoder.id(obj))

    # Handler

    def _get_handler(self, request):
        """
        Returns the handler, which is responsible for the request's endpoint.
        """
        # The regular expressions, which will match the uri path or not.
        escaped_uri = re.escape(self._uri)
        collection_re = escaped_uri\
            + "/(?P<type>[^\/]+?)/?$"
        resource_re = escaped_uri\
            + "/(?P<type>[^\/]+?)/(?P<id>[^\/]+?)/?$"
        relationship_re = escaped_uri\
            + "/(?P<type>[^\/]+?)/(?P<id>[^\/]+?)/relationships/<(?P<relname>[^\/]+?)/?$"
        related_re = escaped_uri\
            + "/(?P<type>[^\/]+?)/(?P<id>[^\/]+?)/<(?P<relname>[^\/]+?)/?$"

        # Collection
        match = re.fullmatch(collection_re, request.parsed_uri.path)
        if match:
            request.japi_uri_arguments.update(match.groupdict())
            spec = (match.group("type"), "collection")
            return self._handler.get(spec)

        # Resource
        match = re.fullmatch(resource_re, request.parsed_uri.path)
        if match:
            request.japi_uri_arguments.update(match.groupdict())
            spec = (match.group("type"), "resource")
            return self._handler.get(spec)

        # Relationship
        match = re.fullmatch(relationship_re, request.parsed_uri.path)
        if match:
            request.japi_uri_arguments.update(match.groupdict())
            spec = (match.group("type"), "relationship", match.group("relname"))
            return self._handler.get(spec)

        # Related
        match = re.fullmatch(related_re, request.parsed_uri.path)
        if match:
            request.japi_uri_arguments.update(match.groupdict())
            spec = (match.group("type"), "related", match.group("relname"))
            return self._handler.get(spec)
        return None

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
            if handler is None:
                LOG.debug("Could not find route.")
                raise errors.NotFound()

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
        encoder = self.get_encoder(resource)
        return self._uri + "/" + encoder.typename

    def resource_uri(self, resource):
        """
        :rtype: str
        :returns: The uri for the resource
        """
        encoder = self.get_encoder(resource)
        return self._uri + "/" + encoder.typename + "/" + encoder.id(resource)

    def relationship_uri(self, resource, relname):
        """
        :rtype: str
        :returns: The uri for the relationship *relname* of the resource
        """
        encoder = self.get_encoder(resource)

        uri = "{base_uri}/{typename}/{resource_id}/relationships/{relname}"
        uri = uri.format(
            base_uri=self._uri, typename=encoder.typename,
            resource_id=encoder.id(resource), relname=relname
        )
        return uri

    def related_uri(self, resource, relname):
        """
        :rtype: str
        :returns:
            The uri for fetching all related resources in the relationship
            *relname* with the resource.
        """
        encoder = self.get_encoder(resource)

        uri = "{base_uri}/{typename}/{resource_id}/{relname}"
        uri = uri.format(
            base_uri=self._uri, typename=encoder.typename,
            resource_id=encoder.id(resource), relname=relname
        )
        return uri

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
        encoder = self.get_encoder(resource)
        return encoder.serialize_resource(resource, request)

    def serialize_many(self, resources, request):
        """
        The same as :meth:`serialize`, but for many resources.

        :rtype: list
        :returns:
            A list with the serialized versions of all *resources*.
        """
        return [self.serialize(resource, request) for resource in resources]
