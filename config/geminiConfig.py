import dspy
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

class GeminiFlashWrapper:
    def __init__(self):
        # Using the model name as requested by the user
        self.lm = dspy.LM("gemini/gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"))

class GeminiEmbeddingWrapper:
    def __init__(self):
        self.model_name = "models/embedding-001" 
        self.api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)

    def get_embeddings(self, text):
        result = genai.embed_content(
            model=self.model_name,
            content=text,
            task_type="retrieval_document",
            title="Embedding of single string"
        )
        return result['embedding']

# Initialize wrappers
gemini_flash = GeminiFlashWrapper()
gemini_embeddings = GeminiEmbeddingWrapper()

# Configure dspy
dspy.configure(lm=gemini_flash.lm)