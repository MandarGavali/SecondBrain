from langgraph.prebuilt import ToolNode

from secondbrain.agent.tools import get_tools

tool_node = ToolNode(get_tools())