#!/usr/bin/env python3

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative

from ..sql import Base


class User(Base):

    __tablename__ = "users"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column("name", sqlalchemy.String(50))
    posts = sqlalchemy.orm.relationship("Post", back_populates="author")
