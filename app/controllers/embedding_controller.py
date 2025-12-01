from config.geminiConfig import gemini_embeddings, gemini_flash
from app.schemas import EmbeddingRequest, EmbeddingResponse

async def generate_embeddings_logic(request: EmbeddingRequest) -> EmbeddingResponse:
    embedding = gemini_embeddings.get_embeddings(request.text)
    
    return EmbeddingResponse(
        text=request.text,
        embedding=embedding,
        model=gemini_embeddings.model_name
    )

async def get_config_info_logic():
    return {
        "model": gemini_flash.lm.model,
        "embedding_model": gemini_embeddings.model_name,
        "status": "configured"
    }
