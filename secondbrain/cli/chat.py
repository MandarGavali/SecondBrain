from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path


from secondbrain.agent.service import answer_query

thread_id = input("Thread ID: ")

print("=" * 50)
print("SecondBrain Agentic RAG")
print("Type 'exit' to quit.")
print("=" * 50)

while True:

    query = input("\nYou: ")

    if query.lower() in ["exit", "quit"]:
        break

    response = answer_query(
        query=query,
        thread_id=thread_id,
    )

    print("\nAssistant:\n")
    print(response)