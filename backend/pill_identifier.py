import google.generativeai as genai
import os
import json
import time
import PIL.Image as Image
import dotenv

dotenv.load_dotenv()
# Use your provided Google Gemini API key directly
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

default_system_instructions = """
You are an assistant that extracts detailed information from an image of a drug label. 
Given the image of a drug label, extract the following information and respond ONLY in JSON format with these fields (no extra text):

- brand_name
- generic_name
- ingredients
- manufacturer
- dosage_instructions
- warnings
- expiration_date
- ndc_code
- barcode
- bounding_box
- image_url
- feedback

Respond in this format:
{
  "brand_name": "Tylenol",
  "generic_name": "Acetaminophen",
  "ingredients": ["Acetaminophen 500 mg"],
  "manufacturer": "Johnson & Johnson",
  "dosage_instructions": "Take 1-2 tablets every 4-6 hours.",
  "warnings": "Do not exceed 8 tablets in 24 hours.",
  "expiration_date": "2025-12-31",
  "ndc_code": "12345-6789",
  "barcode": "0123456789012",
  "bounding_box": "120,320,880,940",
  "image_url": null,
  "feedback": "Image quality is good, text is clearly readable."
}
"""

default_safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

default_config = {
    "temperature": 0.25,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain"
}

class DrugLabelExtractor:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.response = None
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings=default_safety_settings,
            system_instruction=default_system_instructions,
            generation_config=default_config
        )

    def process_drug_label_image_streamlit(self, uploaded_file, retries=3) -> dict:
        try:
            image = Image.open(uploaded_file)
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            return {"error": f"Invalid image: {e}"}

        for attempt in range(retries):
            try:
                response = self.model.generate_content(contents=[image])
                self.response = json.loads(response.text[response.text.index("{"):response.text.rindex("}") + 1])
                return self.response
            except Exception as e:
                if "429" in str(e):
                    print(f"⏳ Rate limit hit (attempt {attempt + 1}), retrying...")
                    time.sleep(60)
                else:
                    print(f"❌ Generation failed: {e}")
                    break

        return {"error": "Gemini price search failed: rate limit exceeded or invalid input."}

    def return_response(self):
        if self.response is None:
            raise Exception("No response available. Please process an image first.")
        return self.response

def prod_img(img_file):
    extractor = DrugLabelExtractor()
    extractor.process_drug_label_image_streamlit(img_file)
    return extractor.return_response()
