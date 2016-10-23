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
        return None

    def id(self, resource):
        return self.schema.id(resource)

    def serialize_attributes(self, resource, request):
        fields = request.japi_fields.get(self.typename)
        d = super().serialize_attributes(resource, request)
        for name, attr in self.schema.attributes.items():
            if fields is None or name in fields:
                d[name] = attr.get(self.schema, resource, request)
        return d

    def serialize_relationship(
        self, relname, resource, request, *, require_data=False,
        pagination=None
        ):
        """
        """
        if relname not in self.schema.relationships:
            return super().serialize_relationship(
                relname, resource, request, require_data=require_data,
                pagination=pagination
            )
        raise Exception("ononsognosg")

    def serialize_links(self, resource, request):
        d = super().serialize_links(resource, request)
        for name, link in self.schema.links.items():
            d[name] = link.get(self.schema, resource, request)
        return d

    def serialize_meta(self, resource, request):
        d = super().serialize_meta(resource, request)
        for name, meta in self.schema.meta.items():
            d[name] = meta.get(self.schema, resource, request)
        return None
