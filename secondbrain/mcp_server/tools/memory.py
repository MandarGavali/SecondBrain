from mcp.server.fastmcp import FastMCP
from secondbrain.core.logger import get_logger
from secondbrain.core.exceptions import MCPError

logger = get_logger("mcp.tools.memory")

from secondbrain.agent.service import (
    remember,
    forget,
    list_memories,
)


def register_memory_tools(mcp: FastMCP):

    @mcp.tool(
        name="remember",
        description="Store information into SecondBrain long-term memory.",
    )
    def remember_tool(
        text: str,
        user_id: str = "default",
    ):
        logger.info("Tool execution started")
        try:
            return remember(
                text=text,
                user_id=user_id,
            )
        except Exception as e:
            logger.exception(f"remember tool failed: {e}")
            raise MCPError(f"remember tool failed: {e}") from e
        finally:
            logger.info("Tool execution finished")


    @mcp.tool(
        name="forget",
        description="Delete a memory from SecondBrain.",
    )
    def forget_tool(
        memory_id: str,
    ):
        logger.info("Tool execution started")
        try:
            return forget(
                memory_id=memory_id,
            )
        except Exception as e:
            logger.exception(f"forget tool failed: {e}")
            raise MCPError(f"forget tool failed: {e}") from e
        finally:
            logger.info("Tool execution finished")


    @mcp.tool(
        name="list_memories",
        description="List all stored long-term memories.",
    )
    def list_memories_tool(
        user_id: str = "default",
    ):
        logger.info("Tool execution started")
        try:
            return list_memories(
                user_id=user_id,
            )
        except Exception as e:
            logger.exception(f"list_memories tool failed: {e}")
            raise MCPError(f"list_memories tool failed: {e}") from e
        finally:
            logger.info("Tool execution finished")