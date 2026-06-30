from secondbrain.core.logger import get_logger
logger = get_logger("graph.export_graph")
import os
from secondbrain.graph.workflow import compile_graph_with_checkpointer

def export_graph_visualization():
    """
    Exports the LangGraph architecture to an image.
    Tries to generate a PNG using Mermaid. If it fails (due to missing system dependencies),
    it falls back to generating a raw Mermaid syntax (.mmd) file.
    """
    logger.info("Compiling graph...")
    graph = compile_graph_with_checkpointer()
    
    png_path = "graph.png"
    mmd_path = "graph.mmd"

    try:
        logger.info("Attempting to generate PNG via Mermaid...")
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open(png_path, "wb") as f:
            f.write(png_bytes)
        logger.info(f"Successfully generated {png_path}!")
    except Exception as e:
        logger.exception(f"Failed to generate PNG: {e}")
        logger.info("Falling back to raw Mermaid syntax generation...")
        
        try:
            mmd_syntax = graph.get_graph().draw_mermaid()
            with open(mmd_path, "w", encoding="utf-8") as f:
                f.write(mmd_syntax)
            logger.info(f"Successfully generated {mmd_path}! You can view this syntax on https://mermaid.live")
        except Exception as fallback_err:
            logger.exception(f"Fallback generation also failed: {fallback_err}")

if __name__ == "__main__":
    export_graph_visualization()
