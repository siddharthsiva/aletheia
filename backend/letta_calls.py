from pypdf import PdfReader
from letta_client import Letta
import os
import dotenv
import json
import google.generativeai as genai
from .pill_identifier import prod_img
from .general_history import *

# Load environment variables
dotenv.load_dotenv()

# Configure LeTTA and Gemini
client = Letta(token=os.getenv("LETTA_API_KEY"))
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

def agents():
    """Returns a dictionary of agent instances."""
    return {
        "document_parser": DocumentParser.getInstance(),
        "insurance_recommender": InsuranceRecommender.getInstance(),
        "medicine_explainer": MedicineExplainer.getInstance(),
        "pill_identifier": PillIdentifier.getInstance(),
        "conversational_interface": ConversationalInterface.getInstance()
    }

class Agent():
    """Base class for all agents."""
    
    def __init__(self, name: str, id: str):
        self.name = name
        self.id = id
        self.client = client

    def initialize(self):
        """Initializes the agent by retrieving its configuration."""
        if not self.id:
            raise ValueError(f"{self.name} ID environment variable is not set.")
        self.agent = self.client.agents.retrieve(agent_id=self.id)
    
    def extract_response_info(self, response_message):
        json_message = json.loads(response_message)
        return json_message['medical_history'], json_message["doctors note"]

class DocumentParser(Agent):
    _instance = None

    def __init__(self):
        super().__init__(
            name="document parser",
            id=os.getenv("DOCUMENT_PARSER_ID"),
        )
        self.initialize()

    @staticmethod
    def getInstance():
        if DocumentParser._instance is None:
            DocumentParser._instance = DocumentParser()
        return DocumentParser._instance
    
    def extract_text_with_pypdf(self, pdf):
        reader = PdfReader(pdf)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    
    def doc_parser(self, pdf, user_info=""):
        pdf_text = self.extract_text_with_pypdf(pdf)
        response = client.agents.messages.create(
            agent_id=os.getenv("DOCUMENT_PARSER_ID"),
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze the following PDF content: {pdf_text} for the user, who's info is as follows: {user_info}"
                }
            ]
        )
        for message in response.messages:
            if message.message_type == "assistant_message":
                return message.content

class InsuranceRecommender(Agent):
    _instance = None

    def __init__(self):
        super().__init__(
            name="insurance recommender",
            id=os.getenv("INSURANCE_RECOMMENDER_ID"),
        )
        self.initialize()

    @staticmethod
    def getInstance():
        if InsuranceRecommender._instance is None:
            InsuranceRecommender._instance = InsuranceRecommender()
        return InsuranceRecommender._instance

class MedicineExplainer(Agent):
    _instance = None

    def __init__(self):
        super().__init__(
            name="medicine explainer",
            id=os.getenv("MEDICINE_EXPLAINER_ID"),
        )
        self.initialize()

    @staticmethod
    def getInstance():
        if MedicineExplainer._instance is None:
            MedicineExplainer._instance = MedicineExplainer()
        return MedicineExplainer._instance
    
    def medicine_explainer(self, medicine_name):
        response = client.agents.messages.create(
            agent_id=os.getenv("MEDICINE_EXPLAINER_ID"),
            messages=[
                {
                    "role": "user",
                    "content": f"Please explain {medicine_name} using research"
                }
            ]
        )
        for message in response.messages:
            if message.message_type == "assistant_message":
                return message.content

class PillIdentifier(Agent):
    _instance = None

    def __init__(self):
        super().__init__(
            name="pill identifier",
            id=os.getenv("PILL_IDENTIFIER_ID"),
        )
        self.initialize()

    @staticmethod
    def getInstance():
        if PillIdentifier._instance is None:
            PillIdentifier._instance = PillIdentifier()
        return PillIdentifier._instance
    
    def pill_identifier(self, image):
        try:
            print(f"DEBUG: Calling prod_img with image type: {type(image)}")
            result = prod_img(image)
            print(f"DEBUG: prod_img returned: {result} (type: {type(result)})")
            
            if result is None:
                return "Could not extract information from the image"
            
            # Handle different return types from prod_img
            if isinstance(result, str):
                # If it's already a string, check if it's valid JSON
                try:
                    json.loads(result)  # Test if it's valid JSON
                    return result
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat it as a simple string response
                    return result
            elif isinstance(result, dict):
                # If it's a dictionary, convert to JSON
                return json.dumps(result, indent=2)
            else:
                # For any other type, convert to string
                return str(result)
                
        except Exception as e:
            error_msg = f"Error in pill identification: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return error_msg
    
    def pill_explainer(self, medication_name):
        try:
            print(f"DEBUG: Explaining medication: {medication_name}")
            response = client.agents.messages.create(
                agent_id=os.getenv("PILL_IDENTIFIER_ID"),
                messages=[
                    {
                        "role": "user",
                        "content": f"Please provide information on the provided medicine: {medication_name}"
                    }
                ]
            )
            for message in response.messages:
                if message.message_type == "assistant_message":
                    return message.content
        except Exception as e:
            error_msg = f"Error explaining medication: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return error_msg

    def find_cheapest_price(self, medication_name):
        try:
            print(f"DEBUG: Finding price for: {medication_name}")
            
            # Handle different input types
            drug_name = None
            if isinstance(medication_name, str):
                try:
                    # Try to parse as JSON first
                    drug_info = json.loads(medication_name)
                    drug_name = drug_info.get("generic_name") or drug_info.get("brand_name")
                except json.JSONDecodeError:
                    # If not JSON, use the string directly as drug name
                    drug_name = medication_name.strip()
            elif isinstance(medication_name, dict):
                drug_name = medication_name.get("generic_name") or medication_name.get("brand_name")
            else:
                drug_name = str(medication_name)
                
            if not drug_name:
                return {"error": "Drug name not found in extracted info."}

            prompt = f"""
            Find and return the link for the cheapest price of the drug named '{drug_name}'.
            Make sure it is from a reputable source.
            Return the link in a JSON with the following fields. Include no other text in your response:
            {{
                "drug_name": "{drug_name}",
                "price": "<price>",
                "link": "<link>"
            }}
            """

            model = genai.GenerativeModel(model_name="gemini-2.5-flash")
            response = model.generate_content(prompt)
            
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            return json.loads(response_text.strip())

        except Exception as e:
            error_msg = f"Gemini price search failed: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return {"error": error_msg}

class ConversationalInterface(Agent):
    _instance = None

    def __init__(self):
        super().__init__(
            name="conversational interface",
            id=os.getenv("CONVERSATIONAL_INTERFACE_ID"),
        )
        self.initialize()

    @staticmethod
    def getInstance():
        if ConversationalInterface._instance is None:
            ConversationalInterface._instance = ConversationalInterface()
        return ConversationalInterface._instance
    
    def conversation(self, query):
        try:
            print(f"DEBUG: Conversational query: {query}")
            response = client.agents.messages.create(
                agent_id=os.getenv("CONVERSATIONAL_INTERFACE_ID"),
                messages=[
                    {
                        "role": "user",
                        "content": f"{query}"
                    }
                ]
            )
            for message in response.messages:
                if message.message_type == "assistant_message":
                    # Handle different response formats
                    content = message.content
                    if isinstance(content, dict):
                        return content.get("Response", content.get("response", str(content)))
                    return content
        except Exception as e:
            error_msg = f"Conversation error: {str(e)}"
            print(f"DEBUG: {error_msg}")
            return error_msg

# Export for cleaner imports
__all__ = [
    "agents",
    "DocumentParser",
    "InsuranceRecommender",
    "MedicineExplainer",
    "PillIdentifier",
    "ConversationalInterface"
]