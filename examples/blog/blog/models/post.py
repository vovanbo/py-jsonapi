#!/usr/bin/env python3

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

from ..sql import Base


class Post(Base):

    __tablename__ = "posts"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    text = sqlalchemy.Column(sqlalchemy.Text)

    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    author = sqlalchemy.orm.relationship("User", back_populates="posts")
