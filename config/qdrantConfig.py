from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()

class QdrantClientWrapper:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"), 
            api_key=os.getenv("QDRANT_API_KEY"),
        )

    def check_connection(self):
        try:
            # Try to list collections to verify connection
            self.client.get_collections()
            return True
        except Exception:
            return False

qdrant_client_wrapper = QdrantClientWrapper()
