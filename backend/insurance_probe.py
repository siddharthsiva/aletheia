import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Set up API key
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


# Initialize model once
model = genai.GenerativeModel('gemini-2.5-flash')

insurance_query = None
context = None

prompt_template = """
You are an uncompromising insurance-industry intelligence engine.

TASK ▶ For the insurer "{{insurance_query}}", analyse reputation, lawsuits, reviews, and
tailor results to the USER_CONTEXT. Respond **only** with valid JSON matching:

DO NOT DEFAULT TO BLUE SHIELD OF CALIFORNIA, DO NOT DEFAULT TO ANY INSURER, DO NOT DEFAULT TO ANYTHING.

MAKE SURE YOU SEARCH UP THE INSURANCE QUERY AND PROVIDE A DETAILED RESPONSE.

{{
"name": Name of the insurance company
  "trust_index": <float 0-10>,
  "alternatives": [<up to 4 insurer names>],
  "reviews": [<5 public customer reviews>],
  "description": "<brief history + • bullet controversies>",
  "links": [<URLs backing controversies/reputation>]
}}

Rules:
• Bullet lines inside description start with "• ".
• No keys beyond the schema. No markdown, no commentary, no code fences.
USER_CONTEXT: {{context}}

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

  *IMPORTANT* IF CUSTOMRES EXPERIENCE UNEXPLAINED PRICE INCREASES, IF THE COMPANY HAS HAD CONTRAVERSIES RECENTLY SUCH AS UNITED HEALTHCARE OR IF THEY HAVE BEEN SUED RECENTLY, MAKE SURE TO MENTION IT IN REVIEWS
  OR DESCRIPTION. ALL OF THESE SHOULD DRAMATICALLY AFFECT THE TRUST INDEX AND APPROPRIATE FIELDS. THE TRUST INDEX SHOULD BE A NUMBER FROM 0 TO 10, WHERE 0 IS THE WORST AND 10 IS THE BEST.
  THE TRUST INDEX SHOULD BE BASED ON THE COMPANY'S REPUTATION, CUSTOMER REVIEWS, and any recent controversies or lawsuits.
  YOU MUST BE AN EXTREMELY HARSH JUDGE OF THE INSURANCE COMPANY'S REPUTATION, AND YOU MUST NOT GIVE THEM A HIGH TRUST INDEX UNLESS THEY DESERVE IT.
  
""".strip()

def extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, 1, flags=re.I)
    text = text.rsplit("```", 1)[0]
    return text.strip()

def analyze_insurance(insurance_query: str, context: str) -> dict:
    prompt = prompt_template.format(
        insurance_query=insurance_query,
        context=context
    ).strip()

    response = model.generate_content(prompt)
    raw = response.text

    # Strip markdown fences, etc.
    json_blob = extract_json(raw)

    try:
        return json.loads(json_blob)
    except json.JSONDecodeError as e:
        # Throw a clearer error with the blob
        raise ValueError(f"Failed to parse JSON:\n{json_blob}\n\nError: {e}")
