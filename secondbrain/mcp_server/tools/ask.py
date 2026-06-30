from mcp.server.fastmcp import FastMCP
from secondbrain.core.logger import get_logger
from secondbrain.core.exceptions import MCPError

logger = get_logger("mcp.tools.ask")

from secondbrain.agent.service import answer_query


def register_ask_tool(mcp: FastMCP) -> None:
    """
    Register the primary SecondBrain query tool.
    """

    @mcp.tool(
        name="ask_secondbrain",
        description=(
            "Ask SecondBrain questions using its RAG pipeline, "
            "LangGraph workflow, and long-term memory."
        ),
    )
    def ask_secondbrain(
        query: str,
        thread_id: str | None = None,
    ) -> str:
        import uuid
        logger.info("Tool execution started")
        actual_thread_id = thread_id if thread_id else f"mcp_{uuid.uuid4().hex[:8]}"
        try:
            return answer_query(
                query=query,
                thread_id=actual_thread_id,
            )
        except Exception as e:
            logger.exception(f"ask_secondbrain tool failed: {e}")
            raise MCPError(f"ask_secondbrain tool failed: {e}") from e
        finally:
            logger.info("Tool execution finished")