#!/usr/bin/env python3

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

from sql import Base


__all__ = ["User", "Post"]


class User(Base):

    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column("name", sqlalchemy.String(50))
    posts = sqlalchemy.orm.relationship("Post", back_populates="author")


class Post(Base):

    __tablename__ = "posts"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    text = sqlalchemy.Column(sqlalchemy.Text)

    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    author = sqlalchemy.orm.relationship("User", back_populates="posts")
