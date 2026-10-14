from mcp.server.fastmcp import FastMCP

from secondbrain.agent.service import end_session
from secondbrain.core.exceptions import MCPError
from secondbrain.core.logger import get_logger

logger = get_logger("mcp.tools.session")


def register_session_tools(mcp: FastMCP) -> None:
    @mcp.tool(
        name="end_session",
        description="Signal that a conversation is finished so long-term memory is updated in the background.",
    )
    def end_session_tool(thread_id: str, user_id: str | None = None) -> dict:  # None -> thread id, like ask_secondbrain
        try:
            return end_session(thread_id=thread_id, user_id=user_id)
        except Exception as e:
            logger.exception("end_session tool failed")
            raise MCPError(f"end_session tool failed: {e}") from e

    @mcp.tool(
        name="discover_tools",
        description="Describe a task; returns only the schemas of the SecondBrain tools relevant to it.",
    )
    def discover_tools_tool(task: str) -> list[dict]:
        from secondbrain.lomcp.predictor import get_index, predict_tools

        try:
            info = predict_tools(task)
            index = get_index()
            return [index.entries[name]["schema"] for name in info["names"]]
        except Exception as e:
            logger.exception("discover_tools tool failed")
            raise MCPError(f"discover_tools tool failed: {e}") from e
