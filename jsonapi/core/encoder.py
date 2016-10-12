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

        title = Attribute()
        author = ToOneRelationship()

But if you want, you are free to fine-tune the serialization::

    class ArticleEncoder(Encoder):
        resource_class = Article
        typename = "article"

        def id(self, article):
            return str(article.id)

        @Attribute(name="TITLE")
        def title(self, article, request):
            return article.title

        @ToOneRelationship()
        def author(self, article, request, *, require_data=False):
            d = dict()
            d["data"] = {"type": "User", "id": str(article.author_id)}
            return d

        @Meta()
        def cache_age(self, article, request):
            return "42 minutes"

        @Link()
        def image_sprite(self, article, request):
            return "/static/article-images/{}".format(article.id)
"""

# std
import logging
import types


__all__ = [
    "Attribute",
    "ToOneRelationship",
    "ToManyRelationship",
    "Meta",
    "Link",
    "Encoder",
]


LOG = logging.getLogger(__file__)


class EncoderMethod(object):
    """
    A method/attribute, which contains information how an attribute,
    relationship, meta or link should be serialized. An EncoderMethod
    is always defined on a *class*. When it :meth:`bound <bind>`, it is
    associated with a specific encoder (class vs instance).

    :arg str name:
        The name of the encoded object in the JSON API document.
    :arg callable fencode:
        The method, which JSON API encodes a value and returns it.
    """

    def __init__(self, name=None, fencode=None):
        """
        """
        #: The name of the encoded object in the JSON API document.
        #: (The name of the field, link or meta value)
        self.name = name

        #: The method on an Encoder, which is used to get and serialize the
        #: value.
        self.fencode = fencode

        #: The name of the encoder method.
        self.key = None
        return None

    def bind(self, encoder):
        raise NotImplementedError()

    def __call__(self, fencode):
        return self.encoder(fencode)

    def encoder(self, fencode):
        self.fencode = fencode
        self.name = self.name or fencode.__name__
        return self


class BoundEncoderMethod(object):
    """
    The counterpart to :class:`EncoderMethod`. This class is used to bind
    an :class:`EncoderMethod` to a specific encoder *instance*.

    Instances of this class behave like methods defined on an encoder instance.

    :arg EncoderMethod meth:
        The method, which is bound to the *encoder*.
    :arg Encoder encoder:
        The *meth* is bound to this encoder.
    """

    def __init__(self, meth, encoder):
        self.meth = meth
        self.encoder = encoder
        return None

    def __call__(self, *args, **kargs):
        if self.fencode:
            return self.meth.fencode(self.encoder, *args, **kargs)
        else:
            return self.default_encode(*args, **kargs)

    def default_encode(self, *args, **kargs):
        """
        Used as fallback for :attr:`EncoderMethod.fencode`.
        """
        raise NotImplementedError()


# Attributes
# ----------

class Attribute(EncoderMethod):

    def bind(self, encoder):
        return BoundAttribute(self, encoder)


class BoundAttribute(BoundEncoderMethod):

    def default_encode(self, resource, request):
        return getattr(resource, self.key)


# Relationships
# -------------

class ToOneRelationship(EncoderMethod):

    def bind(self, encoder):
        return BoundToOneRelationship(self, encoder)


class BoundToOneRelationship(BoundEncoderMethod):

    def default_encode(self, resource, request, *, require_data=False):
        d = dict()

        d["links"] = dict()
        d["links"]["self"] = self.link_self(resource)
        d["links"]["related"] = self.link_related(resource)

        if require_data:
            related = getattr(resource, self.key)
            related = self.encoder.api.ensure_identifier_object(related)
            d["data"] = related
        return d

    def link_self(self, resource):
        resource_id = self.encoder.id(resource)
        base_uri = self.encoder.api.base_uri
        link_self = base_uri + "/" + resource_id + "/relationships/" + self.name
        return link_self

    def link_related(self, resource):
        resource_id = self.encoder.id(resource)
        base_uri = self.encoder.api.base_uri
        link_related = base_uri + "/" + resource_id + "/" + self.name
        return link_related


class ToManyRelationship(EncoderMethod):

    def bind(self, encoder):
        return BoundToManyRelationship(self, encoder)


class BoundToManyRelationship(BoundEncoderMethod):

    def default_encode(
        self, resource, request, *, require_data=False, pagination=None
        ):
        if pagination:
            raise PaginationNotSupported()

        d = dict()

        d["links"] = dict()
        d["links"]["self"] = self.link_self(resource)
        d["links"]["related"] = self.link_related(resource)

        if require_data:
            related = getattr(resource, self.key)
            related = [
                    self.encoder.api.ensure_identifier_object(resource)\
                    for resource in related
            ]
            d["data"] = related
        return d

    def link_self(self, resource):
        resource_id = self.encoder.id(resource)
        base_uri = self.encoder.api.base_uri
        link_self = base_uri + "/" + resource_id + "/relationships/" + self.name
        return link_self

    def link_related(self, resource):
        resource_id = self.encoder.id(resource)
        base_uri = self.encoder.api.base_uri
        link_related = base_uri + "/" + resource_id + "/" + self.name
        return link_related


# Meta
# ----

class Meta(EncoderMethod):

    def bind(self, encoder):
        return BoundMeta(self, encoder)


class BoundMeta(BoundEncoderMethod):

    def default_encode(self, resource, request):
        return getattr(resource, self.key)


# Link
# ----

class Link(EncoderMethod):

    def bind(self, encoder):
        return BoundLink(self, encoder)


class BoundLink(BoundEncoderMethod):

    def default_encode(self, resource, request):
        return getattr(resource, self.key)


# Encoder
# -------

class Encoder(object):
    """
    .. hint::

        You should avoid database interactions in the encoding process for
        performance reasons. All attributes and relationships, which are going
        to be encoded should have already been loaded.

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
        Detects :class:`EncoderMethod`s and binds them to this instance.
        """
        for key in dir(self):
            prop = getattr(self, key)

            if not isinstance(prop, EncoderMethod):
                continue

            print(key, prop)

            prop.name = prop.name or key
            prop.key = key

            bound = prop.bind(self)
            setattr(self, key, bound)

            if isinstance(prop, Attribute):
                self.__attributes[prop.name] = bound
            elif isinstance(prop, (ToOneRelationship, ToManyRelationship)):
                self.__relationships[prop.name] = bound
            elif isinstance(prop, Meta):
                self.__meta[prop.name] = bound
            elif isinstance(prop, Link):
                self.__links[prop.name] = bound
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
        looks for a property ``resource.id``, an id method ``resource.id()``,
        ``resource.get_id()`` or an key ``resource["id"]``.

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
        elif "id" in resource:
            resource_id = resource["id"]
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

        if isinstance(rel, ToOneRelationship):
            ret = rel(resource, request, require_data=require_data)
        else:
            ret = rel(
                resource, request, require_data=require_data,
                pagination=pagination
            )
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



class ArticleEncoder(Encoder):

    @Attribute()
    def title(self, article, request):
        return article["title"]

enc = ArticleEncoder()
