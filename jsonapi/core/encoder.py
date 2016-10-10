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
jsonapi.core.encoder
====================

This module contains a simple *Encoder* interface for serializing resources into
a JSON API document.

The encoder comes with reasonable default implementations, which allow you
to define an encoder very **easily** in a few lines of code::

    class ArticleEncoder(Encoder):
        resource_class = Article

        title = attribute()
        author = relationship(to_one=True)

But if you want, you are free to fine-tune the serialization::

    class ArticleEncoder(Encoder):
        resource_class = Article
        typename = "article"

        @attribute()
        def title(self, article, request):
            return article.title

        @relationship(to_one=True):
        def author(self, article, request, *, require_data=False):
            d = dict()
            d["data"] = {"type": "User", "id": str(article.author_id)}
            return d

        @meta()
        def cache_age(self, article, request):
            return "42 minutes"

        @link()
        def image_sprite(self, article, request):
            return "/static/article-images/{}".format(article.id)
"""

# std
import logging


__all__ = [
    "attribute",
    "relationship",
    "link",
    "meta",
    "Encoder",
]


LOG = logging.getLogger(__file__)


def attribute(name=None):
    """
    Marks an :class:`Encoder` method as an attribute.
    """
    def decorator(f):
        f.jsonapi_encoder = {
            "is_attribute": True,
            "name": name or f.__name__
        }
        return f
    return decorator


def relationship(name=None):
    """
    Marks an :class:`Encoder` method as a relationship.
    """
    def decorator(f):
        f.jsonapi_encoder = {
            "is_relationship": True,
            "name": name or f.__name__
        }
        return f
    return decorator

def meta(name=None):
    """
    Marks an :class:`Encoder` method as a meta member.
    """
    def decorator(f):
        f.jsonapi_encoder = {
            "is_meta": True,
            "name": name or f.__name__
        }
        return f
    return decorator


def link(name=None):
    """
    Marks an :class:`Encoder` method as a member of the links object.
    """
    def decorator(f):
        f.jsonapi_encoder = {
            "is_link": True,
            "name": name or f.__name__
        }
        return f
    return decorator


class Encoder(object):
    """
    .. hint::

        You should avoid database interactions in the encoding process for
        performance reasons.

    The base class for a JSON API encoder. The encoder takes a resource
    and creates different JSON API document based on it.

    :arg ~jsonapi.core.api.API api:
        The API, that owns the encoder.
    """

    #: The JSON API *type* (str) of the resource. If not given, we will
    #: use the name of the :attr:`resource_class`.
    typename = ""

    #: The resource class, which is associated with this encoder.
    #: This class will be used in the API to determine the correct encoder for a
    #: given resource.
    resource_class = None

    def __init__(self, api=None):
        """
        """
        self.__api = api

        # Check for a resource class and typename.
        if not self.resource_class:
            LOG.warning(
                "The encoder '%s' is not assigned to a resource class.",
                self.typename or type(self).__name__
            )
        if self.resource_class and not self.typename:
            self.typename = self.resource_class.__name__

        # Detect the fields, links and meta methods.
        self.__attributes = dict()
        self.__relationships = dict()
        self.__meta = dict()
        self.__links = dict()
        self.__detect_methods()
        return None

    def __detect_methods(self):
        """
        Detects methods, that has been marked with

        *   :func:`attribute`,
        *   :func:`relationship`,
        *   :func:`meta`
        *   or :func:`link`

        and adds them to an internal container.
        """
        for prop in dir(self):
            prop = getattr(self, prop)

            if not hasattr(prop, "jsonapi_encoder"):
                continue

            conf = prop.jsonapi_encoder

            if conf.get("is_attribute"):
                self.__attributes[conf["name"]] = prop
            elif conf.get("is_relationship"):
                self.__relationships[conf["name"]] = prop
            elif conf.get("is_link"):
                self.__links[conf["name"]] = prop
            elif conf.get("is_meta"):
                self.__meta[conf["name"]] = prop
        return None

    @property
    def api(self):
        """
        The :class:`~jsonapi.core.api.API`, whichs owns this encoder.
        """
        return self.__api

    def init_api(self, api):
        """
        Called, when the encoder is assigned to an API.

        :arg ~jsonapi.core.api.API api:
            The owning API
        """
        assert self.api is None or self.api is api
        self.api = api
        return None

    def id(self, resource, request):
        """
        **Can be overridden**.

        Returns the id (string) of the resource. The default implementation
        looks for a property ``resource.id`` or an id method ``resource.id()``,
        ``resource.get_id()``.

        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context
        :rtype: str
        :returns:
            The id of the *resource*
        """
        if hasattr(resource, "id"):
            resource_id = resource.id() if callable(resource.id) else resource.id
            resource_id = str(resource_id)
        elif hasattr(resource, "get_id"):
            resource_id = resource.get_id()
            resource_id = str(resource_id)
        else:
            raise Exception("Could not determine the resource id.")
        return resource_id

    def serialize_resource(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-objects

        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context

        :rtype: dict
        :returns:
            The JSON API resource object
        """
        d = dict()
        d.update(self.serialize_id(resource, request))

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

    def serialize_id(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-identifier-objects

        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context

        :rtype: dict
        :returns:
            The JSON API resource identifier object of the *resource*
        """
        return {"type": self.typename, "id": self.id(resource, request)}

    def serialize_attributes(self, resource, request):
        """
        .. seealso::

            *   http://jsonapi.org/format/#document-resource-object-attributes
            *   http://jsonapi.org/format/#fetching-sparse-fieldsets

        Creates the JSON:API attributes object of the given resource, with
        respect to
        :attr:`request.japi_fields <jsonapi.core.request.Request.japi_fields>`.

        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context

        :rtype: dict
        :returns:
            The JSON API attributes object of the *resource*
        """
        fields = request.japi_fields.get(self.typename)

        d = dict()
        for name, attr in self.__attributes.items():
            if fields is None or name in fields:
                d[name] = attr(resource, request)
        return d

    def serialize_relationships(self, resource, request, *, require_data=None):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-object-relationships

        Creates the JSON API relationships object, with respect to
        :attr:`request.japi_fields <jsonapi.core.request.Request.japi_fields>`.

        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context
        :arg list require_data:
            A list with the names of all relationships, for which the resource
            linkage (*data* member) *must* be included.

        :rtype: dict
        :returns:
            The JSON API relationships object of the *resource*.
        """
        fields = request.japi_fields.get(self.typename)

        d = dict()
        for name, rel in self.__relationships.items():
            if fields is None or name in fields:
                d[name] = self.serialize_relationship(
                    name, resource, request,
                    require_data=(not require_data) or (name in require_data)
                )
        return d

    def serialize_relationship(
        self, relname, resource, request, *, require_data=None, pagination=None
        ):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-object-relationships

        Creates the JSON API relationship object of the relationship *relname*.

        :arg str relname:
            The name of the relationship
        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context
        :arg bool require_data:
            If true, the relationship object must contain a *data* member.
        :arg pagination:
            An object describing the pagination of the relationship. The
            pagination is only used for *to-many* relationships.

        :rtype: dict
        :returns:
            The JSON API relationship object for the relationship *relname*
            of the *resource*
        """
        rel = self.__relationships[relname]
        if pagination:
            ret = rel(
                resource, request, require_data=require_data, pagination=pagination
            )
        else:
            ret = rel(resource, request, require_data=require_data)
        return ret

    def serialize_links(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-links

        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context

        :rtype: dict
        :returns:
            The JSON API links object of the *resource*
        """
        d = dict()
        for name, link in self.__links.items():
            d[name] = link(resource, request)
        return d

    def serialize_meta(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-meta

        :arg resource:
            A resource object
        :arg ~jsonapi.core.request.Request request:
            The request context

        :rtype: dict
        :returns:
            A JSON API meta object
        """
        d = dict()
        for name, meta in self.__meta.items():
            d[name] = meta(resource, request)
        return d
