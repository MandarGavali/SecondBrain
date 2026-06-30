from secondbrain.graph.checkpointer import get_checkpointer

class ShortTermMemory:
    """
    Wrapper for retrieving short-term conversation history directly from 
    the LangGraph MongoDB Checkpointer.
    """
    
    def __init__(self):
        pass

    def get_messages(self, thread_id: str):
        saver = get_checkpointer()
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = saver.get_tuple(config)
        
        if checkpoint_tuple and "messages" in checkpoint_tuple.checkpoint.get("channel_values", {}):
            return checkpoint_tuple.checkpoint["channel_values"]["messages"]
        return []