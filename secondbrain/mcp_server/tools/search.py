from mcp.server.fastmcp import FastMCP
from secondbrain.core.logger import get_logger
from secondbrain.core.exceptions import MCPError

logger = get_logger("mcp.tools.search")

from secondbrain.tools.search import search_documents


def register_search_tool(mcp: FastMCP) -> None:
    """
    Register the document search tool.
    """

    @mcp.tool(
        name="search_documents",
        description="Search the SecondBrain knowledge base."
    )
    def search_documents_tool(
        query: str,
        k: int = 5,
    ):
        logger.info("Tool execution started")
        try:
            return search_documents(
                query=query,
                k=k,
            )
        except Exception as e:
            logger.exception(f"search_documents tool failed: {e}")
            raise MCPError(f"search_documents tool failed: {e}") from e
        finally:
            logger.info("Tool execution finished")