from langchain_core.tools import StructuredTool

from secondbrain.tools.search import search_documents
from secondbrain.tools.documents import list_documents
from secondbrain.tools.summarize import summarize_documents
from secondbrain.tools.questions import generate_questions


search_tool = StructuredTool.from_function(
    func=search_documents,
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