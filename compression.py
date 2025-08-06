import requests
import json
import os
from datetime import datetime
from pyairtable import Api
from dotenv import load_dotenv
from pyairtable.formulas import match

def connect_to_airtable():
    """
    Loads environment variables and returns an Airtable API object and base ID.
    Expects AIRTABLE_API_TOKEN and AIRTABLE_BASE_ID in the .env file.
    """
    load_dotenv()
    api_key = os.getenv("AIRTABLE_API_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID") or os.getenv("base")

    if not api_key:
        raise ValueError("API token not found. Make sure AIRTABLE_API_TOKEN is set in your .env file.")
    if not base_id:
        raise ValueError("Base ID not found. Make sure AIRTABLE_BASE_ID (or base) is set in your .env file.")

    api = Api(api_key)
    return api, base_id

""" Retrieves a single applicant record from the 'Applicants' table
    by matching the provided Applicant ID. Returns the full record
    if found, otherwise returns None.
    """

def get_applicant_by_id(api, base_id, applicant_id):
    applicants = api.table(base_id, "Applicants").all()
    for record in applicants:
        if record["fields"].get("Applicant ID") == applicant_id:
            print(f"Found applicant {applicant_id}: {record['id']}")
            return record
    print(f"{applicant_id} not found.")
    return None


def get_child_records(api, base_id, applicant_id):
    """
    Retrieves child records linked to a given applicant from:
    - Personal Details (1:1)
    - Salary Preferences (1:1)
    - Work Experience (1:N)

    Returns a tuple: (personal, salary, work_records)
    """

    personal = api.table(base_id, "Personal Details").first(formula=match({"Applicant ID": applicant_id}))
    salary = api.table(base_id, "Salary Preferences").first(formula=match({"Applicant ID": applicant_id}))
    work_records = api.table(base_id, "Work Experience").all(formula=match({"Applicant ID": applicant_id}))

    print("Personal:", personal["fields"].get("Full Name"))
    print("Salary:", salary["fields"].get("Preferred Rate"))
    print("Work Experience Entries:", len(work_records))

    return personal, salary, work_records


def build_compressed_json(personal, salary, work_records):
    """
    Constructs a structured JSON object from an applicant's child records:
    - Personal details
    - Salary preferences
    - Work experience list

    Returns a dictionary that matches the compressed JSON format required by the application.
    """
    return {
        "personal": {
            "name": personal["fields"].get("Full Name", ""),
            "email": personal["fields"].get("Email", ""),
            "location": personal["fields"].get("Location", ""),
            "linkedin": personal["fields"].get("LinkedIn", "")
        },
        "experience": [
            {
                "company": wr["fields"].get("Company", ""),
                "title": wr["fields"].get("Title", ""),
                "start": wr["fields"].get("Start", ""),
                "end": wr["fields"].get("End", ""),
                "technologies": wr["fields"].get("Technologies", [])
            } for wr in work_records
        ],
        "salary": {
            "rate": salary["fields"].get("Preferred Rate", 0),
            "min_rate": salary["fields"].get("Minimum Rate", 0),
            "currency": salary["fields"].get("Currency", ""),
            "availability": salary["fields"].get("Availability (hrs/wk)", 0)
        }
    }


def save_compressed_json(api, base_id, applicant_record_id, compressed_data):
    """
    Saves the provided compressed JSON object to the 'Compressed JSON' field
    of the specified applicant record in the 'Applicants' table.
    """
    applicants_table = api.table(base_id, "Applicants")
    json_string = json.dumps(compressed_data, indent=2)

    applicants_table.update(applicant_record_id, {
        "Compressed JSON": json_string
    })

    print("Compressed JSON saved to Airtable.")


def run_compression(applicant_id="A001"):
    """
    Executes the full compression flow for a given applicant:
    - Connects to Airtable
    - Retrieves applicant and related child records
    - Builds a compressed JSON structure
    - Prints and saves the JSON back to the applicant's record
    """
    api, base_id = connect_to_airtable()

    applicant_record = get_applicant_by_id(api, base_id, applicant_id)
    if not applicant_record:
        return

    personal, salary, work_records = get_child_records(api, base_id, applicant_id)

    compressed_json = build_compressed_json(personal, salary, work_records)

    print(json.dumps(compressed_json, indent=2))

    save_compressed_json(api, base_id, applicant_record["id"], compressed_json)

if __name__ == "__main__":
    run_compression(applicant_id="2")
