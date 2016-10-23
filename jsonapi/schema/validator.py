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
jsonapi.schema.validator
========================
"""

# std
import logging

# local
from jsonapi.core import validator


__all__ = [
    "Validator"
]


LOG = logging.getLogger(__file__)


class Validator(validator.Validator):
    """
    Implements a validator using only a schema.

    :arg ~jsonapi.schema.schema.Schema:
    """

    def __init__(self, schema):
        super().__init__()

        #: The schema, which is used to resolve the relationships.
        self.schema = schema

        # Convert the relationship descriptors of the schema to
        # includer methods.
        for attr in schema.attributes:
            self.add_validator_method(validator.Attribute(
                name=attr.name
            ))
        for rel in filter(lambda rel: rel.to_one, schema.relationships):
            self.add_validator_method(validator.ToOneRelationship(
                name=rel.name, types=rel.remote_types
            ))
        for rel in filter(lambda rel: rel.to_many, schema.relationships):
            self.add_validator_method(validator.ToManyRelationship(
                name=rel.name, types=rel.remote_types
            ))
        for link in schema.links:
            self.add_validator_method(validator.Link(
                name=link.name
            ))
        for meta in schema.meta:
            self.add_validator_method(validator.Meta(
                name=meta.name
            ))
        return None
