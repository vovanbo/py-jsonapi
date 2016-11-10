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
jsonapi.schema.encoder
======================
"""

# std
import logging

# local
from jsonapi.core import encoder


__all__ = [
    "Encoder"
]


LOG = logging.getLogger(__file__)


class Encoder(encoder.Encoder):
    """
    Implements an encoder using the descriptors on the *schema*.

    :arg ~jsonapi.schema.schema.Schema schema:
    :arg ~jsonapi.core.api.API api:
    """

    def __init__(self, schema, api=None):
        super().__init__(api=api)

        #: The schema, which is used to get the field values.
        self.schema = schema

        #: The typename from the schema.
        self.typename = schema.typename

        #: The resource class from the schema.
        self.resource_class = schema.resource_class

        # Convert the schema properties to encoder methods.
        for attr in self.schema.attributes.values():
            key = attr.key
            meth = encoder.Attribute(
                name=attr.name,
                fencode=lambda encoder, resource, request: \
                    attr.get(schema, resource, request)
            )
            self.add_encoder_method(key, meth)

        for rel in filter(lambda rel: rel.to_one, schema.relationships.values()):
            key = attr.key
            meth = encoder.ToOneRelationship(
                name=rel.name,
                fencode=lambda encoder, resource, request, *, require_data:\
                    rel.get(schema, resource, request)
            )
            self.add_encoder_method(key, meth)

        for rel in filter(lambda rel: rel.to_many, schema.relationships.values()):
            key = attr.key
            meth = encoder.ToManyRelationship(
                name=rel.name,
                fencode=lambda encoder, resource, request, *, require_data, pagination:\
                    rel.get(schema, resource, request)
            )
            self.add_encoder_method(key, meth)

        for meta in schema.meta.values():
            key = attr.key
            meth = encoder.Meta(
                name=meta.name,
                fencode=lambda encoder, resource, request:\
                    meta.get(schema, resource, request)
            )
            self.add_encoder_method(key, meth)

        for link in schema.links.values():
            key = attr.key
            meth = encoder.Link(
                name=link.name,
                fencode=lambda encoder, resource, request:\
                    link.get(schema, resource, request)
            )
            self.add_encoder_method(key, meth)
        return None

    def id(self, resource):
        return self.schema.id.get(self.schema, resource)
