from langchain_core.tools import StructuredTool

from secondbrain.tools.search import search_documents
from secondbrain.tools.documents import list_documents
from secondbrain.tools.summarize import summarize_documents
from secondbrain.tools.questions import generate_questions


def _search_documents_for_agent(query: str, k: int = 5) -> str:
    """
    Agent-facing wrapper around search_documents.

    The raw function returns LangChain Document objects, which ToolNode would
    stringify as Python reprs. The LLM gets readable, citable text instead.
    """
    documents = search_documents(query=query, k=k)
    if not documents:
        return "No relevant documents were found in the knowledge base."
    return "\n\n".join(
        f"[{i}] Source: {doc.metadata.get('document_name') or doc.metadata.get('source', 'Unknown')}"
        f" (page {doc.metadata.get('page_label', 'N/A')})\n{doc.page_content}"
        for i, doc in enumerate(documents, start=1)
    )


search_tool = StructuredTool.from_function(
    func=_search_documents_for_agent,
    name="search_documents",
    description=(
        "Search the indexed knowledge base and return the most "
        "relevant document chunks. "
        "Use this whenever the user asks about information contained "
        "inside their uploaded documents."
    ),
)

list_documents_tool = StructuredTool.from_function(
    func=list_documents,
    name="list_documents",
    description=(
        "Return the names of all indexed documents uploaded by the user."
    ),
)

summarize_tool = StructuredTool.from_function(
    func=summarize_documents,
    name="summarize_documents",
    description=(
        "Generate a concise summary of information retrieved from the "
        "knowledge base."
    ),
)

generate_questions_tool = StructuredTool.from_function(
    func=generate_questions,
    name="generate_questions",
    description=(
        "Generate interview questions based on the indexed knowledge base."
    ),
)

def get_tools():
    return [
        search_tool,
        list_documents_tool,
        summarize_tool,
        generate_questions_tool,
    ]