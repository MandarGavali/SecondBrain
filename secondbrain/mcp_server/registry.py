from mcp.server.fastmcp import FastMCP
from secondbrain.mcp_server.tools.ask import register_ask_tool
from secondbrain.mcp_server.tools.search import register_search_tool
from secondbrain.mcp_server.tools.upload import register_upload_tool
from secondbrain.mcp_server.tools.memory import register_memory_tools
from secondbrain.mcp_server.resources import register_resources
from secondbrain.mcp_server.prompts import register_prompts


def register_everything(mcp: FastMCP) -> None:
    """
    Register every MCP capability.
    """

    register_ask_tool(mcp)
    register_search_tool(mcp)
    register_upload_tool(mcp)
    register_memory_tools(mcp)
    register_resources(mcp)
    register_prompts(mcp)

    # Future registrations
    # register_search_tool(mcp)
    # register_upload_tool(mcp)
    # register_memory_tools(mcp)
    # register_resources(mcp)
    # register_prompts(mcp)