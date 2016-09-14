.. _blog-api-types:

The API Types
-------------

.. hint::

    Click here to download the complete
    :download:`api_types.py <../../../examples/blog/api_types.py>` file.

Now we are ready to implement our JSON API and get in touch with *py-jsonapi*.

The essence of *py-jsonapi* is the :class:`~jsonapi.base.schema.type.Type` class,
which is similar to a schema. You can use *property*-like decorators, to
reflect the JSON API resource document of a type in Python. We will not use
all features of each decorator in this tutorial, so you should take a look
at their documentation:

*   :class:`~jsonapi.base.schema.id.ID`
*   :class:`~jsonapi.base.schema.attribute.Attribute`
*   :class:`~jsonapi.base.schema.to_one_relationship.ToOneRelationship`
*   :class:`~jsonapi.base.schema.to_many_relationship.ToManyRelationship`
*   :class:`~jsonapi.base.schema.link.Link`
*   :class:`~jsonapi.base.schema.meta.Meta`


When you use the *decorators*, *py-jsonapi* will know which attributes
and relationships exist on a resource, how to get their values and how to
patch them.
However, it knows nothing about your database and thus, you must override
some methods if you want to make changes to the resources permanent:

*   :meth:`~jsonapi.base.schema.type.Type.create_resource`
*   :meth:`~jsonapi.base.schema.type.Type.update_resource`
*   :meth:`~jsonapi.base.schema.type.Type.delete_resource`
*   :meth:`~jsonapi.base.schema.type.Type.update_relationship`
*   :meth:`~jsonapi.base.schema.type.Type.extend_relationship`
*   :meth:`~jsonapi.base.schema.type.Type.clear_relationship`
*   :meth:`~jsonapi.base.schema.type.Type.get_collection`
*   :meth:`~jsonapi.base.schema.type.Type.get_resource`

If you are lucky and an :ref:`extension <extensions>` for your database
exists, you don't have to overridde these methods and its enough to
use the *decorators*.

Here is the *API* definition for the *User* model:

.. literalinclude:: ../../../examples/blog/api_types.py
    :pyobject: UserAPI

Implementing the *PostAPI* is similar:

.. literalinclude:: ../../../examples/blog/api_types.py
    :pyobject: PostAPI
