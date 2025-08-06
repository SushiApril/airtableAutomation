from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

PROMPT_TEMPLATE = """You are a recruiting analyst. Given this JSON applicant profile, do four things:
1. Provide a concise 75-word summary.
2. Rate overall candidate quality from 1 to 10 (higher is better).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps.

Return exactly:
Summary: <text>
Score: <integer>
Issues: <comma-separated list or 'None'>
Follow-Ups:
• <question 1>
• <question 2>
"""

def call_llm(applicant_json):
    prompt = PROMPT_TEMPLATE + "\n\n" + str(applicant_json)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )

    content = response.choices[0].message.content

    return parse_llm_response(content)

def parse_llm_response(text):
    def extract_line(prefix):
        for line in text.splitlines():
            if line.startswith(prefix):
                return line.replace(prefix, "").strip()
        return ""

    def extract_bullets():
        return "\n".join(line for line in text.splitlines() if line.strip().startswith("•"))

    return {
        "summary": extract_line("Summary:"),
        "score": extract_line("Score:"),
        "issues": extract_line("Issues:"),
        "followups": extract_bullets()
    }
