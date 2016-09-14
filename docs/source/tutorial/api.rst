.. _blog-api:

The API
-------

.. hint::

    Click here to download the complete
    :download:`api.py <../../../examples/blog/api.py>` file.

Finally, we can create the API. Because we use *flask* as web-framework, we
profit from the *py-jsonapi-flask* extension.

We want to store the *sqlalchemy* session and the current *api client* in
the request's *settings* dictionary. We already used it in the
:file:`api_types.py` module. You can override the
:meth:`~jsonapi.base.api.API.prepare_request` method to manipulate the request
before it is given to the request handlers:

.. literalinclude:: ../../../examples/blog/api.py
    :pyobject: API

Now we only have to wire up everything:

.. literalinclude:: ../../../examples/blog/api.py
    :pyobject: create_api

.. literalinclude:: ../../../examples/blog/api.py
    :pyobject: create_app

You can start the application with:

.. code-block:: bash

    $ python3 api.py

The resources are available at:

.. code-block:: none

    localhost:5000/api/User
    localhost:5000/api/Post
