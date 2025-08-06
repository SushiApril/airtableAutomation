import json
from compression import connect_to_airtable, get_applicant_by_id
from pyairtable.formulas import match

TIER_1_COMPANIES = {"Google", "Meta", "OpenAI", "Microsoft", "Apple", "Amazon"}
APPROVED_COUNTRIES = {"US", "United States", "UK", "United Kingdom", "Canada", "Germany", "India"}

def evaluate_shortlist(data):
    reasons = []

    # Check experience
    worked_tier1 = any(
        any(tier in (exp.get("company") or "") for tier in TIER_1_COMPANIES)
        for exp in data.get("experience", [])
    )
    total_experience = len(data.get("experience", []))  # crude assumption

    if worked_tier1:
        reasons.append("Worked at a Tier-1 company")
    elif total_experience >= 4:
        reasons.append("Has 4+ work experiences")

    # Check compensation
    if data["salary"].get("rate", 999) <= 100 and data["salary"].get("availability", 0) >= 20:
        reasons.append("Compensation and availability are acceptable")

    # Check location
    location = (data.get("personal", {}).get("location") or "").strip()
    if any(country in location for country in APPROVED_COUNTRIES):
        reasons.append(f"Location eligible ({location})")

    passed = len(reasons) >= 3  # all three categories met
    return passed, "; ".join(reasons) if passed else ""

def create_shortlist_record(api, base_id, applicant_record, json_str, reason):
    table = api.table(base_id, "Shortlisted Leads")
    table.create({
        "Applicant": [applicant_record["id"]],
        "Compressed JSON": json_str,
        "Score Reason": reason
    })
    print(f"Shortlisted {applicant_record['fields'].get('Applicant ID')}")



def run_shortlisting(applicant_id="A001"):
    api, base_id = connect_to_airtable()
    applicants_table = api.table(base_id, "Applicants")

    record = applicants_table.first(formula=match({"Applicant ID": applicant_id}))
    if not record:
        print(f"No record found for {applicant_id}")
        return

    json_str = record["fields"].get("Compressed JSON")
    if not json_str:
        print("No compressed JSON found.")
        return

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
        return

    passed, reason = evaluate_shortlist(data)
    if passed:
        create_shortlist_record(api, base_id, record, json_str, reason)
    else:
        print(f"Applicant {applicant_id} did not pass shortlist criteria.")

if __name__ == "__main__":
    run_shortlisting(applicant_id="2")
