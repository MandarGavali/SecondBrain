import hashlib
import json

from langchain_core.utils.function_calling import convert_to_openai_tool

# Short example utterances make the embedding of each tool more discriminative.
TOOL_EXAMPLES = {
    "search_documents": [
        "what does the document say about X",
        "find the passage about Y",
        "according to my notes",
    ],
    "list_documents": [
        "which documents have I uploaded",
        "show my files",
        "what is in my knowledge base",
    ],
    "summarize_documents": [
        "summarize the document",
        "give me an overview",
        "short summary of chapter 2",
    ],
    "generate_questions": [
        "generate interview questions",
        "create practice questions from my notes",
        "quiz me",
    ],
}


def tool_schema(tool) -> dict:
    """The JSON schema that would be sent to the LLM for this tool."""
    return convert_to_openai_tool(tool)


def schema_tokens(schema: dict) -> int:
    """Cheap token estimate (about 4 characters per token)."""
    return max(1, len(json.dumps(schema, separators=(",", ":"))) // 4)


def spec_hash(name: str, description: str, schema: dict) -> str:
    blob = json.dumps({"n": name, "d": description, "s": schema}, sort_keys=True)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()[:12]


def embedding_text(tool) -> str:
    examples = "; ".join(TOOL_EXAMPLES.get(tool.name, []))
    base = f"{tool.name.replace('_', ' ')}: {tool.description}"
    return f"{base} Examples: {examples}" if examples else base
