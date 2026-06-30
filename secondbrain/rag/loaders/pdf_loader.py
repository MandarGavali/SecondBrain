from secondbrain.utils.logger import logger
import os
import re
from pathlib import Path
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

def load_pdf(pdf_path: str) -> List[Document]:
    """Loads a single PDF, cleans its text, and returns LangChain Documents."""
    loader = PyPDFLoader(file_path=str(pdf_path))
    docs = loader.load()

    # Remove empty pages
    docs = [doc for doc in docs if doc.page_content.strip()]

    for doc in docs:
        text = doc.page_content
        # Remove null characters
        text = text.replace("\x00", "")
        # Normalize whitespace
        text = " ".join(text.split())
        doc.page_content = text

    logger.info(f"Loaded {len(docs)} pages from PDF: {Path(pdf_path).name}")
    return docs

def load_multiple_pdfs(directory: str) -> List[Document]:
    """Loads all PDFs in a directory."""
    all_docs = []
    for filename in os.listdir(directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(directory, filename)
            all_docs.extend(load_pdf(pdf_path))
    return all_docs
