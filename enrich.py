import json
from compression import connect_to_airtable
from pyairtable.formulas import match
from llm import call_llm

def run_llm_enrichment(applicant_id="A001"):
    """
    Executes the LLM enrichment process for a given applicant:
    - Retrieves the applicant record and its compressed JSON
    - Sends the JSON to the LLM for qualitative analysis
    - Parses and saves the summary, score, and follow-up suggestions back to Airtable
    Handles missing records, invalid JSON, and prints LLM output for review.
    """

    api, base_id = connect_to_airtable()
    table = api.table(base_id, "Applicants")
    record = table.first(formula=match({"Applicant ID": applicant_id}))

    if not record:
        print("Applicant not found.")
        return

    json_str = record["fields"].get("Compressed JSON")
    if not json_str:
        print("No Compressed JSON found.")
        return

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        print("Invalid JSON format.")
        return

    result = call_llm(data)
    print("LLM Output:", result)

    table.update(record["id"], {
        "LLM Summary": result["summary"],
        "LLM Score": int(result["score"]),
        "LLM Followup": result["followups"]
    })

    print("LLM enrichment saved to Airtable.")

if __name__ == "__main__":
    run_llm_enrichment("2")
