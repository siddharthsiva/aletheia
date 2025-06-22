"""
Gemini JSON-only insurance-intel probe with automatic fence-stripping.
"""

import os, json, re, google.generativeai as genai

# ── CONFIG ────────────────────────────────────────────────────────────────
genai.configure(api_key="AIzaSyA1DHBN0xCgcpfX6ftlk5gVQdEBhcKvQsQ")
model = genai.GenerativeModel("gemini-2.5-flash")

# ── INPUTS ────────────────────────────────────────────────────────────────
insurance_query = "Blue Shield of California"

context = (
    "User is a 32-year-old freelance graphic designer living in Los Angeles, earning "
    "≈ $85 k/year pre-tax with irregular cash-flow, mild asthma, type-2 diabetes family "
    "history, newly married and planning children in ≤ 3 yrs. Needs PPO that covers "
    "Cedars-Sinai + UCLA, strong maternity, fears high deductibles after a $4 k ER bill, "
    "values ESG & companies with clean denial records, wants first-class mobile app, "
    "travels abroad ~6×/yr."
)

prompt = f"""
You are an uncompromising insurance-industry intelligence engine.

TASK ▶ For the insurer "{insurance_query}", analyse reputation, lawsuits, reviews, and
tailor results to the USER_CONTEXT. Respond **only** with valid JSON matching:

{{
  "trust_index": <float 0-10>,
  "alternatives": [<up to 4 insurer names>],
  "reviews": [<5 public customer reviews>],
  "description": "<brief history + • bullet controversies>",
  "links": [<URLs backing controversies/reputation>]
}}

Rules:
• Bullet lines inside description start with "• ".
• No keys beyond the schema. No markdown, no commentary, no code fences.
USER_CONTEXT: {context}

For the links, make sure the URLs are valid and point to reputable sources. 
Notable sources include:
- Government websites (e.g., .gov)
- Reputable news outlets (e.g., BBC, NYT, WSJ)
- Well-known financial or insurance review sites (e.g., Consumer Reports, J.D. Power)
- Academic or industry research papers (e.g., .edu, .org)
Avoid personal blogs, forums, or unverified sources.
Respond with **only** the JSON, no other text.

Double check the links that they work before adding them to the response.
""".strip()

# ── CALL GEMINI ───────────────────────────────────────────────────────────
response = model.generate_content(prompt)
res = response.text               # raw model output (likely fenced)

# ── CLEAN-UP ──────────────────────────────────────────────────────────────
def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, 1, flags=re.I)
        text = text.rsplit("```", 1)[0]
    return text.strip()

clean = extract_json(res)
data  = json.loads(clean)         # ready to use ✅

output_path = "insurance_intel.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"JSON written to {output_path}")
