from curl_cffi import requests

def run(headers, user_input):
    """Fetch appointments for a given date range, optionally filtered by provider and clinic."""
    # Validate required inputs
    start = user_input.get("start")
    end = user_input.get("end")

    if not start:
        return {'status_code': 400, 'body': {'error': 'start date is required'}}
    if not end:
        return {'status_code': 400, 'body': {'error': 'end date is required'}}

    # Build payload
    payload = {
        "start": start,
        "end": end
    }

    # Add optional filters
    if user_input.get("provider_id"):
        payload["provider_id"] = user_input["provider_id"]
    if user_input.get("clinic_id"):
        payload["clinic_id"] = user_input["clinic_id"]

    try:
        result = _call_api(payload, headers)
        return result
    except Exception as e:
        return {'status_code': 500, 'body': {'error': str(e)}}

# === PRIVATE ===

def _call_api(payload, headers):
    """Make the appointment API request."""
    base_url = BASE_URL

    response = requests.post(
        f"{base_url}/api/appointment",
        json=payload,
        headers={
            **headers,
            "Content-Type": "application/json;charset=UTF-8"
        },
        impersonate="chrome131",
        timeout=30
    )

    # Check for session expiration (login redirect or auth error)
    if response.status_code == 401:
        return {'status_code': 401, 'body': {'error': 'Session expired'}}

    # Check for redirect to login page
    if response.status_code == 200:
        try:
            result = response.json()
            # Check if response indicates auth failure
            if isinstance(result, dict) and result.get("error") == "Unauthenticated":
                return {'status_code': 401, 'body': {'error': 'Session expired'}}
            return {'status_code': 200, 'body': result}
        except:
            # If response is not JSON, might be login page redirect
            if "login" in response.text.lower():
                return {'status_code': 401, 'body': {'error': 'Session expired'}}
            return {'status_code': response.status_code, 'body': {'error': 'Invalid response format'}}

    return {'status_code': response.status_code, 'body': response.text}
