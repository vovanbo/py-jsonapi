Changelog
=========

*   1.0.0b0

    *   The extensions (sqlalchemy, mongoengine, motorengine, flask, tornado)
        are now separate projects and can be installed with pip. This change
        makes the development and versioning easier.
    *   This library now follows a model-view approach. If you want, you have
        full control over the request handling by overriding the methods of
        the schema class.
    *   The main component of this library is now a *schema*, which must be
        defined for each type supported by the API.

    These changes were necessairy, because implementing a new API was very
    complicated in the earlier versions, when no extension was available for
    the target web framework or database. Implementing a permission system was
    also not easy. The new design is more structured and modules can be reused.

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
