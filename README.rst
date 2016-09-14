py-jsonapi
==========

**This library is under active development.**
**If you have any suggestions or found bugs, please create a new issue.**


This library is a model-view framework for building a http://jsonapi.org/
compliant API. There are extensions for many web frameworks and database drivers:

*   `flask <https://github.com/benediktschmitt/py-jsonapi-flask>`__
*   `tornado <https://github.com/benediktschmitt/py-jsonapi-tornado>`__
*   `sqlalchemy <https://github.com/benediktschmitt/py-jsonapi-sqlalchemy>`__
*   `mongoengine <https://github.com/benediktschmitt/py-jsonapi-mongoengine>`__
*   `motorengine <https://github.com/benediktschmitt/py-jsonapi-motorengine>`__

Furthermore, it can be extended to work with **all web frameworks and database
engines**. You can use **blocking and asynchronous** code.


Example
-------

First of all, here is an example, when you use the sqlalchemy extension:

.. code-block:: python3

    class PostAPI(jsonapi_sqlalchemy.schema.Type):
        resource_class = Post

        id = jsonapi_sqlalchemy.schema.ID(Post.id)
        text = jsonapi_sqlalchemy.schema.Attribute(Post.text)
        author = jsonapi_sqlalchemy.schema.ToOneRelationship(Post.author, read_only=True)

        @text.setter
        def text(self, post, new_text, request):
            if request.user != post.author:
                raise jsonapi.base.errors.Forbidden()
            post.text = new_text

That's it. The sqlalchemy extension implements everything else.

If you don't want to use an extension, you can use the *base*
descriptors. Here is a code snippet, which should give you an impression of
*py-jsonapi*:

.. code-block:: python3

    class PostAPI(jsonapi.base.schema.Type):
        resource_class = Post

        @jsonapi.base.schema.ID()
        def id(self, post):
            return str(post.id)

        @jsonapi.base.schema.Attribute()
        def text(self, post, request):
            return post.text

        @jsonapi.base.schema.Attribute()
        def text(self, post, new_text, request):
            if request.user != user:
                raise jsonapi.base.errors.Forbidden()
            post.text = new_text
            return None

        @jsonapi.base.schema.ToManyRelationship(remote_type="User")
        def author(self, post, request):
            return ("User", post.author_id)

        @author.related
        def author(self, post, include, request):
            return post.get_author(load_relatives=include)

        def create_resource(self, data, request):
            new_post = super().create_resource(data, request)
            new_post.save()
            return new_post

        def update_resource(self, post, data, request):
            post = super().update_resource(post, data, request)
            post.save()
            return post

        def delete_resource(self, post, request):
            post = Post.objects.get(post)
            if post is None:
                raise jsonapi.base.errors.ResourceNotFound()
            post.delete()
            return None

        def get_collection(self, query_params, request):
            offset = query_params.get("offset")
            limit = query_params.get("limit")

            start = offset if offset is not None else 0
            end = start + limit if limit is not None else -1

            posts = Post.objects[start:end]
            return (posts, Post.objects.count())

        def get_resources(self, ids, include, request):
            posts = Post.objects.in_bulk(ids)
            posts = {
                ("Post", str(post.id)): post for post in posts.values()
            }
            return posts

If you want to know more, take a look at the
`documentation <https://py-jsonapi.readthedocs.org>`__. We will implement
a *blog* with *py-jsonapi*.


Changelog
---------

Take a look at the `Changelog <./CHANGELOG.rst>`_ to find out, what has changed
in the last versions.

I also explain, why I made huge changes between the *0.0.0b0* beta version
and the *1.0.0b0* beta version.


Docs
----

Check out the docs for a full introduction at
https://py-jsonapi.readthedocs.org.


License
-------

This library is licensed under the `MIT License <./LICENSE>`_.


Contributions and questions
---------------------------

Contributions are always welcome. If you have a question, don't hesitate to
open a new issue.


Version numbers
---------------

We will use semantic version numbers, starting with the first release.
