from pypdf import PdfReader
from letta_client import Letta
import os
import dotenv
from .pill_identifier import prod_img
import json
import dotenv

# Load environment variables
dotenv.load_dotenv()

client = Letta(token=os.getenv("LETTA_API_KEY"))

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
    
    def doc_parser(self, pdf, user_info):
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
            if message.role == "assistant_message":
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
            if message.role == "assistant_message":
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
            print(result)
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
            if message.role == "assistant_message":
                return message.content
    
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
            if message.role == "assistant_message":
                return message.content