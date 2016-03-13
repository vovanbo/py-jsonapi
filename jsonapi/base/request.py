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
jsonapi.base.request
====================

A class for representing HTTP requests. It helps to get some query arguments,
which are defined in the JSONapi specification.
"""

# std
import json
import logging
import re
import urllib.parse

# third party
from cached_property import cached_property

# local
from .errors import BadRequest


LOG = logging.getLogger(__file__)


__all__ = [
    "Request"
]


class Request(object):
    """
    Wraps a request object, which can be used to call the View class.

    :arg str uri:
    :arg str method:
    :arg dict headers:
    :arg bytes body:
    """

    def __init__(self, uri, method, headers, body):
        """
        """
        self.uri = uri
        self.method = method.lower()
        self.headers = {key.lower(): value for key, value in headers.items()}
        self.body = body

        #: Contains parameters, which are encoded into the URI.
        #: For example a resource uri: ``http://localhost:5000/api/User/1``
        #: contains the id ``{'id': '1'}``
        #: This attribute is populated by
        #:
        #: :seealso: :meth:`jsonapi.base.api.API.find_handler`
        self.japi_uri_arguments = dict()
        return None

    @cached_property
    def parsed_uri(self):
        """
        Returns a tuple with the uri components.
        """
        return urllib.parse.urlparse(self.uri)

    @cached_property
    def query(self):
        """
        Returns a dictionary which maps a query key to its values.
        """
        query = urllib.parse.parse_qs(self.parsed_uri.query)
        return query

    def get_query_argument(self, name, fallback=None):
        """
        Returns the (first) value of the query argument with the name *name*. If
        the argument does not exist, *fallback* is returned.

        :arg str name:
        :arg fallback:
        """
        value = self.query.get(name)
        return value[0] if value else fallback

    @cached_property
    def content_type(self):
        """
        Returns a tuple, with the media type and the parameters.

        .. code-block:: python3

            media_type, media_parameters = request.content_type

        :seealso: :attr:`media_parameters`
        :seealso: https://tools.ietf.org/html/rfc7231#section-3.1.1.1
        .. todo:: Parse the media parameters and return them.
        """
        content_type = self.headers.get("content-type", "")
        type_, *parameters = content_type.split(";")
        return (type_, dict())

    @cached_property
    def japi_page_number(self):
        """
        Returns the number of the requested page or None. The first page
        has the number 0.

        Query parameter: ``page[number]``

        :raises BadRequest:
            If ``page[number]`` is not a positive integer

        :seealso: http://jsonapi.org/format/#fetching-pagination
        """
        tmp = self.get_query_argument("page[number]")
        if tmp is None:
            return None
        elif tmp.isdigit():
            return int(tmp)
        else:
            raise BadRequest(
                detail="The 'page[number]' must be a positive integer.",
                source_parameter="page[number]"
            )

    @cached_property
    def japi_page_size(self):
        """
        Returns the size of the pages or None.

        Query parameter: ``page[size]``

        :raises BadRequest:
            If ``page[size]`` is not a positive integer greater than 0

        :seealso: http://jsonapi.org/format/#fetching-pagination
        """
        tmp = self.get_query_argument("page[size]")
        if tmp is None:
            return None
        elif tmp.isdigit() and int(tmp) > 0:
            return int(tmp)
        else:
            raise BadRequest(
                detail="The 'page[size]' must be a positive integer.",
                source_parameter="page[size]"
            )

    @cached_property
    def japi_paginate(self):
        """
        Returns True, if the result should be paginated.
        This is the case, if ``page[size]`` and ``page[number]`` are both
        present and valid.

        .. seealso::

            *   :attr:`japi_page_size`
            *   :attr:`japi_page_number`
            *   http://jsonapi.org/format/#fetching-pagination
        """
        size = self.japi_page_size
        number = self.japi_page_number
        if size is None and number is None:
            return False
        elif size is not None and number is not None:
            return True
        else:
            raise BadRequest(
                detail="Pagination requires 'page[size]' and 'page[number]'.",
                source_parameter="page[]"
            )

    @cached_property
    def japi_page_limit(self):
        """
        Returns the *limit* based on the :attr:`japi_page_size`.
        """
        return self.japi_page_size if self.japi_paginate else None

    @cached_property
    def japi_page_offset(self):
        """
        Returns the offset based on the :attr:`japi_page_size` and
        :attr:`japi_page_number`.
        """
        return self.japi_page_size*self.japi_page_number \
            if self.japi_paginate else None

    @cached_property
    def japi_filters(self):
        """
        Please note, that the *filter* strategy is not defined by the
        jsonapi specification and depends on the implementation. If you want to
        use another filter strategy, feel free to **override** this method.

        Returns a list, which contains 3-tuples of the structure::

            (fieldname, filtername, rule)

        Each entry is a string. For example::

            ("name", "startswith", "Homer")
            ("age", "gt", 25)

        Filter can be applied using the query string::

            >>> # /api/User/?filter[name]=endswith:'Simpson'
            >>> request.japi_filters
            ... [("name", "endswith", "Simpson")]

            >>> # /api/User/?filter[name]=in:['Homer Simpson', 'Darth Vader']
            >>> request.japi_filters
            ... [("name", "in", ["Homer Simpson", "Darth Vader"])]

            >>> # /api/User/?filter[email]=startswith:'lisa'&filter[age]=lt:20
            >>> request.japi_filters
            ... [("email", "startswith", "lisa"), ("age", "lt", 20)]

        The general syntax is::

            "?filter[fieldname]=filtername:rule"

        Where *fieldname* is the name of a relationship or attribute,
        *filtername* is the name of the filter which should be applied and
        *rule* is any JSON serializable object.

        :raises BadRequest:
            If the rule of a filter is not a JSON object.
        :raises BadRequest:
            If a filtername contains other characters than [a-z].
        """
        KEY_RE = re.compile(r"filter\[(?P<field>[A-z0-9_]+)\]")
        VALUE_RE = re.compile(r"(?P<filtername>[a-z]+):(?P<rule>.*)")

        filters = list()
        for key, values in self.query.items():
            key_match = re.fullmatch(KEY_RE, key)
            value_match = re.fullmatch(VALUE_RE, values[0])

            # If the key indicates a filter, but the value is not correct
            # formatted.
            if key_match and not value_match:
                field = key_match.group("field")
                raise BadRequest(
                    detail="The filter '{}' is not correct applied.".format(field),
                    source_parameter=key
                )

            # The key indicates a filter and the filternames exists.
            elif key_match and value_match:
                field = key_match.group(1)
                filtername = value_match.group("filtername")
                rule = value_match.group("rule")
                try:
                    rule = json.loads(rule)
                except Exception as err:
                    LOG.debug(err, exc_info=False)
                    raise BadRequest(
                        detail="The rule '{}' is not JSON serializable".format(rule),
                        source_parameter=key
                    )

                filters.append((field, filtername, rule))
        return filters

    @cached_property
    def japi_fields(self):
        """
        Returns the fields, which should be included in the response
        (sparse fieldset).

        .. code-block:: python3

            >>> # /api/User?fields[User]=email,name&fields[Post]=comments
            >>> request.japi_fields
            ... {"User": ["email", "name"], "Post": ["comments"]}

        :seealso: http://jsonapi.org/format/#fetching-sparse-fieldsets
        """
        FIELDS_RE = re.compile(r"fields\[([A-z0-9_]+)\]")

        fields = dict()
        for key, value in self.query.items():
            match = re.fullmatch(FIELDS_RE, key)
            if match:
                typename = match.group(1)
                type_fields = value[0].split(",")
                type_fields = [
                    item.strip() for item in type_fields if item.strip()
                ]

                fields[typename] = type_fields
        return fields

    @cached_property
    def japi_include(self):
        """
        Returns the names of the relationships, which should be included into
        the response.

        .. code-block:: python3

            >>> # /api/Post?include=author,comments.author
            >>> req.japi_include
            ... [["author"], ["comments", "author"]

        :seealso: http://jsonapi.org/format/#fetching-includes
        """
        include = self.get_query_argument("include", "")
        include = [path.split(".") for path in include.split(",") if path]
        return include

    @cached_property
    def japi_sort(self):
        """
        Returns a list with two tuples, describing how the output should be
        sorted:

        .. code-block:: python3

            >>> # /api/Post?sort=name,-age
            ... [("+", "name"), ("-", "age")]

        :seealso: http://jsonapi.org/format/#fetching-sorting
        """
        tmp = self.get_query_argument("sort")
        tmp = tmp.split(",") if tmp else list()

        sort = list()
        for field in tmp:
            field = field.strip()
            if field[0] == "-":
                sort.append(("-", field[1:]))
            elif field[0] == "+":
                sort.append(("+", field[1:]))
            else:
                sort.append(("+", field))
        return sort
