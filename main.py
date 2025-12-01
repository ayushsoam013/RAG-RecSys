from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import router
import config.geminiConfig

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic if needed
    yield
    # Shutdown logic if needed

# Create FastAPI app with lifespan
app = FastAPI(
    title="RAG-RecSys API",
    description="Recommendation System with RAG using DSPY and Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to RAG-RecSys API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "gemini": "configured"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
