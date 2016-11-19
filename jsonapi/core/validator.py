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
jsonapi.core.validator
======================

.. seealso::

    *   http://jsonapi.org/format/#document-structure
    *   http://jsonapi.org/format/#errors

Validating a json:api document before accepting it, is part of a good API.
You can use this toolkit for checking the existence of fields, their type
and many other things.

A simple validator for an article could look like this:

.. code-block:: python3

    class ArticleValidator(Validator):
        id = ID(regex="\d+")
        type = Type(types=["Article"])

        title = Attribute(type=str, required=True)
        author = ToOneRelationship(
            types=["User"], require_data=True
        )
        comments = ToManyRelationship(
            types=["Comment", "ImageComment"], require_data=True
        )

Now, you can validate different parts of a JSON API resource object:

.. code-block:: python3

    val = ArticleValidator()

    # OK
    val.assert_resource_object({
        "type": "Article",
        "id": "12",
        "attributes": {
            "title": "Hello"
        }
    })

    # ERROR (the *data* member is required)
    val.assert_relationship_object("author", {
        "meta": {}
    })

    # ERROR (the *title* must be a string)
    val.assert_attributes_object({
        "title": 10
    })


.. _validator_function:

validator function
------------------

A validator function takes a data parameter *d* and a *source_pointer* as
arguments and raises an exception, if the data is invalid:

.. code-block:: python3

    class ArticleValidator(Validator):

        @Attribute(required=True)
        def title(self, d, source_pointer="/"):
            if not isinstance(d, str):
                raise InvalidDocument(source_pointer=source_pointer)
            if d.isspace():
                raise InvalidDocument(source_pointer=source_pointer)
            return None
"""

# std
import logging
import re
import types

# local
from .errors import InvalidDocument
from . import validation


__all__ = [
    "ValidatorMethod",
    "ID",
    "Type",
    "Attribute",
    "Relationship",
    "ToOneRelationship",
    "ToManyRelationship",
    "Meta",
    "Link",
    "Validator"
]


LOG = logging.getLogger(__file__)


class ValidatorMethod(object):
    """
    A special method on a :class:`Validator`, which takes a document *d* and
    validates it.

    :arg str name:
        The name of the field, link, meta, ...
    :arg bool required:
        If true, the field must be included in the JSON API document
    :arg callable validator:
        A function, which validates a given document and raises an exception,
        if it is invalid.
    """

    def __init__(self, name=None, required=False, fvalidate=None):
        """
        """
        #:
        self.name = name

        #: The method name on the Encoder class, on which this validator method
        #: has been defined.
        self.key = None

        #: If true, the field must be included in the JSON API document.
        self.required = required

        #: A function, which validates a JSON API document and raises an
        #: exception, if it is invalid.
        self.fvalidate = None
        if fvalidate:
            self.validator(fvalidate)
        return None

    def __call__(self, fvalidate):
        """
        The same as :meth:`validator`.
        """
        return self.validator(fvalidate)

    def validator(self, fvalidate):
        """
        Descriptor for :attr:`fvalidate`.
        """
        self.name = self.name or fvalidate.__name__
        self.fvalidate = fvalidate
        return self

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return types.MethodType(self.validate, instance)

    def pre_validate(self, validator, d, source_pointer="/"):
        """
        **Can be overridden in subclasses.**

        Validates the document *d*, before the user defined validation method
        :attr:`fvalidate` is called.

        This method should be used, to validate the basic structure of the
        document as it is defined by the JSON API specification.

        :arg Validator validator:
        :arg d:
        :arg str source_pointer:

        :raises ~jsonapi.core.errors.InvalidDocument:
        """
        return None

    def validate(self, validator, d, source_pointer="/"):
        """
        Validates *d* and if *d* is invalid, an
        :exc:`~jsonapi.core.errors.InvalidDocument` exception is raised.

        :arg Validator validator:
        :arg d:
        :arg str source_pointer:

        :raises ~jsonapi.core.errors.InvalidDocument:
        """
        self.pre_validate(validator, d, source_pointer)
        if self.fvalidate:
            self.fvalidate(validator, d, source_pointer)
        return None

# ID
# --

class ID(ValidatorMethod):
    """
    Validates the *id* member in a resource document.

    :arg callable fvalidate:
        A :ref:`validator_function` for the *id*.
    :arg str regex:
        If given, the id must match this regular expression.
    """

    def __init__(self, *, fvalidate=None, regex=None, required=False):
        super().__init__(name="id", required=required, fvalidate=fvalidate)
        self.regex = re.compile(regex) if regex is not None else None
        return None

    def pre_validate(self, validator, d, source_pointer="/"):
        """
        Checks, if *d* is a string and matches the :attr:`regex`.
        """
        if not isinstance(d, str):
            raise InvalidDocument(
                detail="The 'id' must be a string.",
                source_pointer=source_pointer
            )

        if self.regex and not self.regex.fullmatch(d):
            raise InvalidDocument(
                detail="The 'id' is invalid.",
                source_pointer=source_pointer
            )
        return None

# Type
# ----

class Type(ValidatorMethod):
    """
    Validates the *type* of a resource document.

    :arg set types:
        A set with all allowed typenames.
    :arg callable fvalidate:
        A :ref:`validator_function` for the *type*.
    """

    def __init__(self, *, types=None, fvalidate=None):
        super().__init__(name="type", required=True, fvalidate=fvalidate)

        #: The names of all allowed types. If this set is empty, we don't
        #: all values are allowed for the name.
        self.types = set()
        if types:
            self.types.update(types)
        return None

    def pre_validate(self, validator, d, source_pointer="/"):
        """
        Checks if *d* is a string and one of :attr:`types`.
        """
        if not isinstance(d, str):
            raise InvalidDocument(
                detail="The 'type' must be a string.",
                source_pointer=source_pointer
            )

        if self.types and d not in self.types:
            raise InvalidDocument(
                detail="The 'type' must be one of the following types: {}."\
                    .format(", ".join(self.types)),
                source_pointer=source_pointer
            )
        return None

# Attributes
# ----------

class Attribute(ValidatorMethod):
    """
    Validates an attribute member.

    :arg str name:
        The name of the attribute
    :arg type:
        If given, the attribute must be an *instance* of this type.
    :arg bool required:
        If true, the attribute must be included in the attributes object.
    :arg callable fvalidate:
        A :ref:`validator_function` for this attribute
    """

    def __init__(self, *, name=None, type=None, required=False, fvalidate=None):
        super().__init__(name=name, required=required, fvalidate=fvalidate)

        #: The attribute must be an *instance* of this type.
        self.type = type
        return None

    def pre_validate(self, validator, d, source_pointer="/"):
        """
        Checks, if *d* is an instance of :attr:`type`.
        """
        if self.type is not None and not isinstance(d, self.type):
            raise InvalidDocument(
                detail="The attribute '{}' must be of type '{}'."\
                    .format(self.name, self.type.__name__),
                source_pointer=source_pointer
            )
        return None


# Relationships
#---------------

class Relationship(ValidatorMethod):
    """
    Base validator for relationships.

    :seealso: :class:`ToOneRelationship`, :class:`ToManyRelationship`

    :arg str name:
        The name of the relationship
    :arg set types:
        A set with all allowed remote types.
    :arg bool required:
        If true, the relationship must be included in the relationships
        object.
    :arg bool require_data:
        If true, the *data* member of the relationship object is required,
        if the relationship object exists.
    :arg callable fvalidate:
        A :ref:`validator_function` for the *relationship*.
    """

    def __init__(
        self, *, name=None, types=None, required=False, require_data=False,
        fvalidate=None
        ):
        super().__init__(name=name, required=required, fvalidate=fvalidate)

        #: A set with all allowed remote types in the *data* object.
        #: If this set is empty, every typename is allowed.
        self.types = set()
        if types:
            self.types.update(types)

        #: If true, the *data* object is required.
        self.require_data = require_data
        return None

    def pre_validate_resource_identifier_object(self, validator, d, source_pointer):
        """
        Checks, if *d* is a valid resource identifier object and that
        ``d["type"]`` is one of :attr:`types`.
        """
        validation.assert_resource_identifier_object(d, source_pointer)

        if self.types and not d["type"] in self.types:
            raise InvalidDocument(
                detail="The 'type' must be one of: {}"\
                    .format(",".join(self.types)),
                source_pointer=source_pointer + "type/"
            )
        return None

    def pre_validate(self, validator, d, source_pointer):
        """
        Checks, that

        *   *d* is a dictionary
        *   *d* is not empty
        *   *d* has no other keys than *links*, *data* and *meta*
        *   *d* has a *data* member, if :attr:`require_data` is true,
        *   the *links* object (if available) is valid,
        *   the *meta* object (if available) is valid.
        """
        if not isinstance(d, dict):
            raise InvalidDocument(
                detail="A relationship object must be an 'object'.",
                source_pointer=source_pointer
            )
        if not d:
            raise InvalidDocument(
                detail=(
                    "A relationship object must contain at least one of these "
                    "members: 'data', 'links', 'meta'."
                ),
                source_pointer=source_pointer
            )
        if not d.keys() <= {"links", "data", "meta"}:
            raise InvalidDocument(
                detail=(
                    "A relationship object may only contain the following "
                    "members: 'links', 'data' and 'meta'."
                ),
                source_pointer=source_pointer
            )

        # data
        if self.require_data and not "data" in d:
            raise InvalidDocument(
                detail="The 'data' member is required.",
                source_pointer=source_pointer
            )

        # links
        if "links" in d:
            validation.assert_links_object(d["links"], source_pointer + "links/")

        # meta
        if "meta" in d:
            validation.assert_meta_object(d["meta"], source_pointer + "meta/")
        return None


class ToOneRelationship(Relationship):

    def pre_validate(self, validator, d, source_pointer):
        """
        Checks additionaly to :meth:`Relationship.pre_validate`, that

        *   the *data* member (if set) is *None* or a valid
            *resource identifier object*.
        """
        super().pre_validate(validator, d, source_pointer)

        if "data" in d:
            # *data* is null
            if d["data"] is None:
                pass
            # *data* is a resource identifier object
            elif isinstance(d["data"], dict):
                self.pre_validate_resource_identifier_object(
                    validator, d["data"], source_pointer + "data/"
                )
            # *data* is something invalid.
            else:
                raise InvalidDocument(
                    detail=(
                        "The 'data' member must be 'null' or a resource "
                        "identifier object."
                    ),
                    source_pointer=source_pointer + "data/"
                )
        return None


class ToManyRelationship(Relationship):

    def pre_validate(self, validator, d, source_pointer):
        """
        Checks additionaly to :meth:`Relationship.pre_validate`, that

        *   the *data* member (if set) is a list of
            *resource identifier objects*.
        """
        super().pre_validate(validator, d, source_pointer)

        if "data" in d:
            if isinstance(d["data"], list):
                for i, item in enumerate(d["data"]):
                    self.pre_validate_resource_identifier_object(
                        validator, item, source_pointer + "[{}]/".format(i)
                    )
            else:
                raise InvalidDocument(
                    detail="The 'data' member must be a list.",
                    source_pointer=source_pointer + "data/"
                )
        return None


# Links
# -----

class Link(ValidatorMethod):
    """
    Validates a member of the links object.

    :arg str name:
        The name of the link in the *links object*
    :arg bool assert_string:
        If true, the value of the link must be a *string*.
    :arg bool assert_object:
        If true, the value of the link must be a JSON API link object.
    :arg bool required:
        If true, the relationship must be included in the relationships
        object.
    :arg callable fvalidate:
        A :ref:`validator_function` for the *link*.
    """

    def __init__(
        self, *, name=None, assert_string=False, assert_object=False,
        required=False, fvalidate=None
        ):
        super().__init__(name=name, required=required, fvalidate=fvalidate)

        #: If true, the link value must be a string.
        self.assert_string = assert_string

        #: If true, the link value must be a JSON API link object.
        self.assert_object = assert_object
        return None

    def pre_validate(self, validator, d, source_pointer):
        """
        *   Checks, if *d* is a string or a JSON API link object.
        *   Enforces, that *d* is a string object, if :attr:`assert_string`
            is true.
        *   Enforces, that *d* is a JSON API link object, if
            :attr:`assert_object` is true.
        """
        if self.assert_string and not isinstance(d, str):
            raise InvalidDocument(
                detail="The link must be a string.",
                source_pointer=source_pointer
            )
        if self.assert_object and not isinstance(d, dict):
            raise InvalidDocument(
                detail="The link must be a link object.",
                source_pointer=source_pointer
            )

        validation.assert_link_object(d, source_pointer)
        return None


# Meta
# ----

class Meta(ValidatorMethod):
    """
    Validates a member of the *meta* object.

    :arg str name:
        The name of the *meta* member
    :arg bool required:
        If true, the member must be included in the *meta* object of the
        resource document.
    :arg callable fvalidate:
        A :ref:`validator_function` for this *meta* member.
    """


# Validator
# ---------

class Validator(object):
    """
    A validator can be used to validate a given JSON API document. It checks
    the type of attributes and makes sure all required fields are present.
    """

    #: Generic id validation.
    id = ID(required=False)

    #: Generic type validation.
    type = Type()

    def __init__(self):
        """
        """
        self.strict = True

        # validator methods
        self.__id = None
        self.__attributes = dict()
        self.__relationships = dict()
        self.__links = dict()
        self.__meta = dict()

        self.__detect_validator_methods()
        return None

    def add_validator_method(self, key, method):
        """
        Adds a new validator method to the validator.

        :arg str key:
        :arg ValidatorMethod method:
        """
        assert isinstance(method, ValidatorMethod)

        method.key = key
        method.name = method.name or key

        if isinstance(method, Attribute):
            self.__attributes[method.name] = method
        elif isinstance(method, (ToOneRelationship, ToManyRelationship)):
            self.__relationships[method.name] = method
        elif isinstance(method, Link):
            self.__links[method.name] = method
        elif isinstance(method, Meta):
            self.__meta[method.name] = method
        elif isinstance(method, ID) and key == "id":
            self.__id = method
        return None

    def __detect_validator_methods(self):
        """
        """
        cls = type(self)
        for key in dir(cls):
            prop = getattr(cls, key)
            if not isinstance(prop, ValidatorMethod):
                continue
            self.add_validator_method(key, prop)
        return None

    def assert_one_resource_object(self, d, source_pointer="/"):
        """
        Asserts, that *d* is a top-level JSON API document, which has a
        *data* member pointing to a resource document.

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        if not isinstance(d, dict):
            raise InvalidDocument(
                detail="A JSON API top-level document must be an object.",
                source_pointer=source_pointer
            )
        if not "data" in d:
            raise InvalidDocument(
                detail="The *data* member is required.",
                source_pointer=source_pointer
            )
        self.assert_resource_object(d["data"], source_pointer="/")
        return None

    def assert_resource_object(self, d, source_pointer="/"):
        """
        Asserts, that *d* is a JSON API resource object.

        :seealso: http://jsonapi.org/format/#document-resource-objects

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        if not isinstance(d, dict):
            raise InvalidDocument(
                detail="A resource object must be an object.",
                source_pointer=source_pointer
            )
        if not d.keys() <= {"id", "type", "attributes", "relationships", "links", "meta"}:
            raise InvalidDocument(
                detail=(
                    "A resource object may only contain these members: "\
                    "'id', 'type', 'attributes', 'relationships', 'links', 'meta'."
                ),
                source_pointer=source_pointer
            )

        # type
        if not "type" in d:
            raise InvalidDocument(
                detail="The 'type' member is required.",
                source_pointer=source_pointer
            )
        if "type" in d:
            self.assert_type(d["type"], source_pointer + "type/")

        # id
        if self.__id.required and not "id" in d:
            raise InvalidDocument(
                detail="The 'id' member is required.",
                source_pointer=source_pointer
            )
        if "id" in d:
            self.assert_id(d["id"], source_pointer + "id/")

        # attributes
        if any(attr.required for attr in self.__attributes.values())\
            and not "attributes" in d:
            raise InvalidDocument(
                detail="The 'attributes' object is required.",
                source_pointer=source_pointer
            )
        if "attributes" in d:
            self.assert_attributes_object(
                d["attributes"], source_pointer + "attributes/"
            )

        # relationships
        if any(rel.required for rel in self.__relationships.values())\
            and not "relationships" in d:
            raise InvalidDocument(
                detail="The 'relationships' object is required.",
                source_pointer=source_pointer
            )
        if "relationships" in d:
            self.assert_relationships_object(
                d["relationships"], source_pointer + "relationships/"
            )

        # links
        if any(link.required for link in self.__links.values())\
            and not "links" in d:
            raise InvalidDocument(
                detail="The 'links' object is required.",
                source_pointer=source_pointer
            )
        if "links" in d:
            self.assert_links_object(d["links"], source_pointer + "links/")

        # meta
        if any(meta.required for meta in self.__meta.values())\
            and not "meta" in d:
            raise InvalidDocument(
                detail="The 'meta' object is required.",
                source_pointer=source_pointer
            )
        if "meta" in d:
            self.assert_meta_object(d["meta"], source_pointer + "meta/")
        return None

    def assert_id(self, d, source_pointer="/"):
        """
        Asserts that *d* is a (syntactic) valid *id*.

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        return self.id(d, source_pointer)

    def assert_type(self, d, source_pointer="/"):
        """
        Asserts that *d* is the correct typename.

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        return self.type(d, source_pointer)

    def assert_attributes_object(self, d, source_pointer="/"):
        """
        Asserts, that *d* is a JSON API attributes object.

        :seealso: http://jsonapi.org/format/#document-resource-object-attributes

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        if not isinstance(d, dict):
            raise InvalidDocument(
                detail="An attributes object must be an object.",
                source_pointer=source_pointer
            )

        # Make sure, all required attributes are present and all given
        # attributes are valid.
        for name, validator in self.__attributes.items():
            if validator.required and not name in d:
                raise InvalidDocument(
                    detail="The '{}' attribute is missing.".format(name),
                    source_pointer=source_pointer
                )
            if name in d:
                validator.validate(self, d[name], source_pointer + name + "/")
        return None

    def assert_relationships_object(self, d, source_pointer="/"):
        """
        Asserts, that *d* is a JSON API relationships object.

        :seealso: http://jsonapi.org/format/#document-resource-object-relationships

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        if not isinstance(d, dict):
            raise InvalidDocument(
                detail="A relationships object must be an object.",
                source_pointer=source_pointer
            )

        # Make sure, all required relationships are present.
        for name, validator in self.__relationships.items():
            if validator.required and not name in d:
                raise InvalidDocument(
                    detail="The '{}' relationship is missing.".format(name),
                    source_pointer=source_pointer
                )

        # Make sure, all relationship objects are valid.
        for key, value in d.items():
            self.assert_relationship_object(
                key, value, source_pointer + key + "/"
            )
        return None

    def assert_relationship_object(self, relname, d, source_pointer="/"):
        """
        Asserts, that *d* is a relationship object.

        :seelso: http://jsonapi.org/format/#document-resource-object-relationships

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        validator = self.__relationships.get(relname)
        if self.strict and validator is None:
            raise InvalidDocument(
                detail="The relationship '{}' does not exist.".format(relname),
                source_pointer=source_pointer
            )
        elif validator is None:
            validation.assert_relationship_object(d, source_pointer)
        elif validator is not None:
            validator.validate(self, d, source_pointer)
        return None

    def assert_links_object(self, d, source_pointer="/"):
        """
        Asserts, that *d* is a JSON API links object.

        :seealso: http://jsonapi.org/format/#document-links

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        if not isinstance(d, dict):
            raise InvalidDocument(
                detail="A links object must be an object.",
                source_pointer=source_pointer
            )

        for name, validator in self.__links.items():
            if validator.required and not name in d:
                raise InvalidDocument(
                    detail="The '{}' link is missing.".format(name),
                    source_pointer=source_pointer
                )
            if name in d:
                validator.validate(self, d[name], source_pointer + name + "/")
        return None

    def assert_meta_object(self, d, source_pointer="/"):
        """
        Asserts that *d* is a meta object.

        :seealso: http://jsonapi.org/format/#document-meta

        :arg d:
        :arg str source_pointer:

        :raises InvalidDocument:
        """
        if not isinstance(d, dict):
            raise InvalidDocument(
                detail="A meta object must be an object.",
                source_pointer=source_pointer
            )

        for name, validator in self.__meta.items():
            if validator.required and not name in d:
                raise InvalidDocument(
                    detail="The '{}' meta is missing.".format(name),
                    source_pointer=source_pointer
                )
            if name in d:
                validator.validate(self, d[name], source_pointer + name + "/")
        return None
