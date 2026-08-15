import json

import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

VALID_CATEGORIES = {
    "travel",
    "meals",
    "supplies",
    "equipment",
    "software",
    "other"
}

REQUIRED_FIELDS = [
    "employeeName",
    "employeeEmail",
    "amount",
    "category",
    "description",
    "managerEmail"
]


@app.route(route="ValidateExpense")
def ValidateExpense(req: func.HttpRequest) -> func.HttpResponse:
    try:
        expense = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({
                "valid": False,
                "reason": "Request body must contain valid JSON"
            }),
            status_code=400,
            mimetype="application/json"
        )

    # Check required fields
    missing_fields = []

    for field in REQUIRED_FIELDS:
        if field not in expense or expense[field] is None:
            missing_fields.append(field)
        elif isinstance(expense[field], str) and not expense[field].strip():
            missing_fields.append(field)

    if missing_fields:
        return func.HttpResponse(
            json.dumps({
                "valid": False,
                "reason": "Missing required fields",
                "missingFields": missing_fields
            }),
            status_code=200,
            mimetype="application/json"
        )

    # Validate amount
    try:
        amount = float(expense["amount"])

        if amount < 0:
            return func.HttpResponse(
                json.dumps({
                    "valid": False,
                    "reason": "Expense amount cannot be negative"
                }),
                status_code=200,
                mimetype="application/json"
            )

    except (ValueError, TypeError):
        return func.HttpResponse(
            json.dumps({
                "valid": False,
                "reason": "Expense amount must be a number"
            }),
            status_code=200,
            mimetype="application/json"
        )

    # Validate category
    category = str(expense["category"]).strip().lower()

    if category not in VALID_CATEGORIES:
        return func.HttpResponse(
            json.dumps({
                "valid": False,
                "reason": "Invalid expense category",
                "category": category,
                "validCategories": sorted(VALID_CATEGORIES)
            }),
            status_code=200,
            mimetype="application/json"
        )

    # Everything is valid
    return func.HttpResponse(
        json.dumps({
            "valid": True,
            "reason": "",
            "amount": amount,
            "category": category
        }),
        status_code=200,
        mimetype="application/json"
    )