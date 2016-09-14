Blog
====

.. seealso::

    You can find the blog application in the
    `examples folder <https://github.com/benediktschmitt/py-jsonapi/tree/master/examples/blog>`_.

Our little blog has only two models: *User* and *Post*. We will only built the
API and do not care about authentication.


The Models
----------

To make things easier for use, we will use *sqlalchemy* and the py-jsonapi
extension for it. You can install *sqlalchemy* and *py-jsonapi-sqlalchemy*
via PyPi:

.. code-block:: bash

    $ pip3 install SQLAlchemy py-jsonapi-sqlalchemy

We start our :file:`blog.py` file by setting up sqlalchemy::

    #!/usr/bin/env python3

    import datetime

    import sqlalchemy
    import sqlalchemy.orm
    import sqlalchemy.ext.declarative

    import jsonapi
    import jsonapi_sqlalchemy


    Base = sqlalchemy.ext.declarative.declarative_base()
    engine = sqlalchemy.create_engine("sqlite:///blog.db")

    Session = sqlalchemy.orm.sessionmaker()
    Session.configure(bind=engine)

Now, we can define our *User* class, which can hold a user id, the user's name
and also a list of the posts written by the user::

    class User(Base):

        __tablename__ = "user"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
        name = sqlalchemy.Column("name", sqlalchemy.String(50), nullable=False)
        posts = sqlalchemy.orm.relationship("Post", back_populates="author")

        @property
        def first_name(self):
            return self.name.split()[0]

The *Post* class must store a *text* and and the id of the *author*::

    class Post(Base):

        __tablename__ = "posts"

        id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
        text = sqlalchemy.Column(sqlalchemy.Text)
        author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
        author = sqlalchemy.orm.relationship("User", back_populates="posts")


We don't have any more models, so we can create the tables in the database::

    Base.metadata.create_all(engine)

.. _blog-api:

The API Schema
--------------

This library must know how to serialize an instance of *User* or *Post*. Thus,
we have to define a :class:`~jsonapi.base.schema.Schema` for each type, we want
to add to the API. Because we are using *sqlalchemy* as our ORM, we can use
the *py-jsonapi-sqlalchemy* extension, which saves a lot of work::

    class UserAPI(jsonapi_sqlalchemy.schema.Schema):

        resource_class = User

        id = jsonapi_sqlalchemy.schema.ID(sql=User.id)
        name = jsonapi_sqlalchemy.schema.ID

The API
-------

.. code-block:: none

    localhost:5000/api/User
    localhost:5000/api/Post
    localhost:5000/api/Comment
