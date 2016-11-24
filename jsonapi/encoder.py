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
jsonapi.encoder
===============

This module contains a simple *Encoder* interface for serializing resources into
a JSON API document.

The encoder comes with reasonable default implementations, which allow you
to define an encoder very **easily** in a few lines of code::

    class ArticleEncoder(Encoder):
        resource_class = Article

        title = Attribute()
        author = ToOneRelationship()
        comments = ToManyRelationship()

        @Meta()
        def cache_age(self, article, request):
            return "42 minutes"

        @Link()
        def image_sprite(self, article, request):
            return url_for("static", file="image_sprite/{}".format(article.id))

attributes
----------

.. seealso::

    http://jsonapi.org/format/#document-resource-object-attributes

The easiest way of encoding attributes is this one::

    title = Attribute()

The encoder will loook for an attribute ``article.title`` and add it to the
JSON API *attributes* object.

The JSON API name of the attribute field can be changed with the *name*
parameter::

    title = Attribute(name="TiTlE")

If you need more control about the serialization, you can implement a *getter*
for the attribute::

    @Attribute()
    def title(self, article, request):
        return article.get_title()

relationships
-------------

.. seealso::

    http://jsonapi.org/format/#document-resource-object-relationships

to-one
^^^^^^

Defining relationships is as easy as defining attributes::

    author = ToOneRelationship()

The encoder will now look for an attribute ``article.author``, which must be
``None`` or point to *related resource*. (We need the actual resource object in
this case and not only an identifier!)

And again, you can customize the serialization::

    @ToOneRelationship()
    def author(self, article, request, *, require_data=False):
        d = dict()
        if article.author_id is None:
            d["data"] = None
        else:
            d["data"] = {"type": "User", "id": str(article.author_id)}
        return d

The *related* and *self* links of the relationship are added automatic.

You may have noticed the *require_data* parameter. If this parameter is *False*,
you can omit the *data* object. In this case, you can return the
:attr:`Omit` symbol::

    @ToOneRelationship()
    def author(self, article, request, *, require_data=False):
        return article.load_author() if require_data else Omit

to-many
^^^^^^^

The only difference between a *to-one* and a *to-many* relationship is,
that the *to-many* relationship can be paginated::

    @ToManyRelationship()
    def comments(self, article, request, *, require_data=False, pagination=None):
        if pagination is None:
            pagination = jsonapi.pagination.NumberSize(
                uri=request.api.relationship_uri(article, "comments"),
                number=0,
                size=25,
                total_resources=article.comments.count()
            )

        comments = article.comments\\
            .limit(pagination.limit)\\
            .offset(pagination.offset)
        return (comments, pagination)

If you don't use the pagination feature, you can simply return the list
of comments::

    return comments

links
-----

.. seealso::

    http://jsonapi.org/format/#document-links

Defining links is similar to defining attributes::

    image_sprite = Link()

In this case, the encoder looks for the property ``article.image_sprite`` and
includes it into the resource's *links object*.

You can also compute the link here::

    @Link()
    def image_sprite(self, article, request):
        d = dict()
        d["href"] = url_for(
            "static", filename="image_sprite/{}.png".format(article.id)
        )
        d["meta"] = {
            "foo": "Some meta stuff..."
        }
        return d

meta
----

.. seealso::

    http://jsonapi.org/format/#document-meta

Meta information can be included with the :class:`Meta` descriptor::

    cached_since = Meta()

or::

    @Meta()
    def cache_age(self, article, request):
        return cache.get_age(article)
"""

# std
import logging
import types

# local
from .pagination import BasePagination
from .utilities import Symbol


__all__ = [
    "Omit",
    "EncoderMethod",
    "Attribute",
    "Relationship",
    "ToOneRelationship",
    "ToManyRelationship",
    "Meta",
    "Link",
    "Encoder",
]


LOG = logging.getLogger(__file__)


#: Can be returned from an :class:`EncoderMethod` to indicate, that a field
#: is not available or should not be included in the final resource object.
Omit = Symbol("Omit")


class EncoderMethod(object):
    """
    A method/attribute, which contains information how an attribute,
    relationship, meta or link should be serialized.

    :arg str name:
        The name of the encoded object in the JSON API document.
    :arg str mapped_key:
        The name of the property on the resource class, which is mapped to
        the JSON API field.
    :arg callable fencode:
        The method, which JSON API encodes a value and returns it.
    """

    def __init__(self, name=None, mapped_key=None, fencode=None):
        """
        """
        #: The name of the encoded object in the JSON API document.
        #: (The name of the field, link or meta value)
        self.name = name

        #: The method on an Encoder, which is used to get and serialize the
        #: value.
        self.fencode = None
        if fencode:
            self.encoder(fencode)

        #: The name of this encoder method.
        self.key = None

        #: The key on the resource class, which is mapped to this JSON API
        #: field.
        #: If None, we use the :attr:`key`.
        self.mapped_key = mapped_key
        return None

    def __call__(self, fencode):
        return self.encoder(fencode)

    def encoder(self, fencode):
        """
        Descriptor for :attr:`fencode`.
        """
        self.fencode = fencode
        self.name = self.name or fencode.__name__
        return self

    def __get__(self, encoder, owner):
        if encoder is None:
            return self
        elif self.fencode:
            return types.MethodType(self.fencode, encoder)
        else:
            return types.MethodType(self.default_encode, encoder)

    def default_encode(self, encoder, *args, **kargs):
        raise NotImplementedError()

    def encode(self, encoder, *args, **kargs):
        if self.fencode:
            return self.fencode(encoder, *args, **kargs)
        else:
            return self.default_encode(encoder, *args, **kargs)


# Attributes
# ----------

class Attribute(EncoderMethod):

    def default_encode(self, encoder, resource, request):
        return getattr(resource, self.mapped_key)


# Relationships
# -------------

class Relationship(EncoderMethod):

    def links(self, encoder, resource):
        resource_id = encoder.id(resource)
        base_uri = encoder.api.uri

        d = dict()
        d["self"] = "{}/{}/{}/relationships/{}".format(
            base_uri, encoder.typename, resource_id, self.name
        )
        d["related"] = "{}/{}/{}/{}".format(
            base_uri, encoder.typename, resource_id, self.name
        )
        return d


class ToOneRelationship(Relationship):

    def encode(self, encoder, resource, request, *, require_data=False):
        fencode = self.fencode or self.default_encode
        d = fencode(encoder, resource, request, require_data=require_data)

        # *d* can be None, Omit or a resource. In these cases, we need to
        # wrap it in a JSON API relationship object.
        if d is None:
            d = dict(data=None)
        elif d == Omit:
            d = dict()
        elif not isinstance(d, dict):
            d = dict(data=encoder.api.ensure_identifier_object(d))

        # Add the links.
        d.setdefault("links", dict()).update(self.links(encoder, resource))
        return d

    def default_encode(self, encoder, resource, request, *, require_data=False):
        return getattr(resource, self.mapped_key)


class ToManyRelationship(Relationship):

    def encode(
        self, encoder, resource, request, *, require_data=False, pagination=None
        ):
        fencode = self.fencode or self.default_encode
        d = fencode(
            encoder, resource, request, require_data=require_data,
            pagination=pagination
        )


        # *d* can be a list of resources or Omit. In these cases, we need to
        # wrap it in a JSON API relationship object.
        if d == Omit:
            d = dict()
        elif isinstance(d, tuple) and isinstance(d[1], BasePagination):
            d = dict(
                data=[encoder.api.ensure_identifier_object(item) for item in d],
            )
            d.setdefault("meta", dict()).update(pagination.json_meta())
            d.setdefault("links", dict()).update(pagination.json_links())
        elif not isinstance(d, dict):
            d = dict(
                data=[encoder.api.ensure_identifier_object(item) for item in d]
            )

        # Add the links.
        d.setdefault("links", dict()).update(self.links(encoder, resource))
        return d

    def default_encode(
        self, encoder, resource, request, *, require_data=False, pagination=None
        ):
        return getattr(resource, self.mapped_key)


# Meta
# ----

class Meta(EncoderMethod):

    def default_encode(self, encoder, resource, request):
        return getattr(resource, self.mapped_key)


# Link
# ----

class Link(EncoderMethod):

    def default_encode(self, encoder, resource, request):
        return getattr(resource, self.mapped_key)


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

    :arg ~jsonapi.api.API api:
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

        # Use the name of the resource class as fallback for the typename.
        if self.resource_class and not self.typename:
            self.typename = self.resource_class.__name__

        # Detect the fields, links and meta methods.
        self._attributes = dict()
        self._relationships = dict()
        self._meta = dict()
        self._links = dict()
        self._detect_encoder_methods()
        return None

    def add_encoder_method(self, key, method):
        """
        Adds an :class:`EncoderMethod` to the encoder.

        :arg str key:
            The name of the encoder method (encoder attribute name)
        :arg EncoderMethod:
            A new encoder method
        """
        assert isinstance(method, EncoderMethod)

        method.name = method.name or key
        method.mapped_key = method.mapped_key or key
        method.key = key

        if isinstance(method, Attribute):
            self._attributes[method.name] = method
        elif isinstance(method, (ToOneRelationship, ToManyRelationship)):
            self._relationships[method.name] = method
        elif isinstance(method, Meta):
            self._meta[method.name] = method
        elif isinstance(method, Link):
            self._links[method.name] = method
        return None

    def _detect_encoder_methods(self):
        """
        Detects :class:`EncoderMethod`s and binds them to this instance.
        """
        cls = type(self)
        for key in dir(cls):
            prop = getattr(cls, key)
            if not isinstance(prop, EncoderMethod):
                continue
            self.add_encoder_method(key, prop)
        return None

    def get_field_descriptor(self, field):
        """
        Returns the :class:`EncoderMethod` for the field. If the field has no
        descriptor or does not exist, ``None`` is returned.

        :arg str field:
            The name of an attribute or relationship.
        """
        return self._attributes.get(field) or self._relationships.get(field)

    @property
    def api(self):
        """
        The :class:`~jsonapi.api.API`, whichs owns this encoder.
        """
        return self.__api

    def init_api(self, api):
        """
        Called, when the encoder is added to an API. This method can be called
        at most once.

        :arg ~jsonapi.api.API api:
            The API, which owns this encoder.
        """
        assert self.__api is None or self.__api is api
        self.__api = api
        return None

    def id(self, resource):
        """
        **Can be overridden**.

        Returns the id (string) of the resource. The default implementation
        looks for a property ``resource.id``, an id method ``resource.id()``,
        ``resource.get_id()`` or a key ``resource["id"]``.

        :arg resource:
            A resource object
        :arg ~jsonapi.request.Request request:
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
        :arg ~jsonapi.request.Request request:
            The request context

        :rtype: dict
        :returns:
            The JSON API resource object
        """
        d = dict()
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

        :arg resource:
            A resource object

        :rtype: dict
        :returns:
            The JSON API resource identifier object of the *resource*
        """
        return {"type": self.typename, "id": self.id(resource)}

    def serialize_attributes(self, resource, request):
        """
        .. seealso::

            *   http://jsonapi.org/format/#document-resource-object-attributes
            *   http://jsonapi.org/format/#fetching-sparse-fieldsets

        Creates the JSON API attributes object of the given resource, with
        respect to
        :attr:`request.japi_fields <jsonapi.request.Request.japi_fields>`.

        :arg resource:
            A resource object
        :arg ~jsonapi.request.Request request:
            The request context

        :rtype: dict
        :returns:
            The JSON API attributes object of the *resource*
        """
        fields = request.japi_fields.get(self.typename)

        d = dict()
        for name, attr in self._attributes.items():
            if fields is None or name in fields:
                d[name] = attr.encode(self, resource, request)
        return d

    def serialize_relationships(self, resource, request, *, require_data=None):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-object-relationships

        Creates the JSON API relationships object, with respect to
        :attr:`request.japi_fields <jsonapi.request.Request.japi_fields>`.

        :arg resource:
            A resource object
        :arg ~jsonapi.request.Request request:
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
        for name, rel in self._relationships.items():
            if fields is None or name in fields:
                d[name] = self.serialize_relationship(
                    name, resource, request,
                    require_data=require_data and (name in require_data)
                )
        return d

    def serialize_relationship(
        self, relname, resource, request, *, require_data=False, pagination=None
        ):
        """
        .. seealso::

            http://jsonapi.org/format/#document-resource-object-relationships

        Creates the JSON API relationship object of the relationship *relname*.

        :arg str relname:
            The name of the relationship
        :arg resource:
            A resource object
        :arg ~jsonapi.request.Request request:
            The request context
        :arg bool require_data:
            If true, the relationship object must contain a *data* member.
        :arg ~jsonapi.pagination.BasePagination pagination:
            An object describing the pagination of the relationship. The
            pagination is only used for *to-many* relationships.

        :rtype: dict
        :returns:
            The JSON API relationship object for the relationship *relname*
            of the *resource*
        """
        rel = self._relationships[relname]

        if isinstance(rel, ToOneRelationship):
            ret = rel.encode(self, resource, request, require_data=require_data)
        else:
            ret = rel.encode(
                self, resource, request,
                require_data=require_data, pagination=pagination
            )
        return ret

    def serialize_links(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-links

        :arg resource:
            A resource object
        :arg ~jsonapi.request.Request request:
            The request context

        :rtype: dict
        :returns:
            The JSON API links object of the *resource*
        """
        d = dict()
        d["self"] = self.api.resource_uri(resource)
        for name, link in self._links.items():
            d[name] = link.encode(self, resource, request)
        return d

    def serialize_meta(self, resource, request):
        """
        .. seealso::

            http://jsonapi.org/format/#document-meta

        :arg resource:
            A resource object
        :arg ~jsonapi.request.Request request:
            The request context

        :rtype: dict
        :returns:
            A JSON API meta object
        """
        d = dict()
        for name, meta in self._meta.items():
            d[name] = meta.encode(self, resource, request)
        return d
