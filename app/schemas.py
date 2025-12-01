from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="The query text to process", min_length=1)
    temperature: float = Field(0.5, description="Temperature for response generation", ge=0.0, le=2.0)

class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    query: str
    response: str
    model: str

class EmbeddingRequest(BaseModel):
    """Request model for embedding endpoint."""
    text: str = Field(..., description="The text to generate embeddings for", min_length=1)

class EmbeddingResponse(BaseModel):
    """Response model for embedding endpoint."""
    text: str
    embedding: List[float]
    model: str

class RecommendationResponse(BaseModel):
    """Response model for recommendation endpoint."""
    product_id: int
    recommendations: List[dict]

class GeneratorRequest(BaseModel):
    """Request model for generator endpoint."""
    product_id: int = Field(..., description="The product ID to get base recommendations for")
    total_recommendations: int = Field(..., description="The total number of recommendations to generate")

class GeneratorResponse(BaseModel):
    """Response model for generator endpoint."""
    product_id: int
    reranked_recommendations: List[dict]
    reasoning: str

