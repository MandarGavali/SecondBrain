from langchain_core.runnables import Runnable
from secondbrain.rag.llm.gemini_llm import get_llm

from secondbrain.agent.tools import get_tools
from secondbrain.agent.prompts import agent_prompt


def create_agent() -> Runnable:
    """
    Creates the Gemini agent with all registered tools.
    """

    llm = get_llm()

    tools = get_tools()

    llm_with_tools = llm.bind_tools(tools)

    agent = agent_prompt | llm_with_tools

    return agent