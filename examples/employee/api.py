#!/usr/bin/env python3

import jsonapi
import jsonapi_flask
from model import Employee


class EmployeeEncoder(jsonapi.encoder.Encoder):
    resource_class = Employee
    name = jsonapi.encoder.Attribute()
    chief = jsonapi.encoder.ToOneRelationship()

    @jsonapi.encoder.Meta()
    def a_meta_value(self, employee, request):
        return "This text appears in the meta object."

    @jsonapi.encoder.Attribute()
    def first_name(self, employee, request):
        return employee.name.split()[0].strip()


class EmployeeIncluder(jsonapi.includer.Includer):
    resource_class = Employee
    chief = jsonapi.includer.ToOneRelationship(remote_types=["Employee"])


class NewEmployeeValidator(jsonapi.validator.Validator):
    id = jsonapi.validator.ID(regex="[A-z0-9]{24}")
    type = jsonapi.validator.Type(types=["Employee"])
    name = jsonapi.validator.Attribute(type=str, required=True)
    chief = jsonapi.validator.ToOneRelationship(
        types=["Employee"], require_data=True, required=True
    )


class UpdateEmployeeValidator(jsonapi.validator.Validator):
    id = jsonapi.validator.ID(regex="[A-z0-9]{24}")
    type = jsonapi.validator.Type(types=["Employee"])
    name = jsonapi.validator.Attribute(type=str)
    chief = jsonapi.validator.ToOneRelationship(
        types=["Employee"], require_data=True
    )


class EmployeeCollection(jsonapi.handler.Handler):

    def get(self, request):
        # The pagination module contains helpers for different
        # pagination strategies (number-size, limit-offset, cursor, ...)
        #
        # The NumberSize pagination extracts the page parameters from the
        # current request uri. The second parameter allows us to compute
        # the index of the last page.
        pagination = jsonapi.pagination.NumberSize.from_request(
            request, Employee.objects.count()
        )

        # We allow the request to contain some filters for the *name* field.
        mongo_filters = dict()
        if request.has_filter("name", "eq"):
            mongo_filters["name"] = request.get_filter("name", "eq")
        if request.has_filter("name", "startswith"):
            mongo_filters["name__startswith"] = request.get_filter("name", "startswith")

        # The collection can be sorted based on the *name* field.
        mongo_order = list()
        if request.get_order("name") == "+":
            mongo_order.append("name")
        else:
            mongo_order.append("-name")

        employees = Employee.objects(**mongo_filters)\
            .order_by(*mongo_order)\
            .skip(pagination.offset)\
            .limit(pagination.limit)

        # The response builder class will do the rest of the work:
        # Including the related resources (JSONAPI include parameter) and
        # composing the final JSON API document.
        return jsonapi.response_builder.Collection(request, data=list(employees))

    def post(self, request):
        # Validate the JSON API document first.
        NewEmployeeValidator().assert_one_resource_object(request.json)
        data = request.json["data"]

        # Now we load the chief object, if necessairy.
        # Since the *require_data* argument on the NewEmployeeValidator
        # is True, *request.json* contains a the *chief* relationship
        # and the *chief* relationship contains a *data* object.
        chief_id = data["relationships"]["chief"]["data"]
        if chief_id is None:
            chief = None
        else:
            chief = Employee.objects.filter(id=chief_id["id"]).first()
            if chief is None:
                raise jsonapi.errors.NotFound(details="The *chief* does not exist.")

        # Create a new employee.
        employee = Employee(
            name=data["attributes"]["name"],
            chief=chief
        )
        employee.save()

        # The NewResource response builder will set the LOCATION header
        # automatic.
        return jsonapi.response_builder.NewResource(request, data=employee)


class EmployeeResource(jsonapi.handler.Handler):

    def get(self, request):
        employee = Employee.objects\
            .filter(id=request.japi_uri_arguments["id"]).first()
        if employee is None:
            raise jsonapi.errors.NotFound()
        return jsonapi.response_builder.Resource(request, data=employee)

    def patch(self, request):
        employee = Employee.objects\
            .filter(id=request.japi_uri_arguments["id"]).first()
        if employee is None:
            raise jsonapi.errors.NotFound()

        UpdateEmployeeValidator().assert_one_resource_object(request.json)
        data = request.json["data"]

        if "name" in data["attributes"]:
            employee.name = data["attributes"]["name"]
        if "chief" in data["relationships"]:
            chief_id = data["relationships"]["chief"]["data"]
            if chief_id is None:
                chief = None
            else:
                chief = Employee.objects.filter(id=chief_id["id"]).first()
                if chief is None:
                    raise jsonapi.errors.NotFound()
            employee.chief = chief

        employee.save()
        return jsonapi.response_builder.Resource(request, data=employee)

    def delete(self, request):
        employee = Employee.objects\
            .filter(id=request.japi_uri_arguments["id"]).first()
        if employee is None:
            raise jsonapi.errors.NotFound()
        employee.delete()
        return jsonapi.response.Response(status=204)


class EmployeeRelationshipsChief(jsonapi.handler.Handler):

    def get(self, request):
        employee = Employee.objects\
            .filter(id=request.japi_uri_arguments["id"]).first()
        if employee is None:
            raise jsonapi.errors.NotFound()
        return jsonapi.response_builder.Relationship(request, resource=employee)

    def patch(self, request):
        employee = Employee.objects\
            .filter(id=request.japi_uri_arguments["id"]).first()
        if employee is None:
            raise jsonapi.errors.NotFound()

        UpdateEmployeeValidator().assert_relationship_object("chief", request.json)

        chief_id = request.json["data"]
        if chief_id is None:
            chief = None
        else:
            chief = Employee.objects.filter(id=chief_id["id"]).first()
            if chief is None:
                raise jsonapi.errors.NotFound()

        employee.chief = chief
        employee.save()
        return jsonapi.response_builder.Relationship(request, resource=employee)


class EmployeeRelatedChief(jsonapi.handler.Handler):

    def get(self, request):
        employee = Employee.objects\
            .filter(id=request.japi_uri_arguments["id"]).first()
        if employee is None:
            raise jsonapi.errors.NotFound()
        return jsonapi.response_builder.Resource(request, data=employee.chief)


def create_api():
    """
    We put the initialisation of our API in this factory function. At this
    point, we create an API instance and register the Employee encoder and all
    handlers.
    """
    api = jsonapi_flask.api.API("/api")

    encoder = EmployeeEncoder()
    includer = EmployeeIncluder()
    api.add_type(encoder, includer)

    api.add_handler(
        handler=EmployeeCollection(), typename=encoder.typename,
        endpoint_type="collection"
    )
    api.add_handler(
        handler=EmployeeResource(), typename=encoder.typename,
        endpoint_type="resource"
    )
    api.add_handler(
        handler=EmployeeRelationshipsChief(), typename=encoder.typename,
        endpoint_type="relationship", relname="chief"
    )
    api.add_handler(
        handler=EmployeeRelatedChief(), typename=encoder.typename,
        endpoint_type="related", relname="chief"
    )
    return api
