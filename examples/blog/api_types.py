#!/usr/bin/env python3

import jsonapi
from models import User, Post


__all__ = ["UserAPI", "PostAPI", "api"]


class UserAPI(jsonapi.base.schema.Type):

    resource_class = User

    @jsonapi.base.schema.ID()
    def id(self, user):
        """
        JSON API requires an ID to be a string. So we must convert the id,
        before returning it.
        """
        return str(user.id)

    @jsonapi.base.schema.Attribute()
    def name(self, user, request):
        """
        *name* will appear in the JSON API attributes object of the user.
        """
        return user.name

    @name.setter
    def name(self, user, new_name, request):
        """
        We want the name to be editable, so we must define a setter.

        We check if the new name is a string and if the API client is
        authorized to edit the name. If not, we throw an exception.
        """
        if request.settings["user"] != user:
            raise jsonapi.base.errors.Forbidden()
        if not isinstance(new_name, str):
            raise jsonapi.base.errors.BadRequest(detail="The name must be a string.")
        if not new_name.strip():
            raise jsonapi.base.errors.BadRequest(detail="The name is empty.")
        user.name = new_name.strip()
        return None

    @jsonapi.base.schema.ToManyRelationship(remote_type="Post")
    def posts(self, user, request, required=False):
        """
        We don't want the *post* relationship to be writable. It can only
        be edited from the remote side: *Post.author*.

        Therefore we define a *getter*, but no *setter*.
        """
        if required:
            return user.posts

        # We can return the symbol RelationshipNotLoaded, to avoid loading
        # the posts from the database, when they are not really needed.
        return jsonapi.base.schema.RelationshipNotLoaded

    @jsonapi.base.schema.Meta()
    def foo(self, user, request):
        """
        We can also add members to the user's JSON API meta object.

        *foo* will appear with a customized greeting for the user in the meta
        object.
        """
        return "Hello {}!".format(user.name)

    @jsonapi.base.schema.Link(name="foo")
    def foo_link(self, user, request):
        """
        We can also add members to the user's JSON API links object.

        Since we already defined a class property *foo*, we must name the
        property in Python *foo_link*. However, the link name should still
        be *foo*, so we use the *name* argument of the Link descriptor.
        """
        return "https://github.com"

    # We implemented everything needed to serialize a User object. However,
    # we need to override some methods, to make sure that changes are
    # saved in the database.
    # If you use the sqlalchemy extension, you don't have to override these
    # methods, but we only use the base package of py-jsonapi, so we have to.
    #
    # Each method below is directly linked with an API url endpoint.

    def create_resource(self, data, request):
        """
        POST /api/User/

        *data* is a JSON API resource object which contains the initial values
        for the attributes and relationships of the new user.
        """
        # The base class method will use the constructor of User to create
        # a new instance. We only have to save the result in the database.
        new_user = super().create_resource(data, request)
        session = request.settings["sql_session"]
        session.add(new_user)
        session.commit()
        return new_user

    def update_resource(self, user, data, request):
        """
        PATCH /api/User/<id>

        *user* is the User object or the id of the User, that should be updated.
        *data* is a JSON API relationships object, which contains the new values.
        """
        # The base class method uses the setters of the properties we defined
        # above to patch the user. We only have to save the result in the
        # databse.
        user = super().update_resource(user, data, request)
        session = request.settings["sql_session"]
        session.add(user)
        session.commit()
        return user

    def delete_resource(self, user, request):
        """
        DELETE /api/User/<id>

        Deletes the *user*. Only the user itself should be able to delete
        his account, so we throw an exception, if someone else tries to delete
        the user.
        """
        session = request.settings["sql_session"]

        # user is only the id of the user.
        if isinstance(user, str):
            user_id = user
            user = session.query(User).get(user_id)
            if user is None:
                raise jsonapi.base.errors.ResourceNotFound(user_id)

        # Authorize the user
        if user != request.settings["user"]:
            raise jsonapi.base.errors.Forbidden()

        session.delete(user)
        session.commit()
        return None

    def update_relationship(self, relname, user, data, request):
        """
        PATCH /api/User/<id>/relationships/<relname>

        *relname* is the name of the relationship, which should be patched.
        *user* is the user object or the id of the user, who is affected from the patched
        *data* is a JSON API relationship object with new values for the relationship
        """
        # The base class method uses the *setter* of the properties to change
        # the relationships. So we only have to save the changes.
        user = super().update_relationship(relname, user, data, request)
        session = request.settings["sql_session"]
        session.add(user)
        session.commit()
        return user

    def extend_relationship(self, relname, user, data, request):
        """
        POST /api/User/<id>/relationships/<relname>

        This is similar to *update_relationship()*, but adds new relatives
        to a *to-many* relationship.
        """
        session = request.settings["sql_session"]
        user = super().update_relationship(relname, user, data, request)
        session.add(user)
        session.commit()
        return user

    def remove_relationship(self, relname, user, data, request):
        """
        DELETE /api/User/<id>/relationships/<relname>

        Removes all related resources from a *to-many* relationship.
        """
        # Again, we only have to commit the changes to the database :)
        user = super().update_relationship(relname, user, data, request)
        session = request.settings["sql_session"]
        session.add(user)
        session.commit()
        return user

    def get_collection(self, query_params, request):
        """
        GET /api/User/

        Returns the user collection.

        *query_params* is a dictionary, which contains parameters like
        filters, limit, offset, ... for the query.
        """
        session = request.settings["sql_session"]

        # We don't support filtering or sorting.
        if query_params.get("filters"):
            raise jsonapi.base.errors.BadRequest()
        if query_params.get("sort"):
            raise jsonapi.base.errors.BadRequest()

        limit = query_params.get("limit")
        offset = query_params.get("offset", 0)

        users = session.query(User).limit(limit).offset(offset).all()

        # The total number of users is important for the pagination.
        total_number = session.query(User).count()
        return (users, total_number)

    def get_resources(self, ids, include, request):
        """
        This method is not directly associated with any API endpoint, but
        needed to implemnt features like the *including related resources*.

        *ids* is a list of user ids
        *include* is a list of relationship paths, which should be pre-loaded
        from the database if possible

        We return a dictionary, which maps the JSON API id of the resources
        to the resouce.
        """
        session = request.settings["sql_session"]
        users = dict()
        for id_ in ids:
            user = session.query(User).get(id_)
            if user is None:
                raise jsonapi.base.errors.ResourceNotFound((self.typename, id_))
            users[("User", id_)] = user
        return users


class PostAPI(jsonapi.base.schema.Type):
    """
    The API for Post objects can be analogue to the User API.
    """

    resource_class = Post

    @jsonapi.base.schema.ID()
    def id(self, post):
        return str(post.id)

    @jsonapi.base.schema.Attribute()
    def text(self, post, request):
        return post.text

    @text.setter
    def text(self, post, new_text, request):
        if request.settings["user"] != post.author:
            raise jsonapi.base.errors.Forbidden()
        if not isinstance(new_text, str):
            raise jsonapi.base.errors.BadRequest(detail="'text' must be a string.")
        post.text = new_text
        return None

    @jsonapi.base.schema.ToOneRelationship(remote_type="User")
    def author(self, post, request, required=False):
        """
        Returns the id tuple of the related resource.
        """
        return ("User", str(post.author_id))

    @author.setter
    def author(self, post, data, new_author, request):
        if request.settings["user"] != post.author:
            raise jsonapi.base.errors.Forbidden()
        post.author = new_author
        post.author_id = new_author.id
        return None

    # Now we have to override the same methods again to make sure changes
    # of a Post object are stored in the database.
    #
    # End again, we should have used the sqlalchemy extension ;(

    def create_resource(self, data, request):
        """
        POST /api/Post/
        """
        new_post = super().create_resource(data, request)
        session = request.settings["sql_session"]
        session.add(new_post)
        session.commit()
        return new_post

    def update_resource(self, post, data, request):
        """
        PATCH /api/Post/<id>
        """
        post = super().update_resource(post, data, request)
        session = request.settings["sql_session"]
        session.add(post)
        session.commit()
        return post

    def delete_resource(self, post, request):
        """
        DELETE /api/Post/<id>
        """
        session = request.settings["sql_session"]

        # post is only an ID, so we must load the actual object first.
        if isinstance(post, str):
            post_id = post
            post = session.query(Post).get(post_id)
            if post is None:
                raise jsonapi.base.errors.ResourceNotFound(post_id)

        # Authorize the API client
        if post.author != request.settings["user"]:
            raise jsonapi.base.errors.Forbidden()

        session.delete(post)
        session.commit()
        return None

    def update_relationship(self, relname, post, data, request):
        """
        PATCH /api/Post/<id>/relationships/<relname>
        """
        post = super().update_relationship(relname, post, data, request)
        session = request.settings["sql_session"]
        session.add(post)
        session.commit()
        return post

    def extend_relationship(self, relname, post, data, request):
        """
        POST /api/Post/<id>/relationships/<relname>
        """
        session = request.settings["sql_session"]
        post = super().update_relationship(relname, post, data, request)
        session.add(post)
        session.commit()
        return post

    def remove_relationship(self, relname, post, data, request):
        """
        DELETE /api/Post/<id>/relationships/<relname>
        """
        # Again, we only have to commit the changes to the database :)
        post = super().update_relationship(relname, post, data, request)
        session = request.settings["sql_session"]
        session.add(post)
        session.commit()
        return post

    def get_collection(self, query_params, request):
        """
        GET /api/Post/
        """
        session = request.settings["sql_session"]

        # We don't support filtering or sorting.
        if query_params.get("filters"):
            raise jsonapi.base.errors.BadRequest()
        if query_params.get("sort"):
            raise jsonapi.base.errors.BadRequest()

        limit = query_params.get("limit")
        offset = query_params.get("offset", 0)

        posts = session.query(Post).limit(limit).offset(offset).all()

        total_number = session.query(Post).count()
        return (posts, total_number)

    def get_resources(self, ids, include, request):
        session = request.settings["sql_session"]
        posts = dict()
        for id_ in ids:
            post = session.query(Post).get(id_)
            if post is None:
                raise jsonapi.base.errors.ResourceNotFound((self.typename, id_))
            posts[("User", id_)] = post
        return posts
