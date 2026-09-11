from fastapi import APIRouter
from elephantine.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "engine": "MemAgent CPU Native",
        "embedding_model": settings.EMBEDDING_MODEL_NAME,
        "embedding_dim": settings.EMBEDDING_DIM,
        "threads": {
            "intra_op": settings.ONNX_INTRA_OP_NUM_THREADS,
            "inter_op": settings.ONNX_INTER_OP_NUM_THREADS
        }
    }
