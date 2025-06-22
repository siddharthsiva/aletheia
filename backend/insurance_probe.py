import os
import json
import re
import google.generativeai as genai

# Set up API key
genai.configure(api_key="AIzaSyA1DHBN0xCgcpfX6ftlk5gVQdEBhcKvQsQ")

# Initialize model once
model = genai.GenerativeModel('gemini-pro')

def extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, 1, flags=re.I)
    text = text.rsplit("```", 1)[0]
    return text.strip()

def analyze_insurance(insurance_query: str, context: str) -> dict:
    prompt = f"""
You are an uncompromising insurance-industry intelligence engine.

TASK ▶ For the insurer "{insurance_query}", analyse reputation, lawsuits, reviews, and
tailor results to the USER_CONTEXT. Respond **only** with valid JSON matching:

{{
"name": Name of the insurance company,
"trust_index": <float 0-10>,
"alternatives": [
  {{"name": "Ambetter", "trust_index": 7}},
  {{"name": "USAA", "trust_index": 9}},
  {{"name": "MetLife", "trust_index": 7}},
  {{"name": "GEICO", "trust_index": 7}}
],
"reviews": ["...", "...", "...", "...", "..."],
"description": "brief history + • bullet controversies",
"links": ["<valid reputable links>"]
}}

Rules:
• Description bullets start with "• ".
• No markdown/code fences/extra keys.

USER_CONTEXT: {context}
""".strip()

    response = model.generate_content(prompt)
    json_str = extract_json(response.text)
    return json.loads(json_str)
