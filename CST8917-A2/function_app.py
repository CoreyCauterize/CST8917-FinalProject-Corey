import json
import azure.functions as func
import logging
import asyncio
from datetime import timedelta, datetime, timezone

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

REQUIRED_FIELDS = [
    "employee_name",
    "employee_email",
    "amount",
    "category",
    "description",
    "manager_email",
]

VALID_CATEGORIES = {"travel", "meals", "supplies", "equipment", "software", "other"}


def _http_json_response(payload: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload),
        mimetype="application/json",
        status_code=status_code,
    )


def _normalize_manager_decision(payload) -> str:
    if isinstance(payload, dict):
        return str(payload.get("decision", "")).strip().lower()

    if isinstance(payload, str):
        stripped = payload.strip()
        if stripped.startswith("{"):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, dict):
                    return str(parsed.get("decision", "")).strip().lower()
            except json.JSONDecodeError:
                pass

        return stripped.lower()

    return ""


# HTTP starter for the expense approval orchestrationd
@app.route(route="expenses/start", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_expense_workflow(req: func.HttpRequest, client):
    try:
        payload = req.get_json()
    except ValueError:
        return _http_json_response({"error": "Request body must be valid JSON."}, status_code=400)

    instance_id = await client.start_new("expense_approval_orchestrator", client_input=payload)
    logging.info("Started expense approval orchestration with ID = %s", instance_id)

    response = client.create_check_status_response(req, instance_id)
    return response


# Optional status endpoint for easier manual testing
@app.route(route="expenses/{instanceId}/status", methods=["GET"])
@app.durable_client_input(client_name="client")
async def get_expense_workflow_status(req: func.HttpRequest, client):
    instance_id = req.route_params.get("instanceId")
    status = await client.get_status(instance_id)

    if status is None:
        return _http_json_response({"error": f"No orchestration found for instanceId '{instance_id}'."}, status_code=404)

    return _http_json_response(
        {
            "instanceId": status.instance_id,
            "runtimeStatus": str(status.runtime_status),
            "createdTime": status.created_time.isoformat() if status.created_time else None,
            "lastUpdatedTime": status.last_updated_time.isoformat() if status.last_updated_time else None,
            "output": status.output,
            "message": "Workflow is still running." if status.output is None else "Workflow completed.",
            "customStatus": status.custom_status,
        }
    )


# HTTP callback endpoint used by managers to approve/reject
@app.route(route="expenses/{instanceId}/manager-decision", methods=["POST"])
@app.durable_client_input(client_name="client")
async def manager_decision_callback(req: func.HttpRequest, client):
    instance_id = req.route_params.get("instanceId")
    try:
        payload = req.get_json()
    except ValueError:
        return _http_json_response({"error": "Request body must be valid JSON."}, status_code=400)

    decision = _normalize_manager_decision(payload)
    if decision not in {"approved", "rejected"}:
        return _http_json_response(
            {"error": "Decision must be either 'approved' or 'rejected'."},
            status_code=400,
        )

    status = await client.get_status(instance_id)
    if status is None:
        return _http_json_response(
            {"error": f"No orchestration found for instanceId '{instance_id}'."},
            status_code=404,
        )

    runtime_status = str(status.runtime_status)
    if runtime_status in {
        "OrchestrationRuntimeStatus.Completed",
        "OrchestrationRuntimeStatus.Failed",
        "OrchestrationRuntimeStatus.Terminated",
        "OrchestrationRuntimeStatus.Canceled",
    }:
        return _http_json_response(
            {
                "error": "This workflow is already finished and cannot accept a manager decision.",
                "instanceId": instance_id,
                "runtimeStatus": runtime_status,
                "output": status.output,
            },
            status_code=409,
        )

    await client.raise_event(instance_id, "ManagerDecision", payload)

    # Briefly poll so callers can immediately see a non-null output in most cases.
    latest_status = status
    for _ in range(10):
        await asyncio.sleep(0.5)
        latest_status = await client.get_status(instance_id)
        if latest_status and latest_status.output is not None:
            break

    return _http_json_response(
        {
            "message": "Manager decision received.",
            "instanceId": instance_id,
            "decision": decision,
            "runtimeStatus": str(latest_status.runtime_status) if latest_status else None,
            "output": latest_status.output if latest_status else None,
        },
        status_code=202,
    )


# Orchestrator implementing validation, auto-approval, human interaction, timeout, and notification
@app.orchestration_trigger(context_name="context")
def expense_approval_orchestrator(context):
    expense = context.get_input() or {}

    validation = yield context.call_activity("validate_expense_activity", expense)
    if not validation.get("is_valid", False):
        result = yield context.call_activity(
            "build_decision_activity",
            {
                "expense": expense,
                "instance_id": context.instance_id,
                "status": "validation_error",
                "approved": False,
                "escalated": False,
                "reason": "Validation failed.",
                "errors": validation.get("errors", []),
            },
        )
        yield context.call_activity("send_employee_notification_activity", result)
        return result

    amount = float(expense["amount"])
    if amount < 100:
        result = yield context.call_activity(
            "build_decision_activity",
            {
                "expense": expense,
                "instance_id": context.instance_id,
                "status": "approved",
                "approved": True,
                "escalated": False,
                "reason": "Auto-approved because amount is under $100.",
                "errors": [],
            },
        )
        yield context.call_activity("send_employee_notification_activity", result)
        return result

    timeout_seconds = int(expense.get("timeout_seconds", 120))
    manager_decision_task = context.wait_for_external_event("ManagerDecision")
    timeout_at = context.current_utc_datetime + timedelta(seconds=timeout_seconds)
    timeout_task = context.create_timer(timeout_at)

    winner = yield context.task_any([manager_decision_task, timeout_task])

    if winner == manager_decision_task:
        decision_payload = manager_decision_task.result
        decision = _normalize_manager_decision(decision_payload)

        if decision == "approved":
            status = "approved"
            approved = True
            reason = "Manager approved the expense request."
        elif decision == "rejected":
            status = "rejected"
            approved = False
            reason = "Manager rejected the expense request."
        else:
            status = "escalated"
            approved = True
            reason = "Invalid manager decision payload. Auto-approved and escalated."
            escalated = True

        if decision in {"approved", "rejected"}:
            escalated = False
        if not timeout_task.is_completed:
            timeout_task.cancel()
    else:
        status = "escalated"
        approved = True
        escalated = True
        reason = "No manager decision was received before timeout. Auto-approved and escalated."

    result = yield context.call_activity(
        "build_decision_activity",
        {
            "expense": expense,
            "instance_id": context.instance_id,
            "status": status,
            "approved": approved,
            "escalated": escalated,
            "reason": reason,
            "errors": [],
        },
    )
    yield context.call_activity("send_employee_notification_activity", result)
    return result


@app.activity_trigger(input_name="expense")
def validate_expense_activity(expense: dict):
    errors = []

    if not isinstance(expense, dict):
        return {"is_valid": False, "errors": ["Expense payload must be a JSON object."]}

    for field in REQUIRED_FIELDS:
        value = expense.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            errors.append(f"Missing required field: {field}")

    try:
        amount_value = float(expense.get("amount"))
        if amount_value < 0:
            errors.append("Amount must be non-negative.")
    except (TypeError, ValueError):
        errors.append("Amount must be a valid number.")

    category = str(expense.get("category", "")).strip().lower()
    if category not in VALID_CATEGORIES:
        errors.append(
            "Invalid category. Valid categories: travel, meals, supplies, equipment, software, other."
        )

    return {"is_valid": len(errors) == 0, "errors": errors}


@app.activity_trigger(input_name="decision_input")
def build_decision_activity(decision_input: dict):
    expense = decision_input.get("expense", {})
    return {
        "instance_id": decision_input.get("instance_id"),
        "status": decision_input.get("status"),
        "approved": decision_input.get("approved"),
        "escalated": decision_input.get("escalated"),
        "reason": decision_input.get("reason"),
        "errors": decision_input.get("errors", []),
        "expense": expense,
        "processed_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.activity_trigger(input_name="result_payload")
def send_employee_notification_activity(result_payload: dict):
    expense = result_payload.get("expense", {})
    employee_email = expense.get("employee_email", "unknown")
    message = (
        f"Expense outcome for {expense.get('employee_name', 'employee')}: "
        f"status={result_payload.get('status')}, "
        f"escalated={result_payload.get('escalated')}, "
        f"reason={result_payload.get('reason')}"
    )

    # Simulated email send for assignment purposes.
    logging.info("Notify %s -> %s", employee_email, message)
    return {
        "notified": True,
        "to": employee_email,
        "message": message,
    }