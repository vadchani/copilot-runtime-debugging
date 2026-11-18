# FastAPI Runtime Debugging Lab

## Run

From this project directory:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs to execute requests interactively.
In another terminal, activate the environment and run `pytest -v`.
The suite has 46 cases, including the five original regression tests.
`pytest.ini` makes project imports work with both `pytest` and `python -m pytest`.

## Reproduce and Understand

The original bonus request raised `TypeError` and employee 999 raised `KeyError`.
The original average request returned 422 because the earlier dynamic employee
route matched `average-salary` as an employee ID. Calling the original average
function directly reproduced `ZeroDivisionError`. Named routes now precede the
dynamic route, so requests reach the correct handler.

The four additional challenges were reproduced as isolated Python operations
before adding their safe API endpoints. To repeat all seven exceptions without
breaking the fixed application, run this separate demonstration:

```bash
python - <<'PY'
from main import Employee

examples = {
    "TypeError": lambda: "50000" * 0.10,
    "KeyError": lambda: {101: "Rahul", 102: "Priya"}[999],
    "ZeroDivisionError": lambda: 150000 / 0,
    "ValueError": lambda: float("invalid"),
    "AttributeError": lambda: getattr(
        Employee(name="Rahul", age=30, salary=50000), "department"
    ),
    "IndexError": lambda: [101, 102][999],
    "ValidationError": lambda: Employee(
        name="Rahul", age="invalid", salary="invalid"
    ),
}
for expected, operation in examples.items():
    try:
        operation()
    except Exception as error:
        print(f"{expected}: {type(error).__name__}: {error}")
PY
```

The broad catch above is only for demonstrating independent failures. API
handlers use validation, guards, and narrowly scoped exception handling.

| Exception | Incorrect operation and cause | Applied fix |
| --- | --- | --- |
| TypeError | `salary * 0.10` with a string salary; strings support integer repetition, not float multiplication | Change `salary = "50000"` to `salary = 50000.0` |
| KeyError | `employees[employee_id]` raises for absent keys | Use `.get()`, which returns `None` for a missing key, and raise HTTP 404 |
| ZeroDivisionError | `total_salary / employee_count` with zero count has no defined quotient | Check non-positive counts before dividing and raise HTTP 400 |
| ValueError | `float("invalid")` cannot parse nonnumeric text | Catch conversion errors; reject negative or non-finite values with HTTP 400 |
| AttributeError | The employee model has no `department` attribute | Allow only declared model fields; return HTTP 404 for other names |
| IndexError | Index 999 is outside a two-element list | Check lower and upper bounds before indexing; return HTTP 404 |
| ValidationError | Invalid JSON field values fail Pydantic model validation | Accept a typed request body and let FastAPI return structured HTTP 422 errors |

## Validate the Original Fixes

Use these URLs with GET requests:

| Path | Status | Response |
| --- | --- | --- |
| `/employee/bonus` | 200 | `{"bonus": 5000.0}` |
| `/employee/101` | 200 | `{"name": "Rahul", "department": "IT"}` |
| `/employee/999` | 404 | `{"detail": "Employee 999 not found"}` |
| `/employee/average-salary?total_salary=150000&employee_count=3` | 200 | `{"average_salary": 50000.0}` |
| `/employee/average-salary?total_salary=150000&employee_count=0` | 400 | `{"detail": "Employee count must be greater than zero"}` |

Negative employee counts also return 400. Invalid types, negative total salaries,
non-finite totals, and counts above 2,147,483,647 return 422. The count limit
prevents unbounded integers from overflowing during floating-point division.

## Validate the Additional Challenges

| Request | Status | Result |
| --- | --- | --- |
| `GET /employee/salary?salary=50000` | 200 | `{"salary": 50000.0}` |
| `GET /employee/salary?salary=invalid` | 400 | Salary must be a finite, non-negative number |
| `GET /employee/attribute?attribute=name` | 200 | `{"name": "Rahul"}` |
| `GET /employee/attribute?attribute=department` | 404 | Employee attribute department not found |
| `GET /employee/by-index/0` | 200 | Rahul's record |
| `GET /employee/by-index/999` | 404 | Employee index 999 not found |

POST valid and invalid employee JSON:

```bash
curl -i http://127.0.0.1:8000/employee/validate \
  -H 'Content-Type: application/json' \
  -d '{"name":"Rahul","age":30,"salary":50000}'

curl -i http://127.0.0.1:8000/employee/validate \
  -H 'Content-Type: application/json' \
  -d '{"name":"Rahul","age":"invalid","salary":"invalid"}'
```

The first returns 200 with validated data; the second returns 422 with errors
identifying the invalid fields. This endpoint validates only; it does not save
employees. Blank names, negative ages/salaries, missing fields, non-finite
salaries, and malformed JSON are covered by tests.

## Final Review

- All three original exceptions are resolved for the exercised inputs.
- Static routes are tested through HTTP, guarding against route-order regressions.
- Missing employees, fields, and indexes return 404; invalid salary conversions
  and non-positive counts return 400; request validation failures return 422.
- Attribute lookup excludes methods and internal attributes. Index lookup rejects
  negative indexes rather than accidentally returning the last employee.
- No broad API exception handler hides programming errors. FastAPI handles request
  validation errors; direct invalid `Employee(...)` construction still correctly
  raises Pydantic `ValidationError` in Python.
- Tests cover successful calls, failure paths, defaults, both sample employees,
  invalid types, bounds, malformed JSON, and non-finite numeric values.
- The installed TestClient emits an `httpx` deprecation warning recommending
  `httpx2`; tests pass. Test a compatible dependency upgrade and pin versions
  before using this lab as a maintained service.
- Production improvements: use `Decimal` with a defined rounding policy for money,
  persistent storage and stable index ordering, response models for the remaining
  endpoints, authentication/authorization, and logging. The current sample data
  and salary calculations are teaching examples, not a payroll implementation.