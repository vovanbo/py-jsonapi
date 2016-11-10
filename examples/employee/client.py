#!/usr/bin/env python3

import json
import requests
from pprint import pprint


employee_uri = "http://localhost:5000/api/Employee"

jsonapi_headers = {
    "content-type": "application/vnd.api+json",
    "accept-type": "application/vnd.api+json"
}


def create_employee(name, chief_id=None):
    """
    Creates a new employee.
    """
    d = {
        "data": {
            "type": "Employee",
            "attributes": {
                "name": name
            },
            "relationships": {
                "chief": {
                    "data": {"type": "Employee", "id": chief_id} if chief_id else None
                }
            }
        }
    }
    r = requests.post(
        employee_uri, headers=jsonapi_headers, data=json.dumps(d)
    )
    return r.json()


def update_employee(employee_id, **kargs):
    """
    Updates an existing employee.

    :arg employee_id:
        The id of the targeted employee
    :arg str name:
        The new name of the employee
    :arg chief_id:
        The id of the new chief
    """
    d = {
        "data": {
            "type": "Employee",
            "id": employee_id,
            "attributes": {},
            "relationships": {}
        }
    }

    if "name" in kargs:
        d["data"]["attributes"]["name"] = kargs["name"]

    if "chief_id" in kargs and kargs["chief_id"] is None:
        d["data"]["relationships"]["chief"] = {
            "data": None
        }
    elif "chief_id" in kargs:
        d["data"]["relationships"]["chief"] = {
            "data": {"type": "Employee", "id": kargs["chief_id"]}
        }

    r = requests.patch(
        employee_uri + "/" + employee_id, headers=jsonapi_headers,
        data=json.dumps(d)
    )
    return r.json()


def delete_employee(employee_id):
    """
    Deletes an employee.
    """
    r = requests.delete(
        employee_uri + "/" + employee_id,
        headers=jsonapi_headers
    )
    r.raise_for_status()
    return None


def update_chief_relationship(employee_id, chief_id):
    """
    Updates the chief relationship of an employee.
    """
    if chief_id is None:
        d = {"data": None}
    else:
        d = {"data": {"type": "Employee", "id": chief_id}}

    r = requests.patch(
        employee_uri + "/" + employee_id + "/relationships/chief" ,
        headers=jsonapi_headers,
        data=json.dumps(d)
    )
    return r.json()


if __name__ == "__main__":
    # Create some new employees
    mr_burns = create_employee("Mr. Burns", None)
    pprint(mr_burns)

    mr_smithers = create_employee("Waylon Smithers", mr_burns["data"]["id"])
    pprint(mr_smithers)

    homer = create_employee("Homer Simpsons", mr_smithers["data"]["id"])
    pprint(homer)

    # We wrote Homer's name wrong.
    homer = update_employee(homer["data"]["id"], name="Homer Simpson")
    pprint(homer)

    # Ups, Mr. Smithers died.
    delete_employee(mr_smithers["data"]["id"])

    homer_chief = update_chief_relationship(
        homer["data"]["id"], mr_burns["data"]["id"]
    )
    pprint(homer_chief)
