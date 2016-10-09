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
jsonapi.core.utilities
======================

This module contains some helpers, which are frequently needed in different
modules.
"""

# std
import warnings


__all__ = [
    "Symbol",
    "collect_identifiers",
    "rebase_include",
    "load_relationships_object",
    "register_auto_type",
    "auto_type"
]


class Symbol(object):
    """
    A simple symbol implementation.

    .. code-block:: python3

        foo = Symbol()
        assert foo == foo

        bar = Symbol()
        assert bar != foo
    """

    def __init__(self, name=""):
        self.name = name
        return None

    def __eq__(self, other):
        return other is self

    def __ne__(self, other):
        return other is not self


def collect_identifiers(d, with_data=True, with_meta=False):
    """
    Walks through the document *d* and saves all type identifers. This means,
    that each time a dictionary in *d* contains a *type* and *id* key, this
    pair is added to a set and later returned:

    .. code-block:: python3

        >>> d = {
        ...     "author": {
        ...         "data": {"type": "User", "id": "42"}
        ...     }
        ...     "comments": {
        ...         "data": [
        ...             {"type": "Comment", "id": "2"},
        ...             {"type": "Comment", "id": "3"}
        ...         ]
        ...     }
        ... }
        >>> collect_identifiers(d)
        {("User", "42"), ("Comment", "2"), ("Comment", "3")}

    :arg dict d:
    :arg bool with_data:
        If true, we check recursive in all *data* objects for identifiers.
    :arg bool with_meta:
        If true, we check recursive in all *meta* objects for identifiers.

    :rtype: set
    :returns:
        A set with all found identifier tuples.
    """
    ids = set()
    docs = [d]
    while docs:
        d = docs.pop()

        if isinstance(d, list):
            for value in d:
                if isinstance(value, (dict, list)):
                    docs.append(value)

        elif isinstance(d, dict):
            if "id" in d and "type" in d:
                ids.add((d["type"], d["id"]))

            for key, value in d.items():
                if key == "meta" and not with_meta:
                    continue
                if key == "data" and not with_data:
                    continue
                if isinstance(value, (dict, list)):
                    docs.append(value)
    return ids


def rebase_include(new_root, include):
    """
    Adds *new_root* to each include path in *include*.

    .. code-block:: python3

        >>> rebase_include("articles", [["comments"], ["posts"]])
        [["articles", "comments"], ["articles", "posts"]]
        >>> rebase_include("articles", [])
        [["articles"]]

    :arg str new_root:
        The new root of all include paths in include.
    :arg list include:
        A list of include paths.

    :rtype: list
    :returns:
        The new list of include paths.
    """
    if not include:
        rebased = [[new_root]]
    else:
        rebased = [[new_root] + path for path in include]
    return rebased


def load_relationships_object(d, api, request):
    """
    Loads the relatives in a relationships object and returns a dictionary,
    which maps the relationship names to the related resources.

    :arg dict d:
        A JSON API relationships object
    :arg ~jsonapi.core.api.API api:
        An API, which knows all types mentioned in *d*.

    :rtype: dict
    :returns:
        A dictionary, mapping the relationship names in *d* to the actual
        resources in the *data* dictionary of the relationship.

    :seealso: http://jsonapi.org/format/#document-resource-object-relationships
    """
    ids = collect_identifiers(d, with_data=True, with_meta=False)
    resources = api.get_resources(ids, request)

    # Map the relationship names to the resources.
    relationships = dict()
    for name, value in d.items():
        # no data object
        if "data" not in value:
            pass
        # to-one relationship (NULL)
        elif value["data"] is None:
            relationships[name] = None
        # to-one relationship (NOT NULL)
        elif isinstance(value["data"], dict):
            resource_id = (value["data"]["type"], value["data"]["id"])
            relationships[name] = resources[resource_id]
        # to-many relationship
        else:
            assert isinstance(value["data"], list)
            relationships[name] = [
                resources[(item["type"], item["id"])]\
                for item in value["data"]
            ]
    return relationships


# The type factory
__auto_type_factories = []

def register_auto_type(func):
    """
    Registers a new *auto_type()* function. This function receives a *model*
    and must either return a new :class:`~jsonapi.core.schema.type.Type`
    *class* (not an instance!), a list of *Type* classes or *None*.

    This function can be used as decorator::

        @register_auto_type
        def neo_auto_type(model):
            # ...
            return Type

    :arg callable func:
    """
    global __auto_type_factories
    __auto_type_factories.append(func)
    return func


def auto_type(model, api=None):
    """
    A type factory for new JSON API types. If possible, we will create
    a JSON API Type based on the model automatic. If an API is given,
    we will also register the new Type.

    :arg model:
    :arg ~jsonapi.core.api.API api:
    :rtype: ~jsonapi.core.schema.Type
    """
    warnings.warn(
        "The *auto_type()* feature is still experimental. Use with care.",
        FutureWarning
    )

    global __auto_type_factories

    Types = None
    for func in __auto_type_factories:
        Types = func(model)
        if Types:
            break

    if Types is not None and api:
        if isinstance(Types, list):
            for Type in Types:
                api.add_type(Type())
        else:
            api.add_type(Types())
    return Types
