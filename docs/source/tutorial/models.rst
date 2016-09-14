.. _blog-models:

The Models
----------

.. hint::

    Click here to download the complete
    :download:`models.py <../../../examples/blog/models.py>` file.

Now we are ready to define the *User* model. To keep things simple, it only
has an *id* and *name* attribute and a reference to the *posts* written by
the *user*:

.. literalinclude:: ../../../examples/blog/models.py
    :pyobject: User

The *Post* model has an attribute *id* and *text* and a relationship *author*,
which points to the *User*, who wrote the post.

.. literalinclude:: ../../../examples/blog/models.py
    :pyobject: Post
