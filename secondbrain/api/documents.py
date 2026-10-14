from fastapi import APIRouter

from secondbrain.core.logger import get_logger

logger = get_logger("api.documents")

router = APIRouter()


@router.get("/documents")
def get_documents():
    """Names of all indexed documents (unique file names from the vector store)."""
    from secondbrain.tools.documents import list_documents

    return {"documents": list_documents()}
