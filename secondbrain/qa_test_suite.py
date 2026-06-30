import os
import sys
import uuid
import time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
from secondbrain.core.logger import get_logger

logger = get_logger("qa.test_suite")

from secondbrain.graph.workflow import create_graph
from secondbrain.memory.memory_manager import MemoryManager

print("Initializing QA Test Suite for Phase 5...")
manager = MemoryManager()
graph = create_graph()

def test_category_1_short_term():
    print("\n--- TEST CATEGORY 1: SHORT-TERM MEMORY ---")
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("User: Explain what Docker is in exactly one sentence.")
    res1 = graph.invoke({"messages": [("user", "Explain what Docker is in exactly one sentence.")], "user_id": "test_qa_user"}, config=config)
    print(f"Assistant: {res1['messages'][-1].content}")
    
    time.sleep(6) # Avoid rate limits
    
    print("User: Explain it again, but simpler.")
    res2 = graph.invoke({"messages": [("user", "Explain it again, but simpler.")], "user_id": "test_qa_user"}, config=config)
    print(f"Assistant: {res2['messages'][-1].content}")
    
    if "docker" in res2['messages'][-1].content.lower() or "container" in res2['messages'][-1].content.lower():
        print("[PASS] Pronoun resolution ('it' -> Docker) worked.")
    else:
        print("[FAIL] Pronoun resolution failed.")

def test_category_2_and_3_long_term():
    print("\n--- TEST CATEGORY 2 & 3: LONG-TERM MEMORY EXTRACTION ---")
    user_id = "test_qa_user_" + str(uuid.uuid4())
    
    time.sleep(6)
    print("Simulating Transient Request...")
    graph.invoke({"messages": [("user", "Hello, summarize this PDF for me.")], "user_id": user_id}, config={"configurable": {"thread_id": "t1"}})
    
    time.sleep(6)
    print("Simulating Durable Request...")
    graph.invoke({"messages": [("user", "I am preparing for AI placements. I prefer concise answers and I code in Python.")], "user_id": user_id}, config={"configurable": {"thread_id": "t1"}})
    
    time.sleep(6)
    memories = manager.get_long_term(user_id=user_id, query="What is the user doing?")
    print(f"Extracted Memories: {memories}")
    
    has_durable = False
    for mem in memories.get("results", []):
        text = mem["memory"].lower()
        if "ai placements" in text or "python" in text or "concise" in text:
            has_durable = True
    
    if has_durable:
        print("[PASS] Meaningful durable memory extracted.")
    else:
        print("[FAIL] Did not extract meaningful memory.")

def test_category_5_6_isolation():
    print("\n--- TEST CATEGORY 5 & 6: ISOLATION ---")
    user_a = "user_A_" + str(uuid.uuid4())
    user_b = "user_B_" + str(uuid.uuid4())
    thread_a = str(uuid.uuid4())
    thread_b = str(uuid.uuid4())
    
    time.sleep(6)
    graph.invoke({"messages": [("user", "I love frontend development.")], "user_id": user_a}, config={"configurable": {"thread_id": thread_a}})
    
    time.sleep(6)
    res_b = graph.invoke({"messages": [("user", "What do I love doing?")], "user_id": user_b}, config={"configurable": {"thread_id": thread_b}})
    print(f"User B query response: {res_b['messages'][-1].content}")
    
    if "frontend" not in res_b['messages'][-1].content.lower():
        print("[PASS] User isolation confirmed. User B doesn't know User A's context.")
    else:
        print("[FAIL] Memory leaked between users.")

if __name__ == "__main__":
    try:
        test_category_1_short_term()
        test_category_2_and_3_long_term()
        test_category_5_6_isolation()
    except Exception as e:
        logger.exception(f"Exception during testing: {e}")
