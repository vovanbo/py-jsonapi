Changelog
=========

*   1.0.0b0

    This library is now splitted in two packages: *jsonapi.core* and
    *jsonapi.schema*.

    The *jsonapi.core* package is essentially a collection of tools, which make
    it easier to implement a JSON API.
    The *jsonapi.schema* package is built on top of the *core* and is meant
    to be used in combination with existing ORMs.

    The old architecture of *py-jsonapi* was not flexible enough for the
    type of applications I develop and wish to develop. Problems occured, when
    authentication and authorization should be integrated in the encoding
    and patching process (*"is the client allowed to read this attribute,
    can he change the value of this relationship?"*)

    The new *jsonapi.core* has a clean structure and the modules are highly
    independant. Used together, they allow you to built an API, which scales.
    A usual JSON API request can be described by different phases:

    1.  parse the request parameters (done by the *Request* class)
    2.  validate the document sent from the client (done by the *Validator*)
    3.  patch the resource (completely up to you)
    4.  compose the response document

        1. include related resources (done by the *Includer* class)
        2. serialize all resources (done by the *Encoder* class)

    If you want more abstraction, you can use the *jsonapi.schema* package.
    After defining a *Schema*, the validators, includer and request
    handlers are generated automatic and you are done with a few lines of
    code.

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
