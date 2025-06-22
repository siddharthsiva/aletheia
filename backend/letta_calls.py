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
        result = prod_img(image)
        if result is None:
            return "Could not extract information"
        return json.dumps(result, indent=2)
    
    def pill_explainer(self, identification_json):
        response = client.agents.messages.create(
            agent_id=os.getenv("PILL_IDENTIFIER_ID"),
            messages=[
                {
                    "role": "user",
                    "content": f"Please use the identification json from our image identifier to provide information on the provided medicine: {identification_json}"
                }
            ]
        )
        for message in response.messages:
            if message.message_type == "assistant_message":
                return message.content
    
    def find_cheapest_price(self, identification_json):
        try:
            drug_info = json.loads(identification_json)
            drug_name = drug_info.get("generic_name") or drug_info.get("brand_name")
            if not drug_name:
                return {"error": "Drug name not found in extracted info."}

            prompt = f"""
            Find the cheapest US online pharmacies selling '{drug_name}'.
            Provide a list in JSON format with:
            - pharmacy name
            - estimated price
            - direct link (if available)
            Only return the JSON list. No explanation.
            """

            model = genai.GenerativeModel(model_name="gemini-1.5-pro")
            response = model.generate_content(prompt)
            return json.loads(response.text)

        except Exception as e:
            return {"error": f"Gemini price search failed: {str(e)}"}

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
                return message.content["Response"]

# Export for cleaner imports
__all__ = [
    "agents",
    "DocumentParser",
    "InsuranceRecommender",
    "MedicineExplainer",
    "PillIdentifier",
    "ConversationalInterface"
]
