from dotenv import load_dotenv
load_dotenv()

from mcp.server.fastmcp import FastMCP

from secondbrain.mcp_server.registry import register_everything

mcp = FastMCP(
    name="SecondBrain",
    instructions=(
        "SecondBrain is an AI-powered personal knowledge assistant capable "
        "of answering questions using RAG, long-term memory, and LangGraph."
    ),
)

register_everything(mcp)

if __name__ == "__main__":
    mcp.run()