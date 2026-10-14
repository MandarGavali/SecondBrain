from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from secondbrain.core.logger import get_logger

logger = get_logger("rag.loaders.pdf")


def load_pdf(pdf_path: str) -> List[Document]:
    """Loads a single PDF, cleans its text, and returns LangChain Documents."""
    docs = [d for d in PyPDFLoader(file_path=str(pdf_path)).load() if d.page_content.strip()]
    for doc in docs:
        # Remove null characters and normalize whitespace
        doc.page_content = " ".join(doc.page_content.replace("\x00", "").split())
    logger.info(f"Loaded {len(docs)} pages from PDF: {Path(pdf_path).name}")
    return docs
