#!/usr/bin/env python3

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative


__all__ = ["Base", "engine", "Session"]


# Create the sqlalchemy base, engine and the sessionmaker.
Base = sqlalchemy.ext.declarative.declarative_base()
engine = sqlalchemy.create_engine("sqlite:///blog.db")

Session = sqlalchemy.orm.sessionmaker()
Session.configure(bind=engine)
