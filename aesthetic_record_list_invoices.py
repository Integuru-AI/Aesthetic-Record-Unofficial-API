from curl_cffi import requests


def run(headers, user_input):
    """List invoices within a date range with optional filters."""
    # Required fields
    from_date = user_input.get("from_date")
    to_date = user_input.get("to_date")

    if not from_date:
        return {"status_code": 400, "body": {"error": "from_date is required"}}
    if not to_date:
        return {"status_code": 400, "body": {"error": "to_date is required"}}

    # Optional filters
    clinic_id = user_input.get("clinic_id", [])
    user_id = user_input.get("user_id", [])
    invoice_status = user_input.get("invoice_status", [])
    search_key = user_input.get("search_key", "")
    page_number = user_input.get("page_number", 1)

    # Build request payload
    payload = {
        "fromDate": from_date,
        "toDate": to_date,
        "clinic_id": clinic_id if clinic_id else [],
        "user_id": user_id if user_id else [],
        "invoice_status": invoice_status if invoice_status else [],
        "search_key": search_key,
        "page_number": page_number,
    }

    try:
        result = _call_api(payload, headers)
        return result
    except Exception as e:
        return {"status_code": 500, "body": {"error": str(e)}}


# === PRIVATE ===


def _call_api(payload, headers):
    """Make the API request to fetch invoices."""
    response = requests.post(
        f"{BASE_URL}/api/sales/invoices",
        json=payload,
        headers={
            **headers,
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "*/*",
        },
        impersonate="chrome131",
        timeout=30,
    )

    # Check for auth failure (login redirect or 401)
    if response.status_code == 401:
        return {"status_code": 401, "body": {"error": "Authentication expired"}}

    # Check for redirect to login page
    if response.status_code == 200:
        try:
            result = response.json()
            # Check if response indicates auth failure
            if isinstance(result, dict) and result.get("redirect") == "/login":
                return {"status_code": 401, "body": {"error": "Session expired"}}
            return {"status_code": 200, "body": result}
        except Exception:
            # If response is not JSON, check if it's a login page
            if "/login" in response.text or "Sign In" in response.text:
                return {"status_code": 401, "body": {"error": "Session expired"}}
            return {
                "status_code": response.status_code,
                "body": {"error": "Invalid response format", "raw": response.text[:500]},
            }

    return {"status_code": response.status_code, "body": {"error": response.text}}
