import dspy
from config.geminiConfig import gemini_flash, gemini_embeddings
from config.qdrantConfig import qdrant_client_wrapper
from app.schemas import QueryRequest, QueryResponse

# Simple DSPY Signature
class GenerateAnswer(dspy.Signature):
    """Generate an answer to a given question."""
    question = dspy.InputField(desc="The question to answer")
    answer = dspy.OutputField(desc="The answer to the question")

async def process_query_logic(request: QueryRequest) -> QueryResponse:
    # Create DSPY module for generation
    generator = dspy.ChainOfThought(GenerateAnswer)
    
    # Generate response
    # Note: Temperature is currently using the global default from config
    result = generator(question=request.query)
    
    return QueryResponse(
        query=request.query,
        response=result.answer,
        model=gemini_flash.lm.model
    )

async def search_products_logic(query: str):
    # Generate embedding for the query
    query_vector = gemini_embeddings.get_embeddings(query)
    
    # Search in Qdrant
    search_result = qdrant_client_wrapper.client.search(
        collection_name="product_embeddings",
        query_vector=query_vector,
        limit=5
    )
    
    return {"results": search_result}

async def check_db_status_logic():
    is_connected = qdrant_client_wrapper.check_connection()
    return {
        "status": "connected" if is_connected else "disconnected",
        "database": "qdrant"
    }
