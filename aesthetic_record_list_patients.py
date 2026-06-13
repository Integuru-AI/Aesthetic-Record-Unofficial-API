import json
import urllib.request
import urllib.parse


def run(headers, user_input):
    """List all patients/customers with optional filtering and pagination."""

    # Build query parameters
    params = {
        "page": user_input.get("page", 1),
        "pagesize": user_input.get("pagesize", 20),
    }

    # Sort order defaults to descending
    params["sortorder"] = user_input.get("sortorder", "desc")

    # Optional parameters
    if user_input.get("sortby"):
        params["sortby"] = user_input["sortby"]

    if user_input.get("term"):
        params["term"] = user_input["term"]

    if user_input.get("letter_key"):
        params["letter_key"] = user_input["letter_key"]

    if user_input.get("filter_id"):
        params["filter_id"] = user_input["filter_id"]

    try:
        result = _call_api(params, headers)
        return {"status_code": 200, "body": result}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"status_code": 401, "body": {"error": "Authentication failed"}}
        return {"status_code": e.code, "body": {"error": str(e)}}
    except Exception as e:
        return {"status_code": 500, "body": {"error": str(e)}}

# === PRIVATE ===

def _call_api(params, headers):
    """Fetch clients list from API."""
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/api/clients?{query_string}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            raise Exception("Session expired")
        return json.loads(response.read().decode())
