"""
Gemini JSON-only insurance-intel probe with automatic fence-stripping.
"""

import os, json, re, google.generativeai as genai

# ── CONFIG ────────────────────────────────────────────────────────────────
genai.configure(api_key="") # REMEMBER TO REMOVE THIS KEY BEFORE COMMITTING!
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

use this as an example template for the JSON response (keep the KEYS THE EXACT SMAE):

  "trust_index": 8,
  "coverage_quality": "int from 0 to 100",
  "affordability": "int from 0 to 100",
  "customer_service": "int from 0 to 100",
  "alternatives": [
    
      "name": "Ambetter",
      "trust_index": 7
    
    
      "name": "USAA",
      "trust_index": 9
    
    
      "name": "MetLife",
      "trust_index": 7
    
    
      "name": "GEICO",
      "trust_index": 7
    
    
      "name": "Farmers Insurance",
      "trust_index": 8
    
  ],
  "reviews": [
    "Finding comprehensive health coverage with pre-existing conditions was daunting, but a marketplace plan offered manageable out-of-pocket costs, which was a huge relief.",
    "The mobile app and 24/7 support are game-changers for my busy freelance schedule. I can manage policies and get quick answers anytime, anywhere.",
    "After a previous denial, transparency was my top priority. This provider has been upfront about all costs and policy terms, which builds a lot of trust.",
    "While their health insurance is excellent, I had to secure my renters policy separately. It would be convenient to bundle, but the quality of each coverage makes it worthwhile.",
    "Customer service can sometimes have long wait times, but when I connect with a representative, they are usually very knowledgeable and helpful, especially with complex medical inquiries."
  ],
  "description": [
    "**History of Insurance Industry:**",
    "- The modern insurance industry evolved from ancient risk-sharing practices, with formal companies emerging in the 17th century.",
    "- Health insurance gained prominence in the U.S. post-WWII, often tied to employment, while individual markets were more fragmented.",
    "- The Affordable Care Act (ACA) of 2010 significantly reformed the individual health insurance market, introducing marketplaces and protections for pre-existing conditions.",
    "- Renters insurance, a form of property insurance, protects personal belongings and provides liability coverage for tenants.",
    "**Common Controversies & Concerns:**",
    "- **Coverage Denials:** A frequent source of frustration for policyholders, especially concerning specific treatments, pre-existing conditions (though less common post-ACA), or complex claims.",
    "- **Premium Increases:** Regular adjustments to premiums can strain budgets, often attributed to rising healthcare costs or claims experience.",
    "- **Transparency Issues:** Lack of clear billing, complex policy language, and opaque claims processes can lead to distrust and confusion.",
    "- **Customer Service Quality:** Inconsistent service, long wait times, or difficulty resolving issues are common complaints across the industry.",
    "- **Out-of-Pocket Costs:** High deductibles, co-pays, and co-insurance can make healthcare expensive even with insurance, a key concern for those seeking 'low out-of-pocket' plans."
  ],
  "links": [
    "https://www.healthcare.gov/glossary/affordable-care-act/",
    "https://www.naic.org/index_consumer.htm",
    "https://www.jdpower.com/business/insurance",
    "https://www.consumerreports.org/insurance/",
    "https://www.bbb.org/us/us/find-a-business/insurance"
  ]
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
