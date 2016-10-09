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
jsonapi.core.pagination
=======================

This module contains a helper for the pagination feature:
http://jsonapi.org/format/#fetching-pagination
"""

# std
import urllib.parse


class Pagination(object):
    """
    A helper class for the pagination.

    The first page has the number **0**.

    :arg str uri:
        The uri to the endpoint which provides a collection
    :arg int current_page:
        The number of the current page
    :arg int page_size:
        The number of resources on a page
    :arg int total_resources:
        The total number of resources in the collection
    """

    def __init__(self, uri, current_page, page_size, total_resources):
        """
        """
        self.uri = uri
        self.parsed_uri = urllib.parse.urlparse(uri)
        self.query_uri = urllib.parse.parse_qs(self.parsed_uri.query)

        # Get the current page number and size.
        assert current_page >= 0
        self.current_page = current_page

        assert page_size >= 1
        self.page_size = page_size

        # Get the number of resources
        assert total_resources >= 0
        self.total_resources = total_resources

        self.total_pages = int(self.total_resources/self.page_size)

        # Build all links
        self.link_self = self._page_link(self.current_page, self.page_size)
        self.link_first = self._page_link(0, self.page_size)
        self.link_last = self._page_link(self.total_pages, self.page_size)

        self.has_prev = (self.current_page > 0)
        self.link_prev = self._page_link(self.current_page - 1, self.page_size)

        self.has_next = (self.current_page < self.total_pages)
        self.link_next = self._page_link(self.current_page + 1, self.page_size)
        return None

    @classmethod
    def from_request(cls, request, total_resources):
        """
        Shortcut for creating a Pagination object based on a jsonapi
        :class:`~jsonapi.core.request.Request`.
        """
        assert request.japi_paginate
        return cls(
            uri=request.uri, current_page=request.japi_page_number,
            page_size=request.japi_page_size, total_resources=total_resources
        )

    def _page_link(self, page_number, page_size):
        query = self.query_uri
        query.update({
            "page[number]": page_number,
            "page[size]": page_size
        })
        query = urllib.parse.urlencode(query)

        uri = "{scheme}://{netloc}{path}?{query}".format(
            scheme=self.parsed_uri.scheme,
            netloc=self.parsed_uri.netloc,
            path=self.parsed_uri.path,
            query=query
        )
        return uri

    @property
    def json_meta(self):
        """
        A dictionary, which must be included in the top-level *meta object*. It
        contains these keys:

        *   *total-pages*
            The total number of pages

        *   *total-resources*
            The total number of resources

        *   *page*
            The number of the current page

        *   *page-size*
            The page size
        """
        d = {
            "total-pages": self.total_pages,
            "total-resources": self.total_resources,
            "page": self.current_page,
            "page-size": self.page_size
        }
        return d

    @property
    def json_links(self):
        """
        A dictionary, which must be included in the top-level *links object*. It
        contains these keys:

        *   *self*
            The link to the current page

        *   *first*
            The link to the first page

        *   *last*
            The link to the last page

        *   *prev*
            The link to the previous page (only set, if a previous page exists)

        *   *next*
            The link to the next page (only set, if a next page exists)
        """
        d = {
            "self": self.link_self,
            "first": self.link_first,
            "last": self.link_last
        }
        if self.has_prev:
            d["prev"] = self.link_prev
        if self.has_next:
            d["next"] = self.link_next
        return d
