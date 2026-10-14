from langchain_core.runnables import Runnable
from secondbrain.rag.llm.gemini_llm import get_llm

from secondbrain.agent.tools import get_tools
from secondbrain.agent.prompts import agent_prompt


def create_agent(tools=None) -> Runnable:
    """Creates the Gemini agent. `tools` = subset to bind (LO-MCP); default = all tools."""
    llm = get_llm()
    tools = tools if tools is not None else get_tools()
    llm_with_tools = llm.bind_tools(tools)
    return agent_prompt | llm_with_tools
