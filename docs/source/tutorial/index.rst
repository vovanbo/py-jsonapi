Tutorial
========

.. seealso::

    You can find the blog application in the
    `examples folder <https://github.com/benediktschmitt/py-jsonapi/tree/master/examples/blog>`_.

.. toctree::
    :maxdepth: 1

    setup
    sql
    models
    api_types
    api
    next_steps


We will show you how to install *py-jsonapi* and how to create a simple blog
with *flask* and *sqlalchemy*.

You will learn how to use the decorators

*   :class:`~jsonapi.base.schema.id.ID`
*   :class:`~jsonapi.base.schema.attribute.Attribute`
*   :class:`~jsonapi.base.schema.to_one_relationship.ToOneRelationship`
*   :class:`~jsonapi.base.schema.to_many_relationship.ToManyRelationship`
*   :class:`~jsonapi.base.schema.link.Link`
*   and :class:`~jsonapi.base.schema.meta.Meta`

and how to implement a *py-jsonapi* :class:`~jsonapi.base.schema.type.Type`.
Furthermore, we will use the *py-jsonapi-flask* extension.
