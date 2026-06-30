from mcp.server.fastmcp import FastMCP

from secondbrain.agent.service import list_memories


def register_resources(mcp: FastMCP):

    @mcp.resource("secondbrain://system")
    def system_resource():

        return {
            "project": "SecondBrain",
            "version": "1.0",
            "framework": "LangGraph",
            "llm": "Gemini 2.5 Flash",
            "vector_store": "Qdrant",
            "memory": "Mem0",
        }


    @mcp.resource("secondbrain://memories")
    def memories_resource():

        return list_memories()


    @mcp.resource("secondbrain://documents")
    def documents_resource():

        return {
            "message": (
                "Knowledge Base Resource.\n"
                "Future version will expose indexed documents."
            )
        }