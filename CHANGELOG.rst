Changelog
=========

*   1.0.0b0

    The old architecture of *py-jsonapi* was not flexible enough for the
    type of applications I develop and wish to develop. Problems occured, when
    authentication and authorization should be integrated in the encoding
    and patching process (*"is the client allowed to read this attribute,
    can it change the value of this relationship?"*)

    The new *jsonapi* has a clean structure and the modules are highly
    independant. Used together, they allow you to built an API, which scales.
    A usual JSON API request can be split up into these phases:

    1.  parse the request parameters (done by the *Request* class)
    2.  validate the received document (done by the *Validator* class)
    3.  patch the resource (that's your job)
    4.  compose the response document

        1. include related resources (done by the *Includer* class)
        2. serialize all resources (done by the *Encoder* class)

    Furthermore, the pagination feature of *to-many* relationships is now
    fully supported.

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
