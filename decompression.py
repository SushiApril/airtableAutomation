from pyairtable.formulas import match
import json
from compression import connect_to_airtable

def decompress_json(api, base_id, applicant_record):
    """
    Reconstructs and syncs child records from a compressed JSON object stored
    in the given applicant record. This includes:
    - Updating or creating Personal Details and Salary Preferences (1:1)
    - Replacing all associated Work Experience records (1:N)
    
    Skips if JSON is missing or invalid.
    """

    applicant_id = applicant_record["fields"].get("Applicant ID")
    record_id = applicant_record["id"]

    if not applicant_id or "Compressed JSON" not in applicant_record["fields"]:
        print(f"Missing compressed JSON or Applicant ID for {record_id}")
        return

    try:
        data = json.loads(applicant_record["fields"]["Compressed JSON"])
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
        return

    print(f"Decompressing data for Applicant ID: {applicant_id}")

    personal_table = api.table(base_id, "Personal Details")
    salary_table = api.table(base_id, "Salary Preferences")
    work_table = api.table(base_id, "Work Experience")

    upsert_personal_details(personal_table, applicant_id, record_id, data["personal"])
    upsert_salary_preferences(salary_table, applicant_id, record_id, data["salary"])
    sync_work_experience(work_table, applicant_id, record_id, data["experience"])

def upsert_personal_details(personal_table, applicant_id, record_id, personal_data):
    """
    Creates or updates a record in the 'Personal Details' table for the given applicant.
    If a matching record exists based on Applicant ID, it is updated with the new values.
    Otherwise, a new record is created and linked back to the applicant.
    """
    match_formula = match({"Applicant ID": applicant_id})
    existing = personal_table.first(formula=match_formula)

    payload = {
        "Full Name": personal_data.get("name", ""),
        "Email": personal_data.get("email", ""),
        "Location": personal_data.get("location", ""),
        "LinkedIn": personal_data.get("linkedin", ""),
        "Applicant ID": [record_id]
    }

    if existing:
        personal_table.update(existing["id"], payload)
        print("Updated Personal Details")
    else:
        personal_table.create(payload)
        print("Created Personal Details")

def upsert_salary_preferences(salary_table, applicant_id, record_id, salary_data):
    """
    Creates or updates a record in the 'Salary Preferences' table for the given applicant.
    If a matching record exists based on Applicant ID, it is updated with the new salary fields.
    Otherwise, a new record is created and linked to the applicant.
    Logs parsed salary data for debugging purposes.
    """
    match_formula = match({"Applicant ID": applicant_id})
    existing = salary_table.first(formula=match_formula)

    payload = {
        "Preferred Rate": salary_data.get("rate", 0),
        "Minimum Rate": salary_data.get("min_rate", 0),
        "Currency": salary_data.get("currency", ""),
        "Availability (hrs/wk)": salary_data.get("availability", 0),
        "Applicant ID": [record_id]
    }
    print("Raw salary data from JSON:", salary_data)
    print("Parsed availability value:", salary_data.get("availability"))

    if existing:
        salary_table.update(existing["id"], payload)
        print("Updated Salary Preferences")
    else:
        salary_table.create(payload)
        print("Created Salary Preferences")

def sync_work_experience(work_table, applicant_id, record_id, experience_list):
    """
    Replaces all existing 'Work Experience' records for the given applicant.
    Deletes all current entries linked by Applicant ID, then creates new entries
    based on the provided experience list from the compressed JSON.
    Ensures correct linkage to the applicant record via record ID.
    """

    existing_records = work_table.all(formula=match({"Applicant ID": applicant_id}))

    for rec in existing_records:
        work_table.delete(rec["id"])
    print(f"Deleted {len(existing_records)} existing work entries")

    for entry in experience_list:
        work_table.create({
            "Company": entry.get("company", ""),
            "Title": entry.get("title", ""),
            "Start": entry.get("start", ""),
            "End": entry.get("end", ""),
            "Technologies": entry.get("technologies", []),
            "Applicant ID": [record_id]
        })
    print(f"Created {len(experience_list)} new work entries")


def run_decompression(applicant_id="A001"):
    """
    Runs the full decompression workflow for a given applicant ID.
    - Connects to Airtable
    - Retrieves the applicant record from the 'Applicants' table
    - Calls the decompression function to restore all child table data from JSON
    Skips execution if the applicant is not found.
    """

    api, base_id = connect_to_airtable()
    applicants_table = api.table(base_id, "Applicants")
    record = applicants_table.first(formula=match({"Applicant ID": applicant_id}))

    if not record:
        print(f"Applicant ID {applicant_id} not found.")
        return

    decompress_json(api, base_id, record)

if __name__ == "__main__":
    run_decompression(applicant_id="2")
