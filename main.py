from math import isfinite

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="GitHub Copilot Runtime Debugging Lab")

EMPLOYEES = {
    101: {"name": "Rahul", "department": "IT"},
    102: {"name": "Priya", "department": "HR"},
}


class Employee(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    age: int = Field(ge=0)
    salary: float = Field(ge=0, allow_inf_nan=False)


@app.get("/employee/bonus")
def calculate_bonus():
    salary = 50000.0
    bonus = salary * 0.10

    return {"bonus": bonus}


@app.get("/employee/average-salary")
def calculate_average_salary(
    total_salary: float = Query(default=150000, ge=0, allow_inf_nan=False),
    employee_count: int = Query(default=3, le=2_147_483_647),
):
    if employee_count <= 0:
        raise HTTPException(
            status_code=400,
            detail="Employee count must be greater than zero",
        )

    average = total_salary / employee_count

    return {"average_salary": average}


@app.get("/employee/salary")
def parse_salary(salary: str):
    try:
        numeric_salary = float(salary)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Salary must be a finite, non-negative number",
        ) from None

    if not isfinite(numeric_salary) or numeric_salary < 0:
        raise HTTPException(
            status_code=400,
            detail="Salary must be a finite, non-negative number",
        )

    return {"salary": numeric_salary}


@app.get("/employee/attribute")
def get_employee_attribute(attribute: str):
    if attribute not in Employee.model_fields:
        raise HTTPException(
            status_code=404,
            detail=f"Employee attribute {attribute} not found",
        )

    employee = Employee(name="Rahul", age=30, salary=50000)
    return {attribute: getattr(employee, attribute)}


@app.get("/employee/by-index/{index}")
def get_employee_by_index(index: int):
    employees = list(EMPLOYEES.values())
    if index < 0 or index >= len(employees):
        raise HTTPException(
            status_code=404,
            detail=f"Employee index {index} not found",
        )

    return employees[index]


@app.post("/employee/validate", response_model=Employee)
def validate_employee(employee: Employee):
    return employee


@app.get("/employee/{employee_id}")
def get_employee(employee_id: int):
    employee = EMPLOYEES.get(employee_id)
    if employee is None:
        raise HTTPException(
            status_code=404,
            detail=f"Employee {employee_id} not found",
        )

    return employee


@app.get("/")
def home():
    return {"message": "Runtime Debugging Lab"}
