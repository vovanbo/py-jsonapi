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
jsonapi.core
============

The core package of *py-jsonapi* contains the definitions for interfaces and
powerful, yet simple tools, which help you implementing a robust
http://jsonapi.org compliant API.

Each module aims to implement only one feature of the json:api specifiction.
Thus you can use most of them without an actual :class:`~jsonapi.core.api.API`
instance and pick only the ones you need.

If you prefer a higher level of abstraction, take a look
:mod:`~jsonapi.schema` pacakge and the various :ref:`extensions`.

.. Remember to add a .rst file for each Python module listed here in the
.. correct docs folder.

.. toctree::
    :maxdepth: 2

    api
    encoder
    errors
    handler
    includer
    pagination
    request
    response
    response_builder
    utilities
    validation
    validator
"""

# local
from . import api
from . import encoder
from . import errors
from . import handler
from . import includer
from . import pagination
from . import request
from . import response
from . import response_builder
from . import utilities
from . import validation
from . import validator
