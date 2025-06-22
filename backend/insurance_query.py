
# Dependencies (install with):
# pip install google-generative-ai textblob pandas

import json
import os
import re
from google import generativeai as genai
from textblob import TextBlob
import pandas as pd

# 1. Configure your Gemini API key
genai.configure(api_key="")

# 2. User inputs
insurance_query = "Acme Mutual Insurance"
context = (
    "User is a 45-year-old freelance graphic designer based in San Diego with a history "
    "of Type 2 diabetes and mild asthma. He has an annual income of around $60,000, "
    "owns a two-bedroom condo, and is looking for comprehensive health and renters "
    "insurance with low out-of-pocket costs. Prefers customer service available via "
    "mobile app and 24/7 support. Concerned about past coverage denials and wants "
    "transparent billing."
)

# 3. Load insurance reviews from local CSV file
df_path = os.path.join(os.path.dirname(__file__), 'Final Data.csv')
df = pd.read_csv(df_path)
print(f"Loaded {len(df)} records from {df_path}.")

# Normalize column names to lowercase
orig_columns = df.columns.tolist()
df.columns = df.columns.str.lower()
print(f"Columns detected: {orig_columns}")

# Identify review column (fallback to 'review text', else first text-like column)
review_col = next((c for c in df.columns if 'review' in c), None)
if review_col is None:
    # fallback to first non-numeric column
    review_col = df.select_dtypes(include=['object']).columns[0]
print(f"Using review column: {review_col}")

# 4. Prompt_1: ask Gemini for 50 alternative providers based on context
alt_prompt = f"""
Given the user context:
{context}

List 50 insurance providers (only names) that would be better alternatives to '{insurance_query}' for this user. Return strictly JSON with a single field 'alternatives' containing an array of names.
"""
model = genai.GenerativeModel('gemini-2.5-flash')
resp1 = model.generate_content(
    contents=[{"role": "user", "parts": [{"text": alt_prompt}]}],
    generation_config=genai.types.GenerationConfig(
        temperature=0.2,
        max_output_tokens=4096,
        response_mime_type="application/json"
    )
)

# 5. Parse alternatives list
raw_alt = ""
if resp1.candidates:
    cand = resp1.candidates[0]
    if hasattr(cand.content, 'parts') and cand.content.parts:
        raw_alt = ''.join(p.text for p in cand.content.parts)

if not raw_alt:
    raise ValueError(f"No JSON content for alternatives (finish_reason={resp1.candidates[0].finish_reason}).")

alts_json = json.loads(raw_alt)
candidates = alts_json.get('alternatives', [])
print(f"Received {len(candidates)} candidate providers.")

# 6. Sentiment analysis to narrow to top 5
scores = {}
for prov in candidates:
    # find rows where provider name appears in review text (case-insensitive word boundary match)
    pattern = re.compile(rf"\b{re.escape(prov)}\b", re.IGNORECASE)
    mask = df[review_col].astype(str).apply(lambda x: bool(pattern.search(x)))
    subset = df[mask][review_col].dropna().astype(str)
    if subset.empty:
        continue
    sentiments = [TextBlob(txt).sentiment.polarity for txt in subset]
    scores[prov] = sum(sentiments) / len(sentiments)

if not scores:
    print("No sentiment matches found; skipping sentiment ranking.")
    top5 = candidates[:5]
else:
    top5 = sorted(scores, key=scores.get, reverse=True)[:5]
print(f"Top 5 providers by sentiment: {top5}")

# 7. Prompt_2: detailed analysis for top 5
detail_prompt = f"""
Given the insurance company '{insurance_query}' and user context:
{context}

Focus on these 5 alternative providers:
{top5}

Return strictly JSON with these fields:
1. trust_index: (0-10)
2. alternatives: list of objects {{name, trust_index}}
3. reviews: array of 5 most relevant reviews
4. description: bullet-point history and controversies
5. links: URLs to articles or resources
"""
resp2 = model.generate_content(
    contents=[{"role": "user", "parts": [{"text": detail_prompt}]}],
    generation_config=genai.types.GenerationConfig(
        temperature=0.2,
        max_output_tokens=4096,
        response_mime_type="application/json"
    )
)

# 8. Save final JSON to file
raw_detail = ""
if resp2.candidates:
    cand2 = resp2.candidates[0]
    if hasattr(cand2.content, 'parts') and cand2.content.parts:
        raw_detail = ''.join(p.text for p in cand2.content.parts)

if not raw_detail:
    raise ValueError(f"No JSON content for detailed analysis (finish_reason={resp2.candidates[0].finish_reason}).")

final_json = json.loads(raw_detail)
out_file = os.path.join(os.path.dirname(__file__), 'insurance_analysis_output.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(final_json, f, ensure_ascii=False, indent=2)

print(f"Detailed analysis saved to {out_file}")

