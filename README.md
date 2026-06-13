# Aesthetic Record Unofficial API

Unofficial Python integrations for Aesthetic Record.

## Integrations

- `aesthetic_record_get_appointments.py` - `get_appointments` (28,543 live events).
- `aesthetic_record_list_patients.py` - `list_patients` (28,374 live events).
- `aesthetic_record_get_patient_details.py` - `get_patient_details` (13,877 live events).
- `aesthetic_record_list_invoices.py` - `list_invoices` (2,552 live events).

## Usage

Each file exposes a `run(input, context)` entrypoint. The runtime is expected to provide:

- `input`: integration-specific request fields.
- `context["headers"]`: authenticated request headers when required.
- `context["base_url"]`: the platform base URL when overriding the default.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Info

This unofficial API is built by [Integuru.ai](https://integuru.ai/).

For custom requests or hosted authentication, contact richard@taiki.online.

See the [complete list of APIs by Integuru](https://github.com/Integuru-AI/APIs-by-Integuru).
