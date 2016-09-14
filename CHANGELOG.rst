Changelog
=========

*   1.0.0b0

    *   This library now follows a **model-view** approach. This gives
        the developer more control about the serialization and patching of
        resources.

        Implementing a permission system is now very easy.

        The *Database*, *Schema*, *Serializer* and *Unserializer* classes
        are now combined to a new class *Type*. A *Type* can be implemented
        by using decorators, similar to the *marker* in 0.3.0b0.

        There is now no need for a *bulk_database*, because each *Type*
        has all methods needed to integrate it into the JSON API.

    *   The extensions (sqlalchemy, mongoengine, motorengine, flask, tornado)
        are now separate projects and can be installed with pip. This change
        makes the development and versioning easier.

    *   **Everything, what was possible in 0.3.0b0 is still possible in 1.0.0b0+**

    These changes were necessairy, because implementing a new API was very
    complicated in 0.3.0b0, when no extension was available for the target web
    framework or database. Writing a good permission system, which prevents
    the client from reading or editing some fields was not possible.

    The earlier versions py-jsonapi were great for creating an API based on
    existing models very fast. But it was not adaptable. In the next
    minor releases, I will add a ``make_type(model)`` factory, which creates
    a py-jsonapi *Type* based on the model, similar to the creation of
    *schema* in the earlier versions:

    .. code-block:: python3

        # 0.3.0b0
        user_schema = jsonapi.sqlalchemy.Schema(User)
        # or
        user_schema = jsonapi.mongoengine.Schema(User)

        # vs 1.0.0b0+
        user_type = jsonapi.base.make_type(model)

*   0.3.0b0

    *   Removed the *remove()* method from the *to-many* relationship
        descriptor, because it is not needed.

*   0.2.1b0 - 0.2.6b0

    *   Added asyncio support
    *   Added motorengine

*   0.2.0b0

    *   The bulk database is now an extension
    *   The API now takes only one database adapter for all models. This removes
        one layer in the database hierarchy.
    *   The relationship schema's *delete* method has been renamed to *clear*
    *   The serializer has been split up into *Serializer* and *Unserializer*
    *   A dictionary ``_jsonapi``, which contains the serializer, typename,
        schema, ... is added to each resource class
    *   Everything that was names *model* is now named *resource_class*
