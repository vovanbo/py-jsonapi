#!/usr/bin/env python3

import mongoengine


class Employee(mongoengine.Document):
    name = mongoengine.StringField()
    chief = mongoengine.ReferenceField("Employee")
