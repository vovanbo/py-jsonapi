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
jsonapi.schema
==============

This module contains a *schema*, which simplifies the implementation of
your API and makes it almost trivial. However, it comes at the cost of
beeing not as flexible as the core.

.. toctree::
    :maxdepth: 2

    descriptors/index
    encoder
    handler
    includer
    schema
    validator
"""

# local
from .descriptors.attribute import Attribute
from .descriptors.id import ID
from .descriptors.link import Link
from .descriptors.meta import Meta
from .descriptors.to_one_relationship import ToOneRelationship
from .descriptors.to_many_relationship import ToManyRelationship

from .schema import Schema


def add_schema(api, schema):
    """
    Adds a :class:`~jsonapi.schema.schema.Schema` to the API. The
    encoder, includer and handlers are created automatic and also added
    to the API.

    :arg ~jsonapi.schema.schema.Schema schema:
        A schema
    """
    from . import handler
    from .includer import Includer
    from .encoder import Encoder

    schema.init_api(api)

    # Create the encoder and includer.
    api.add_type(
        encoder=Encoder(schema), includer=Includer(schema)
    )

    # Create all handlers.
    api.add_handler(
        handler=handler.Collection(api=api, schema=schema),
        typename=schema.typename,
        endpoint_type="collection"
    )
    api.add_handler(
        handler=handler.Resource(api=api, schema=schema),
        typename=schema.typename,
        endpoint_type="resource"
    )
    for rel in filter(lambda rel: rel.to_one, schema.relationships.values()):
        api.add_handler(
            handler=handler.ToOneRelationship(api=api, schema=schema),
            typename=schema.typename,
            endpoint_type="relationship",
            relname=rel.name
        )
        api.add_handler(
            handler=handler.ToOneRelated(api=api, schema=schema),
            typename=schema.typename,
            endpoint_type="related",
            relname=rel.name
        )
    for rel in filter(lambda rel: rel.to_many, schema.relationships.values()):
        api.add_handler(
            handler=handler.ToManyRelationship(api=api, schema=schema),
            typename=schema.typename,
            endpoint_type="relationship",
            relname=rel.name
        )
        api.add_handler(
            handler=handler.ToManyRelated(api=api, schema=schema),
            typename=schema.typename,
            endpoint_type="related",
            relname=rel.name
        )
    return None
