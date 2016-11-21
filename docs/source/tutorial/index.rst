Tutorial
========

.. seealso::

    You can find all examples in the
    `examples folder <https://github.com/benediktschmitt/py-jsonapi/tree/master/examples/>`_.

In this tutorial, we will create a small database for our employees. We will
store their names and associate them with their boss. We will make use of
*mongodb* and *Flask*. Don't worry, you can walk through this tutorial without
knowing anything about these libraries.

We start by installing our dependencies:

.. code-block:: bash

    $ pip3 install py-jsonapi Flask mongoengine

After that, we create the :file:`employee` project folder. The final project
will look like this:

.. code-block:: text

    \employee
        \model.py
        \api.py
        \app.py

:file:`model.py`
----------------

Our model could not be much easier: We only need one field to store the full
name of the employee and one to store a reference to the chief:

.. literalinclude:: ../../../examples/employee/model.py

:file:`api.py`
--------------

We put everything related to the API in the :file:`api.py` module.

It's a good idea to create a dedicated *API folder* for larger applications and
to write one module for each collection.

Encoder
^^^^^^^

We start by defining an encoder. An encoder tells *py-jsonapi* how to serialize
an instance of *Employee* into a JSON API document:

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: EmployeeEncoder

If you want, you can customize the encoder methods by defining a *getter*.
You can read more about this in the :mod:`jsonapi.encoder` module.

Includer
^^^^^^^^

JSON API supports the inclusion of related resources and so does *py-jsonapi*.
By defining an *Includer*, we tell *py-jsonapi* how to load relationship
paths:

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: EmployeeIncluder

The *remote_types* paramter allows the includer to validate include paths
(check their existence) before performing the actual inclusion. This helps
to avoid unnecessairy database requests in case of an invalid include path.

You can read more about the includer in the :mod:`jsonapi.includer` module.

Validation
^^^^^^^^^^

When you receive JSON API documents from a client, you need to validate them
like every other input you receive via HTTP. *py-jsonapi* offers you two modules
for validation: The generic :mod:`jsonapi.validation` module and the
:mod:`jsonapi.validator` toolbox.

We will use the :mod:`~jsonapi.validator` toolbox and define two validators:
One for documents, which are used to *create* new employees and one for
documents, which are used to *update* existing employees.

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: NewEmployeeValidator

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: UpdateEmployeeValidator

The two validators are almost equal. The only difference is the *required*
parameter for the *name* and *chief* field in the *NewEmployeeValidator*.

If you wonder, what the *regex* in the *ID descriptor* means: It matches
a *mongodb* ObjectID.

You can read more about the includer in the :mod:`jsonapi.validator` module.

Collection Handler
^^^^^^^^^^^^^^^^^^

.. seealso::

    *   http://jsonapi.org/format/#fetching-resources
    *   http://jsonapi.org/format/#crud-creating

JSON API defines four different endpoint types: *collection*, *resource*,
*relationship* and *related*.

We start by implementing the collection endpoint for our employees. This
endpoint supports the *GET* and *POST* HTTP methods. The collection can be
filtered and sorted by the names the employees. Furthermore, it is
paginated.

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: EmployeeCollection

As you can see, it is very easy to implement the collection endpoint. The most
of the work is done by *py-jsonapi* and you only need to put the pieces
together.

Resource Handler
^^^^^^^^^^^^^^^^

.. seealso::

    *   http://jsonapi.org/format/#fetching-resources
    *   http://jsonapi.org/format/#crud-updating
    *   http://jsonapi.org/format/#crud-deleting

The *resource* endpoint supports the *GET*, *PATCH* and *DELETE* HTTP methods.

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: EmployeeResource

Relationship Handlers
^^^^^^^^^^^^^^^^^^^^^

.. seealso::

    *   http://jsonapi.org/format/#fetching-relationships
    *   http://jsonapi.org/format/#crud-updating-relationships


The relationship endpoint provides information about the resource linkage.

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: EmployeeRelationshipsChief


Related Handlers
^^^^^^^^^^^^^^^^

.. seealso::

    *   http://jsonapi.org/format/#fetching-relationships

In contrast to the *relationships* endpoint, the *related* endpoint allows the
client to fetch the related resource.

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: EmployeeRelatedChief


API factory
^^^^^^^^^^^

Now we need to wire everything up. Our API is created in a factory function,
which takes care of the initialisation and registration of the handlers:

.. literalinclude:: ../../../examples/employee/api.py
    :pyobject: create_api

:file:`app.py`
--------------

Finally, we create the *Flask* application and :file:`app.py` file.

.. literalinclude:: ../../../examples/employee/app.py

We use the *py-jsonapi-flask* extension, which embedds the API into a
*Flask* application.

When the script is executed, we connect to the database and start the
integrated web server.

Play With It
------------

Start the server with

.. code-block:: bash

    $ python3 app.py

and browse to http://localhost:5000/api/Employee. You can use the
*employee_client* script in the *examples* folder to create new employees.
