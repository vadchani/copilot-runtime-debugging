import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_calculate_bonus(client):
    response = client.get("/employee/bonus")
    assert response.status_code == 200
    assert response.json() == {"bonus": 5000.0}


def test_get_existing_employee(client):
    response = client.get("/employee/101")
    assert response.status_code == 200
    assert response.json() == {"name": "Rahul", "department": "IT"}


def test_get_missing_employee(client):
    response = client.get("/employee/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Employee 999 not found"}


def test_average_salary(client):
    response = client.get(
        "/employee/average-salary",
        params={"total_salary": 150000, "employee_count": 3},
    )
    assert response.status_code == 200
    assert response.json() == {"average_salary": 50000.0}


def test_zero_employee_count(client):
    response = client.get(
        "/employee/average-salary",
        params={"total_salary": 150000, "employee_count": 0},
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Employee count must be greater than zero"
    }


def test_average_salary_defaults(client):
    response = client.get("/employee/average-salary")
    assert response.status_code == 200
    assert response.json() == {"average_salary": 50000.0}


def test_negative_employee_count(client):
    response = client.get("/employee/average-salary", params={"employee_count": -1})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Employee count must be greater than zero"
    }


@pytest.mark.parametrize("salary", ["invalid", "nan", "inf", "-inf", "1e999", "-1"])
def test_invalid_average_salary(client, salary):
    response = client.get("/employee/average-salary", params={"total_salary": salary})
    assert response.status_code == 422


@pytest.mark.parametrize("count", ["invalid", "1.5", str(10**309)])
def test_invalid_employee_count(client, count):
    response = client.get("/employee/average-salary", params={"employee_count": count})
    assert response.status_code == 422


def test_get_second_employee(client):
    response = client.get("/employee/102")
    assert response.status_code == 200
    assert response.json() == {"name": "Priya", "department": "HR"}


def test_invalid_employee_id(client):
    response = client.get("/employee/not-an-id")
    assert response.status_code == 422


@pytest.mark.parametrize("salary, expected", [("50000", 50000.0), ("0", 0.0)])
def test_parse_salary(client, salary, expected):
    response = client.get("/employee/salary", params={"salary": salary})
    assert response.status_code == 200
    assert response.json() == {"salary": expected}


@pytest.mark.parametrize("salary", ["invalid", "", "nan", "inf", "-inf", "1e999", "-1"])
def test_invalid_salary(client, salary):
    response = client.get("/employee/salary", params={"salary": salary})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Salary must be a finite, non-negative number"
    }


def test_existing_employee_attribute(client):
    response = client.get("/employee/attribute", params={"attribute": "name"})
    assert response.status_code == 200
    assert response.json() == {"name": "Rahul"}


@pytest.mark.parametrize("attribute", ["department", "model_dump", "__class__"])
def test_missing_or_internal_employee_attribute(client, attribute):
    response = client.get("/employee/attribute", params={"attribute": attribute})
    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Employee attribute {attribute} not found"
    }


@pytest.mark.parametrize("index, name", [(0, "Rahul"), (1, "Priya")])
def test_existing_employee_index(client, index, name):
    response = client.get(f"/employee/by-index/{index}")
    assert response.status_code == 200
    assert response.json()["name"] == name


@pytest.mark.parametrize("index", [-1, 2, 999])
def test_missing_employee_index(client, index):
    response = client.get(f"/employee/by-index/{index}")
    assert response.status_code == 404
    assert response.json() == {"detail": f"Employee index {index} not found"}


def test_valid_employee_payload(client):
    payload = {"name": "Rahul", "age": 30, "salary": 50000.0}
    response = client.post("/employee/validate", json=payload)
    assert response.status_code == 200
    assert response.json() == payload


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", " "),
        ("age", "invalid"),
        ("age", -1),
        ("salary", "invalid"),
        ("salary", -1),
        ("salary", "nan"),
        ("salary", "inf"),
    ],
)
def test_invalid_employee_payload(client, field, value):
    payload = {"name": "Rahul", "age": 30, "salary": 50000.0}
    payload[field] = value
    response = client.post("/employee/validate", json=payload)
    assert response.status_code == 422
    assert ["body", field] in [error["loc"] for error in response.json()["detail"]]


def test_missing_employee_fields(client):
    response = client.post("/employee/validate", json={})
    assert response.status_code == 422
    assert {error["loc"][-1] for error in response.json()["detail"]} == {
        "name", "age", "salary"
    }


def test_malformed_employee_json(client):
    response = client.post(
        "/employee/validate",
        content="{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "json_invalid"