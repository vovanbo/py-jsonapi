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
jsonapi.schema.includer
=======================
"""

# std
import logging

# local
from jsonapi.core import includer


__all__ = [
    "Includer"
]


LOG = logging.getLogger(__file__)


class Includer(includer.Includer):
    """
    Implements an includer using only a schema.
    """

    def __init__(self, schema, api=None):
        super().__init__(api=api)

        #: The schema, which is used to resolve the relationships.
        self.schema = schema

        # Convert the relationship descriptors of the schema to
        # includer methods.
        for rel in filter(lambda rel: rel.to_one, schema.relationships):
            self.add_includer_method(includer.ToOneRelationship(
                name=rel.name,
                remote_types=rel.remote_types,
                fget=lambda self, res, req: rel.get(schema, res, req)
            ))
        for rel in filter(lambda rel: rel.to_many, schema.relationships):
            self.add_includer_method(includer.ToManyRelationship(
                name=rel.name,
                remote_types=rel.remote_types,
                fget=lambda self, res, req: rel.get(schema, res, req)
            ))
        return None

    def fetch_resources(self, ids, request):
        """
        .. hint::

            This method may return a **coroutine**, if the underlying
            schema is asynchronous.

        Forwards the call directly to :meth:`Schema.get_resources`.
        """
        return self.schema.get_resources(ids, request=request)
