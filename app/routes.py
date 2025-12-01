from fastapi import APIRouter, HTTPException
from app.schemas import QueryRequest, QueryResponse, EmbeddingRequest, EmbeddingResponse, RecommendationResponse, GeneratorRequest, GeneratorResponse
from app.controllers.rag_controller import process_query_logic, search_products_logic, check_db_status_logic
from app.controllers.embedding_controller import generate_embeddings_logic, get_config_info_logic
from app.controllers.recommendation_controller import get_recommendations_logic, generate_recommendations_logic, get_product_details_logic

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query using the Gemini model via DSPY.
    """
    try:
        return await process_query_logic(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """
    Generate embeddings for the given text using Gemini.
    """
    try:
        return await generate_embeddings_logic(request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating embeddings: {str(e)}"
        )

@router.get("/config")
async def get_config_info():
    """
    Get current Gemini configuration information.
    """
    try:
        return await get_config_info_logic()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting config: {str(e)}"
        )

@router.get("/search")
async def search_products(query: str):
    """
    Search for products using RAG retrieval on product_embeddings collection.
    """
    try:
        return await search_products_logic(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health/db")
async def check_db_status():
    """
    Check the status of the Qdrant database connection.
    """
    try:
        return await check_db_status_logic()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{product_id}", response_model=RecommendationResponse)
async def get_recommendations(product_id: int, total_recommendations: int = 5):
    """
    Get recommendations for a specific product based on its embedding.
    """
    try:
        return await get_recommendations_logic(product_id, total_recommendations)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendations/generate", response_model=GeneratorResponse)
async def generate_recommendations(request: GeneratorRequest):
    """
    Generate re-ranked recommendations based on a system prompt.
    """
    try:
        return await generate_recommendations_logic(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/product/{product_id}")
async def get_product_details(product_id: int):
    """
    Get details for a specific product.
    """
    try:
        return await get_product_details_logic(product_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
