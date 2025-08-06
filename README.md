# Mercor Mini-Interview Project: Airtable Multi-Table Form + JSON Automation

## Overview

This project implements a structured Airtable-based application system with Python-driven automation for JSON compression/decompression, shortlisting logic, and LLM enrichment.

---

## Airtable Schema

### Main Tables

| Table               | Description                                      |
|---------------------|--------------------------------------------------|
| `Applicants`        | Holds applicant metadata, compressed JSON, and LLM outputs |
| `Personal Details`  | One-to-one child of `Applicants`                 |
| `Work Experience`   | One-to-many child of `Applicants`                |
| `Salary Preferences`| One-to-one child of `Applicants`                 |
| `Shortlisted Leads` | Auto-generated for shortlisted applicants        |

### Required Fields

#### `Applicants` Table

- `Applicant ID` (Primary or Text)
- `Compressed JSON` (Long Text)
- `LLM Summary`, `LLM Score`, `LLM Followup` (for Step 6)

#### `Shortlisted Leads` Table

- `Applicant` (Linked Record to Applicants)
- `Compressed JSON` (copied)
- `Score Reason` (text)
- `Created At` (auto-generated)

---

## Functional Components

### Step 1–2: Form + Base Setup

- Three Airtable forms created for Personal Details, Work Experience, and Salary Preferences
- Each form captures and links to `Applicant ID` manually

### Step 3: JSON Compression

- `run_compression(applicant_id)`:
  - Pulls child table records
  - Builds structured JSON
  - Saves it to `Compressed JSON` field

### Step 4: JSON Decompression

- `run_decompression(applicant_id)`:
  - Reads `Compressed JSON`
  - Updates (or creates) records in child tables to reflect JSON

### Step 5: Shortlisting

- `run_shortlisting(applicant_id)`:
  - Parses JSON
  - Applies multi-factor rules:
    - Experience at Tier-1 or ≥ 4 entries
    - Preferred Rate ≤ 100 AND Availability ≥ 20
    - Location in US, UK, Canada, Germany, or India
  - If passed, inserts into `Shortlisted Leads` with explanation

### Step 6: LLM Enrichment

- `run_llm_enrichment(applicant_id)`:
  - Calls OpenAI GPT to:
    - Summarize the applicant (≤ 75 words)
    - Score (1–10)
    - Flag data issues
    - Suggest follow-ups
  - Saves to `LLM Summary`, `LLM Score`, and `LLM Followup`

---

## API Keys

Store API keys in a `.env` file:

```env
AIRTABLE_API_KEY=your_airtable_token
AIRTABLE_BASE_ID=your_base_id
OPENAI_API_KEY=your_openai_key

## Dependencies

Install required libraries:

```bash
pip install pyairtable openai python-dotenv

Testing
Each functional step can be tested independently:
run_compression("A001")
run_decompression("A001")
run_shortlisting("A001")
run_llm_enrichment("A001")```

Replace "A001" with any valid Applicant ID in your Airtable base.

Project Structure
.
├── compression.py         # Builds compressed JSON from Airtable records
├── decompression.py       # Reconstructs Airtable child records from stored JSON
├── shortlist.py           # Applies shortlisting rules and inserts to Shortlisted Leads
├── llm.py                 # Handles OpenAI API call and prompt parsing
├── enrich.py              # Orchestrates LLM enrichment and Airtable field updates
├── .env                   # Local API keys (excluded from Git)
└── .gitignore             # Prevents sensitive/config files from being pushed

Notes
Airtable record links must be stored as arrays of record IDs (e.g. ["recXXXX"])

Field names in Python must match the Airtable schema exactly

Compressed JSON is structured consistently across compression and decompression steps

OpenAI results must be parsed carefully and validated before saving


Final Words
This project showcases a full-stack automation flow that:

Collects structured applicant data

Serializes and syncs it via JSON

Applies automated business rules

Enhances decisions using LLMs

All logic is modular and suitable for both standalone execution and CI-based workflows.


