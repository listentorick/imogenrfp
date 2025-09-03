from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging
from schemas import RerankRequest, RerankResponse, RerankResult
from model import reranker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model on startup
    logger.info("Loading Qwen4-reranker model...")
    try:
        reranker.load_model()
        logger.info("Qwen4-reranker model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    yield
    # Cleanup if needed

app = FastAPI(
    title="Qwen3 Reranker Service",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": reranker.model_name}

@app.post("/rerank", response_model=RerankResponse)
async def rerank_passages(request: RerankRequest):
    """Rerank passages based on relevance to query using Qwen3-reranker"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if not request.passages:
            raise HTTPException(status_code=400, detail="Passages list cannot be empty")
        
        logger.info(f"Reranking {len(request.passages)} passages for query: {request.query[:100]}...")
        
        # Perform reranking
        ranked_results = reranker.rerank(
            query=request.query,
            passages=request.passages,
            top_k=request.top_k
        )
        
        # Convert to response format
        results = [
            RerankResult(
                text=text,
                score=score,
                index=original_index
            )
            for text, score, original_index in ranked_results
        ]
        
        logger.info(f"Reranking completed. Top score: {results[0].score:.4f}")
        
        return RerankResponse(results=results)
        
    except Exception as e:
        logger.error(f"Error during reranking: {e}")
        raise HTTPException(status_code=500, detail=f"Reranking failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)