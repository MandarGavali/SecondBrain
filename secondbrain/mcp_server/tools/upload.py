from mcp.server.fastmcp import FastMCP
from secondbrain.core.logger import get_logger
from secondbrain.core.exceptions import MCPError

logger = get_logger("mcp.tools.upload")

from secondbrain.agent.service import upload_document


def register_upload_tool(mcp: FastMCP) -> None:
    """
    Register the upload document tool.
    """

    @mcp.tool(
        name="upload_document",
        description=(
            "Upload a PDF document into the SecondBrain knowledge base. "
            "The document will be loaded, chunked, embedded, and indexed into Qdrant."
        ),
    )
    def upload_document_tool(path: str) -> dict:
        """
        Upload a document into SecondBrain.

        Args:
            path: Absolute path to the PDF file.

        Returns:
            Dictionary describing the ingestion result.
        """
        logger.info("Tool execution started")
        try:
            return upload_document(path)
        except Exception as e:
            logger.exception(f"upload_document tool failed: {e}")
            raise MCPError(f"upload_document tool failed: {e}") from e
        finally:
            logger.info("Tool execution finished")