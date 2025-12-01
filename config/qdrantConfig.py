from qdrant_client import QdrantClient

class QdrantClientWrapper:
    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")

    def check_connection(self):
        try:
            # Try to list collections to verify connection
            self.client.get_collections()
            return True
        except Exception:
            return False

qdrant_client_wrapper = QdrantClientWrapper()
