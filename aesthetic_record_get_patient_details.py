import json
import urllib.request


def run(headers, user_input):
    """Fetch detailed patient/client information from Aesthetic Record."""
    # Validate input
    patient_id = user_input.get("patient_id")
    if not patient_id:
        return {'status_code': 400, 'body': {'error': 'patient_id is required'}}

    try:
        patient = _fetch_patient(headers, patient_id)
    except Exception as e:
        error_msg = str(e)
        if '401' in error_msg:
            return {'status_code': 401, 'body': {'error': 'Authentication required'}}
        return {'status_code': 500, 'body': {'error': error_msg}}

    # Fetch payment methods
    payments_on_file = []
    try:
        payments_on_file = _fetch_payment_methods(headers, patient_id)
    except Exception:
        pass

    # Fallback to card_on_files from patient data if stripe call didn't return data
    if not payments_on_file and patient.get('card_on_files'):
        for card in patient['card_on_files']:
            payments_on_file.append({
                'brand': card.get('card_type', 'unknown'),
                'last4': card.get('card_number', '****')[-4:] if card.get('card_number') else '****'
            })

    # Calculate age from DOB
    age = None
    dob = patient.get('date_of_birth')
    if dob:
        try:
            from datetime import datetime, date
            birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except Exception:
            pass

    # Collect phone numbers (up to 4)
    phones = []
    for i in ['', '_2', '_3', '_4']:
        phone = patient.get(f'phoneNumber{i}')
        if phone:
            phones.append(phone)

    # Collect emails (up to 4)
    emails = []
    for i in ['', '_2', '_3', '_4']:
        email = patient.get(f'email{i}')
        if email:
            emails.append(email)

    # Get primary clinic name
    primary_clinic = None
    clinics = patient.get('clinics', [])
    if clinics:
        primary_clinic = clinics[0].get('clinic_name')

    # Get last visit date
    last_visit = None
    last_appointment = patient.get('last_appointment', [])
    if last_appointment and len(last_appointment) > 0:
        appt = last_appointment[0]
        if isinstance(appt, dict):
            last_visit = appt.get('date') or appt.get('format_date')
        else:
            last_visit = appt
    if not last_visit:
        last_visit = patient.get('last_procedure_date')

    # Get membership program
    membership_program = None
    membership_sub = patient.get('patient_membership_subscription', [])
    if membership_sub and len(membership_sub) > 0:
        sub = membership_sub[0]
        membership_program = sub.get('membership_name') or sub.get('subscription_name') or sub.get('name') or sub.get('membership_tier_name')
    if not membership_program:
        fallback_name = patient.get('membership_subscription_name')
        if fallback_name and membership_sub:
            membership_program = fallback_name

    # Get insurance/carrier info
    insurance = patient.get('patient_insurence') or {}
    carrier = insurance.get('carrier_name') if isinstance(insurance, dict) else None
    prescription_card = insurance.get('prescription_card') if isinstance(insurance, dict) else None

    # Build response
    result = {
        'first_name': patient.get('firstname'),
        'middle_name': patient.get('middlename'),
        'last_name': patient.get('lastname'),
        'date_of_birth': dob,
        'age': age,
        'address': {
            'line_1': patient.get('address_line_1'),
            'line_2': patient.get('address_line_2'),
            'city': patient.get('city'),
            'state': patient.get('state'),
            'zip': patient.get('pincode'),
            'country': patient.get('country')
        },
        'phones': phones,
        'emails': emails,
        'patient_creation_date': patient.get('created'),
        'primary_clinic': primary_clinic,
        'patient_portal': {
            'invited': bool(patient.get('invited_portal')),
            'accepted': bool(patient.get('access_portal'))
        },
        'communication_consent': {
            'call': not bool(patient.get('do_not_call')),
            'sms': not bool(patient.get('do_not_sms')),
            'email': not bool(patient.get('do_not_email'))
        },
        'last_visit': last_visit,
        'membership_program': membership_program,
        'total_sales': patient.get('total_sale_relationship'),
        'payments_on_file': payments_on_file,
        'loyalty_programs': {
            'alle': {
                'enrolled': bool(patient.get('alle_status')),
                'account_id': patient.get('alle_id')
            },
            'aspire': {
                'enrolled': bool(patient.get('aspire_status')),
                'account_id': patient.get('aspire_id')
            },
            'evolus': {
                'enrolled': bool(patient.get('evolus_status')),
                'account_id': patient.get('evolus_id')
            },
            'xperience': {
                'enrolled': bool(patient.get('xperience_status')),
                'account_id': patient.get('xperience_id')
            },
            'repeatmd': {
                'enrolled': bool(patient.get('repeatmd_status')),
                'account_id': patient.get('repeatmd_id')
            }
        },
        'additional_contact': {
            'name': patient.get('emergency_contact_name'),
            'phone': patient.get('emergency_contact_number')
        },
        'referral_source': patient.get('referral_source'),
        'referral_source_subcategory': patient.get('referral_source_subcategory'),
        'carrier': carrier,
        'prescription_card': prescription_card
    }

    return {'status_code': 200, 'body': result}

# === PRIVATE ===

def _fetch_patient(headers, patient_id):
    """Fetch patient details from the API."""
    base_url = BASE_URL
    patient_url = f"{base_url}/api/clients/{patient_id}?scopes=cardOnFiles,patientInsurence"
    req = urllib.request.Request(
        patient_url,
        headers={**headers, "Accept": "*/*"},
        method="GET"
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read().decode())

    if data.get('status') == 'error' and 'auth' in str(data.get('message', '')).lower():
        raise Exception('401 - Session expired')

    return data.get('data', {})


def _fetch_payment_methods(headers, patient_id):
    """Fetch saved payment methods from Stripe endpoint."""
    base_url = BASE_URL
    payload = json.dumps({"patient_id": int(patient_id)}).encode('utf-8')
    req = urllib.request.Request(
        f"{base_url}/api/stripe/list-payment-methods",
        data=payload,
        headers={**headers, "Content-Type": "application/json;charset=UTF-8", "Accept": "*/*"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payment_data = json.loads(response.read().decode())

    payments = []
    if payment_data.get('data'):
        for pm in payment_data['data']:
            card = pm.get('card', {})
            payments.append({
                'brand': card.get('brand', 'unknown'),
                'last4': card.get('last4', '****')
            })
    return payments
